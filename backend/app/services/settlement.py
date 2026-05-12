"""T+N 份额确认 & 资金到账服务"""
import logging
from datetime import date
from sqlalchemy.orm import Session
from app.models.fund import Fund
from app.models.holding import FundHolding
from app.models.transaction import TransactionRecord
from app.models.account import SavingsAccount
from app.services.trading_calendar import TradingCalendarService

logger = logging.getLogger(__name__)

# 基金类型 → (份额确认周期, 赎回到账周期)
FUND_SETTLE_CYCLE_MAP = {
    "money":   ("T+1", "T+1"),
    "bond":    ("T+1", "T+2"),
    "stock":   ("T+1", "T+3"),
    "mixed":   ("T+1", "T+3"),
    "index":   ("T+1", "T+3"),
    "qdii":    ("T+2", "T+7"),
    "etf":     ("T+1", "T+2"),
    "fof":     ("T+2", "T+4"),
}
DEFAULT_CYCLE = ("T+1", "T+3")


class SettlementService:
    """份额确认 & 资金到账"""

    def __init__(self, db: Session):
        self.db = db
        self.calendar = TradingCalendarService(db)

    # ----------------------------------------------------------------
    # 日期计算
    # ----------------------------------------------------------------

    @staticmethod
    def _parse_cycle(cycle_str: str) -> int:
        return int(cycle_str.split("+")[1])

    def compute_confirm_date(self, order_date: date, fund_type: str | None) -> date:
        """计算份额确认日期"""
        cycle = FUND_SETTLE_CYCLE_MAP.get(fund_type, DEFAULT_CYCLE)
        days = self._parse_cycle(cycle[0])
        return self.calendar.get_next_trading_day(order_date, offset=days)

    def compute_redeem_date(self, order_date: date, fund_type: str | None) -> date:
        """计算赎回到账日期"""
        cycle = FUND_SETTLE_CYCLE_MAP.get(fund_type, DEFAULT_CYCLE)
        days = self._parse_cycle(cycle[1])
        return self.calendar.get_next_trading_day(order_date, offset=days)

    # ----------------------------------------------------------------
    # 每日批量确认
    # ----------------------------------------------------------------

    def process_daily_confirmations(self, today: date, user_id: int | None = None) -> int:
        """
        处理所有今日到期的份额确认
        返回确认笔数
        """
        today_str = today.isoformat()
        q = (
            self.db.query(TransactionRecord)
            .filter(
                TransactionRecord.confirm_date == today_str,
                TransactionRecord.status == "pending",
                TransactionRecord.trans_type.in_(["buy", "auto_buy"]),
            )
        )
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        pending = q.all()

        for txn in pending:
            self._confirm_one(txn)

        if pending:
            self.db.commit()
            logger.info(f"份额确认完成: {len(pending)}笔")
        return len(pending)

    def process_daily_settlements(self, today: date, user_id: int | None = None) -> int:
        """
        处理所有今日到账的赎回
        返回到账笔数
        """
        today_str = today.isoformat()
        q = (
            self.db.query(TransactionRecord)
            .filter(
                TransactionRecord.settle_date == today_str,
                TransactionRecord.status == "confirmed",
                TransactionRecord.trans_type == "sell",
            )
        )
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        pending = q.all()

        for txn in pending:
            self._settle_one(txn)

        if pending:
            self.db.commit()
            logger.info(f"赎回到账完成: {len(pending)}笔")
        return len(pending)

    # ----------------------------------------------------------------
    # 单笔处理
    # ----------------------------------------------------------------

    def _confirm_one(self, txn: TransactionRecord):
        """确认单笔买入"""
        holding = self._get_or_create_holding(
            txn.fund_code, txn.source_account_id, txn.user_id
        )
        shares = txn.confirm_shares or txn.shares or 0

        holding.total_shares += shares
        holding.available_shares += shares
        holding.frozen_shares = max(0, holding.frozen_shares - shares)
        holding.total_cost += txn.actual_amount or txn.amount
        holding.avg_cost_nav = (
            holding.total_cost / holding.total_shares
            if holding.total_shares > 0
            else 0
        )

        if holding.status == "closed":
            holding.status = "holding"
        if not holding.first_buy_date:
            holding.first_buy_date = txn.order_date

        txn.status = "confirmed"

    def _settle_one(self, txn: TransactionRecord):
        """结算单笔赎回"""
        if txn.source_account_id:
            account = (
                self.db.query(SavingsAccount)
                .filter_by(id=txn.source_account_id, user_id=txn.user_id)
                .first()
            )
            if account:
                account.balance += txn.actual_amount or txn.amount
        txn.status = "settled"

    def _get_or_create_holding(self, fund_code: str,
                                source_account_id: int | None,
                                user_id: int | None = None) -> FundHolding:
        """获取或创建持仓记录"""
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
