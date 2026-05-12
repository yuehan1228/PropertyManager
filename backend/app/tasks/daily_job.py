"""每日定时任务编排器"""
import logging
from datetime import date
from sqlalchemy.orm import Session
from app.services.trading_calendar import TradingCalendarService
from app.services.fund_sync import FundDataSyncService
from app.services.settlement import SettlementService
from app.services.auto_invest import AutoInvestService
from app.services.pnl_calculator import PnLCalculator, SnapshotService

logger = logging.getLogger(__name__)


class DailyJobOrchestrator:
    """每日定时任务总编排"""

    def __init__(self, db: Session):
        self.db = db
        self.calendar = TradingCalendarService(db)
        self.fund_sync = FundDataSyncService(db)
        self.settlement = SettlementService(db)
        self.auto_invest = AutoInvestService(db)
        self.pnl = PnLCalculator(db)
        self.snapshot_svc = SnapshotService(db)

    def run(self) -> dict:
        """执行全部每日任务，返回摘要"""
        today = date.today()
        summary = {"date": today.isoformat(), "steps": []}

        is_trade = self.calendar.is_trading_day(today)
        summary["is_trade_day"] = is_trade

        # Step 1: 同步净值
        sync_result = self.fund_sync.sync_all_held_funds(today)
        summary["steps"].append(f"净值同步: {sync_result}")

        if not is_trade:
            self.snapshot_svc.take_snapshot(today, is_trade_day=False)
            summary["steps"].append("非交易日，仅拍快照")
            self.db.commit()
            return summary

        # Step 2: 份额确认
        confirm_count = self.settlement.process_daily_confirmations(today)
        summary["steps"].append(f"份额确认: {confirm_count}笔")

        # Step 3: 赎回到账
        settle_count = self.settlement.process_daily_settlements(today)
        summary["steps"].append(f"赎回到账: {settle_count}笔")

        # Step 4: 执行定投
        invest_count = self.auto_invest.execute_due_plans(today)
        summary["steps"].append(f"定投执行: {invest_count}笔")

        # Step 5: 计算盈亏
        pnl_result = self.pnl.calculate_daily_pnl(today)
        summary["steps"].append(f"盈亏计算: 总市值={pnl_result['total_fund_value']}")

        # Step 6: 快照
        self.snapshot_svc.take_snapshot(today, is_trade_day=True)
        summary["steps"].append("快照已保存")

        self.db.commit()
        logger.info(f"每日任务完成: {summary}")
        return summary
