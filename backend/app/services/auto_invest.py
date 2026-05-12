"""定投 / 自动转入执行引擎"""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.plan import InvestmentPlan
from app.models.fund import Fund
from app.models.account import SavingsAccount
from app.models.holding import FundHolding
from app.models.transaction import TransactionRecord
from app.services.trading_calendar import TradingCalendarService
from app.services.settlement import SettlementService, FUND_SETTLE_CYCLE_MAP, DEFAULT_CYCLE

logger = logging.getLogger(__name__)


class AutoInvestService:
    """自动定投执行"""

    def __init__(self, db: Session):
        self.db = db
        self.calendar = TradingCalendarService(db)
        self.settlement = SettlementService(db)

    # ----------------------------------------------------------------
    # 每日执行
    # ----------------------------------------------------------------

    def execute_due_plans(self, today: date, user_id: int | None = None) -> int:
        """
        执行所有到期定投计划
        返回实际执行的笔数
        """
        today_str = today.isoformat()
        executed = 0

        q = (
            self.db.query(InvestmentPlan)
            .filter(
                InvestmentPlan.next_execute_date <= today_str,
                InvestmentPlan.status == "active",
            )
        )
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        due_plans = q.all()

        for plan in due_plans:
            if self._execute_one(plan, today):
                executed += 1

        self.db.commit()
        if executed:
            logger.info(f"定投执行完成: {executed}笔")
        return executed

    # ----------------------------------------------------------------
    # 单笔执行
    # ----------------------------------------------------------------

    def _execute_one(self, plan: InvestmentPlan, today: date) -> bool:
        """执行单个定投计划，返回是否执行成功"""
        execute_date = today

        user_id = plan.user_id

        # 1. 是否交易日
        if not self.calendar.is_trading_day(execute_date):
            execute_date = self.calendar.get_next_trading_day(execute_date)
            plan.next_execute_date = execute_date.isoformat()
            return False

        # 2. 检查账户余额
        account = (
            self.db.query(SavingsAccount)
            .filter_by(id=plan.from_account_id, user_id=user_id)
            .first()
        )
        if not account or not account.is_active:
            logger.warning(f"定投计划 {plan.plan_name}: 账户不可用")
            self._schedule_next(plan, execute_date)
            return False

        if account.balance < plan.amount:
            logger.warning(
                f"定投计划 {plan.plan_name}: 余额不足 "
                f"({account.balance:.2f} < {plan.amount:.2f})"
            )
            self._schedule_next(plan, execute_date)
            return False

        # 3. 获取基金信息
        fund = (
            self.db.query(Fund)
            .filter_by(code=plan.fund_code, user_id=user_id)
            .first()
        )
        if not fund or not fund.nav:
            logger.warning(f"定投计划 {plan.plan_name}: 净值不可用")
            # 顺延至下一交易日
            plan.next_execute_date = self.calendar.get_next_trading_day(
                execute_date
            ).isoformat()
            return False

        # 4. 扣款
        account.balance -= plan.amount

        # 5. 计算费用 & 份额
        fee = self._calc_fee(plan.amount, fund.fund_type)
        actual_amount = plan.amount - fee
        shares = actual_amount / fund.nav

        # 6. 确认日期
        confirm_date = self.settlement.compute_confirm_date(
            execute_date, fund.fund_type
        )

        # 7. 创建交易记录
        txn = TransactionRecord(
            user_id=user_id,
            trans_type="auto_buy",
            fund_code=plan.fund_code,
            fund_name=fund.name,
            amount=plan.amount,
            nav=fund.nav,
            shares=round(shares, 4),
            fee=fee,
            actual_amount=actual_amount,
            order_date=execute_date.isoformat(),
            confirm_date=confirm_date.isoformat(),
            source_account_id=plan.from_account_id,
            plan_id=plan.id,
            status="pending",
            confirm_shares=round(shares, 4),
        )
        self.db.add(txn)
        self.db.flush()

        # 8. 冻结持仓份额
        holding = self._get_or_create_holding(
            plan.fund_code, plan.from_account_id, user_id
        )
        holding.frozen_shares += round(shares, 4)

        # 9. 更新计划状态
        plan.last_execute_date = execute_date.isoformat()
        plan.completed_rounds += 1
        if plan.total_rounds and plan.completed_rounds >= plan.total_rounds:
            plan.status = "stopped"
            plan.next_execute_date = None
        else:
            self._schedule_next(plan, execute_date)

        logger.info(
            f"定投执行: {plan.plan_name} → {fund.name} "
            f"金额={plan.amount:.2f} 份额={shares:.4f} "
            f"确认日期={confirm_date}"
        )
        return True

    # ----------------------------------------------------------------
    # 工具方法
    # ----------------------------------------------------------------

    def _schedule_next(self, plan: InvestmentPlan, current_date: date):
        """计算下次执行日期"""
        if plan.frequency == "monthly":
            day = plan.execute_day or 1
            month = current_date.month + 1
            year = current_date.year
            if month > 12:
                month = 1
                year += 1
            # 2 月兼容
            try:
                next_date = date(year, month, min(day, 28))
            except ValueError:
                next_date = date(year, month, 28)
            plan.next_execute_date = next_date.isoformat()
        elif plan.frequency == "weekly":
            plan.next_execute_date = (current_date + timedelta(days=7)).isoformat()
        elif plan.frequency == "biweekly":
            plan.next_execute_date = (current_date + timedelta(days=14)).isoformat()
        elif plan.frequency == "daily":
            plan.next_execute_date = (current_date + timedelta(days=1)).isoformat()

    @staticmethod
    def _calc_fee(amount: float, fund_type: str | None) -> float:
        """简化的申购费计算"""
        # 常见费率：股票/混合型 0.15%，债券型 0.08%，货币型 0%
        fee_rates = {
            "stock": 0.0015,
            "mixed": 0.0015,
            "index": 0.0012,
            "bond": 0.0008,
            "money": 0,
            "qdii": 0.0015,
        }
        rate = fee_rates.get(fund_type, 0.0015)
        # 打折（互联网平台通常1折）
        rate *= 0.1
        return round(amount * rate, 2)

    def _get_or_create_holding(self, fund_code: str,
                                source_account_id: int | None,
                                user_id: int | None = None) -> FundHolding:
        holding = (
            self.db.query(FundHolding)
            .filter_by(fund_code=fund_code, source_account_id=source_account_id, user_id=user_id)
            .first()
        )
        if not holding:
            fund = (
                self.db.query(Fund)
                .filter_by(code=fund_code, user_id=user_id)
                .first()
            )
            holding = FundHolding(
                user_id=user_id or 1,
                fund_code=fund_code,
                fund_name=fund.name if fund else fund_code,
                source_account_id=source_account_id,
            )
            self.db.add(holding)
            self.db.flush()
        return holding
