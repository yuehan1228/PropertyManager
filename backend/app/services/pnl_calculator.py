"""盈亏计算服务"""
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

    def calculate_daily_pnl(self, today: date) -> dict:
        """
        计算所有持仓的当日盈亏
        返回: {total_fund_value, daily_fund_profit, profit_summary_by_holding}
        """
        holdings = (
            self.db.query(FundHolding)
            .filter(FundHolding.status.in_(["holding", "partial_redeem"]))
            .all()
        )

        total_value = 0.0
        daily_profit = 0.0

        for h in holdings:
            fund = self.db.query(Fund).filter_by(code=h.fund_code).first()
            if not fund or not fund.nav:
                continue

            # 昨日市值 = total_shares * 昨日净值
            yesterday_nav = self._get_yesterday_nav(fund, today)
            yesterday_value = h.total_shares * yesterday_nav

            # 今日市值
            today_value = h.total_shares * fund.nav
            today_profit = today_value - yesterday_value
            today_rate = (today_profit / yesterday_value * 100) if yesterday_value > 0 else 0.0

            # 更新持仓
            h.current_value = today_value
            h.daily_profit = round(today_profit, 2)
            h.daily_profit_rate = round(today_rate, 4)
            h.last_update = today.isoformat()

            # 更新累计
            h.total_profit = h.current_value - h.total_cost
            h.profit_rate = (
                (h.total_profit / h.total_cost * 100) if h.total_cost > 0 else 0.0
            )

            total_value += today_value
            daily_profit += today_profit

        self.db.commit()

        result = {
            "total_fund_value": round(total_value, 2),
            "daily_fund_profit": round(daily_profit, 2),
        }
        logger.info(f"盈亏计算完成: 总市值={total_value:.2f} 日盈亏={daily_profit:.2f}")
        return result

    def _get_yesterday_nav(self, fund: Fund, today: date) -> float:
        """获取昨日净值（优先查本地历史表）"""
        from app.models.fund import FundNavHistory

        yesterday = (today - timedelta(days=1)).isoformat()
        row = (
            self.db.query(FundNavHistory)
            .filter_by(fund_code=fund.code, nav_date=yesterday)
            .first()
        )
        if row:
            return row.unit_nav

        # Fallback: 上一条历史记录
        row = (
            self.db.query(FundNavHistory)
            .filter(FundNavHistory.fund_code == fund.code)
            .order_by(FundNavHistory.nav_date.desc())
            .first()
        )
        if row:
            return row.unit_nav

        # 最后 fallback: 基金表缓存的净值（同一天，涨跌幅为0）
        return fund.nav or 0.0


class SnapshotService:
    """每日资产快照"""

    def __init__(self, db: Session):
        self.db = db

    def take_snapshot(self, today: date, is_trade_day: bool) -> DailyAssetSnapshot:
        """拍摄当日资产快照"""
        today_str = today.isoformat()

        # 汇总储蓄卡余额
        accounts = self.db.query(SavingsAccount).filter_by(is_active=1).all()
        total_savings = sum(a.balance for a in accounts)

        # 汇总基金市值
        holdings = (
            self.db.query(FundHolding)
            .filter(FundHolding.status.in_(["holding", "partial_redeem"]))
            .all()
        )
        total_fund_value = sum(h.current_value for h in holdings)
        total_assets = total_savings + total_fund_value
        daily_profit = sum(h.daily_profit for h in holdings)

        # 累计盈亏
        cumulative_profit = sum(h.total_profit for h in holdings)
        total_cost = sum(h.total_cost for h in holdings)
        cumulative_rate = (
            (cumulative_profit / total_cost * 100) if total_cost > 0 else 0.0
        )

        # 总资产收益率
        prev_snapshot = (
            self.db.query(DailyAssetSnapshot)
            .order_by(DailyAssetSnapshot.snapshot_date.desc())
            .first()
        )
        daily_profit_rate = 0.0
        if prev_snapshot and prev_snapshot.total_assets > 0:
            daily_profit_rate = (
                (total_assets - prev_snapshot.total_assets)
                / prev_snapshot.total_assets
                * 100
            )

        # 持仓明细 JSON
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

        existing = self.db.query(DailyAssetSnapshot).filter_by(snapshot_date=today_str).first()
        if existing:
            # 更新已有快照
            for key, value in snapshot.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
        else:
            self.db.add(snapshot)

        self.db.commit()
        logger.info(f"快照已保存: {today_str} 总资产={total_assets:.2f}")
        return snapshot
