"""盈亏计算服务 —— 支持按用户隔离"""
import json
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.holding import FundHolding
from app.models.fund import Fund
from app.models.snapshot import DailyAssetSnapshot
from app.models.account import SavingsAccount

logger = logging.getLogger(__name__)


class PnLCalculator:
    """盈亏计算"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_daily_pnl(self, today: date, user_id: int | None = None) -> dict:
        """
        计算所有持仓的当日盈亏
        返回: {total_fund_value, daily_fund_profit, profit_summary_by_holding}
        """
        q = (
            self.db.query(FundHolding)
            .filter(FundHolding.status.in_(["holding", "partial_redeem"]))
        )
        if user_id is not None:
            q = q.filter_by(user_id=user_id)
        holdings = q.all()

        total_value = 0.0
        daily_profit = 0.0

        for h in holdings:
            fund_q = self.db.query(Fund).filter_by(code=h.fund_code)
            if user_id is not None:
                fund_q = fund_q.filter_by(user_id=user_id)
            fund = fund_q.first()
            if not fund or not fund.nav:
                continue

            yesterday_nav = self._get_yesterday_nav(fund, today)
            yesterday_value = h.total_shares * yesterday_nav

            today_value = h.total_shares * fund.nav
            today_profit = today_value - yesterday_value
            today_rate = (today_profit / yesterday_value * 100) if yesterday_value > 0 else 0.0

            h.current_value = today_value
            h.daily_profit = round(today_profit, 2)
            h.daily_profit_rate = round(today_rate, 4)
            h.last_update = today.isoformat()

            h.total_profit = h.current_value - h.total_cost
            h.profit_rate = (
                (h.total_profit / h.total_cost * 100) if h.total_cost > 0 else 0.0
            )

            total_value += today_value
            daily_profit += today_profit

        self.db.commit()

        # 同步基金账户余额
        self._sync_fund_accounts(user_id)

        result = {
            "total_fund_value": round(total_value, 2),
            "daily_fund_profit": round(daily_profit, 2),
        }
        logger.info(f"盈亏计算完成: 总市值={total_value:.2f} 日盈亏={daily_profit:.2f}")
        return result

    def _sync_fund_accounts(self, user_id: int | None):
        """将持仓市值同步到对应基金账户的 balance"""
        from app.models.account import SavingsAccount
        from app.models.holding import FundHolding

        fund_accounts = (
            self.db.query(SavingsAccount)
            .filter_by(account_type="fund", is_active=1)
        )
        if user_id is not None:
            fund_accounts = fund_accounts.filter_by(user_id=user_id)
        fund_accounts = fund_accounts.all()

        for acct in fund_accounts:
            if not acct.fund_code:
                continue
            holding = (
                self.db.query(FundHolding)
                .filter_by(fund_code=acct.fund_code, user_id=acct.user_id)
                .first()
            )
            if holding:
                acct.balance = round(holding.current_value, 2)
        self.db.commit()

    def _get_yesterday_nav(self, fund: Fund, today: date) -> float:
        from app.models.fund import FundNavHistory

        yesterday = (today - timedelta(days=1)).isoformat()
        row = (
            self.db.query(FundNavHistory)
            .filter_by(fund_code=fund.code, nav_date=yesterday)
            .first()
        )
        if row:
            return row.unit_nav

        row = (
            self.db.query(FundNavHistory)
            .filter(FundNavHistory.fund_code == fund.code)
            .order_by(FundNavHistory.nav_date.desc())
            .first()
        )
        if row:
            return row.unit_nav

        return fund.nav or 0.0


class SnapshotService:
    """每日资产快照"""

    def __init__(self, db: Session):
        self.db = db

    def take_snapshot(self, today: date, is_trade_day: bool, user_id: int | None = None) -> DailyAssetSnapshot:
        """拍摄当日资产快照"""
        today_str = today.isoformat()

        acct_q = self.db.query(SavingsAccount).filter_by(is_active=1)
        if user_id is not None:
            acct_q = acct_q.filter_by(user_id=user_id)
        accounts = acct_q.all()
        total_savings = sum(a.balance for a in accounts)

        hold_q = (
            self.db.query(FundHolding)
            .filter(FundHolding.status.in_(["holding", "partial_redeem"]))
        )
        if user_id is not None:
            hold_q = hold_q.filter_by(user_id=user_id)
        holdings = hold_q.all()
        total_fund_value = sum(h.current_value for h in holdings)
        total_assets = total_savings + total_fund_value
        daily_profit = sum(h.daily_profit for h in holdings)

        cumulative_profit = sum(h.total_profit for h in holdings)
        total_cost = sum(h.total_cost for h in holdings)
        cumulative_rate = (
            (cumulative_profit / total_cost * 100) if total_cost > 0 else 0.0
        )

        snap_q = self.db.query(DailyAssetSnapshot)
        if user_id is not None:
            snap_q = snap_q.filter_by(user_id=user_id)
        prev_snapshot = (
            snap_q.order_by(DailyAssetSnapshot.snapshot_date.desc()).first()
        )
        daily_profit_rate = 0.0
        if prev_snapshot and prev_snapshot.total_assets > 0:
            daily_profit_rate = (
                (total_assets - prev_snapshot.total_assets)
                / prev_snapshot.total_assets
                * 100
            )

        detail = []
        for h in holdings:
            detail.append({
                "fund_code": h.fund_code,
                "fund_name": h.fund_name,
                "shares": h.total_shares,
                "current_value": h.current_value,
                "daily_profit": h.daily_profit,
            })

        snapshot = DailyAssetSnapshot(
            user_id=user_id or 1,
            snapshot_date=today_str,
            is_trade_day=1 if is_trade_day else 0,
            total_savings=round(total_savings, 2),
            total_fund_value=round(total_fund_value, 2),
            total_assets=round(total_assets, 2),
            daily_fund_profit=round(daily_profit, 2),
            daily_profit_rate=round(daily_profit_rate, 4),
            cumulative_profit=round(cumulative_profit, 2),
            cumulative_rate=round(cumulative_rate, 4),
            detail_json=json.dumps(detail, ensure_ascii=False),
        )

        existing_q = self.db.query(DailyAssetSnapshot).filter_by(snapshot_date=today_str)
        if user_id is not None:
            existing_q = existing_q.filter_by(user_id=user_id)
        existing = existing_q.first()
        if existing:
            for key, value in snapshot.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
        else:
            self.db.add(snapshot)

        self.db.commit()
        logger.info(f"快照已保存: {today_str} 总资产={total_assets:.2f}")
        return snapshot
