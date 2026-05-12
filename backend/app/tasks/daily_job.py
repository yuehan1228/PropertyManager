"""每日定时任务编排器 —— 遍历所有用户"""
import logging
from datetime import date
from sqlalchemy.orm import Session
from app.models.user import User
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
        is_trade = self.calendar.is_trading_day(today)

        # 获取所有用户
        users = self.db.query(User).all()
        if not users:
            # 没有用户时创建一个默认用户（兼容旧数据）
            default = User(id=1, openid="dev_user", nickname="默认用户")
            self.db.add(default)
            self.db.commit()
            users = [default]

        summary = {
            "date": today.isoformat(),
            "is_trade_day": is_trade,
            "user_count": len(users),
            "steps": [],
        }

        for user in users:
            uid = user.id
            try:
                self._run_for_user(today, is_trade, uid)
            except Exception:
                logger.exception(f"用户 {uid} ({user.nickname or user.openid}) 每日任务执行失败")

        summary["steps"].append(f"已为 {len(users)} 个用户执行每日任务")
        self.db.commit()
        logger.info(f"每日任务完成: {summary}")
        return summary

    def _run_for_user(self, today: date, is_trade: bool, user_id: int):
        """为单个用户运行每日任务"""
        # Step 1: 同步净值
        sync_result = self.fund_sync.sync_all_held_funds(today, user_id=user_id)

        if not is_trade:
            self.snapshot_svc.take_snapshot(today, is_trade_day=False, user_id=user_id)
            return

        # Step 2: 份额确认
        self.settlement.process_daily_confirmations(today, user_id=user_id)

        # Step 3: 赎回到账
        self.settlement.process_daily_settlements(today, user_id=user_id)

        # Step 4: 执行定投
        self.auto_invest.execute_due_plans(today, user_id=user_id)

        # Step 5: 计算盈亏
        self.pnl.calculate_daily_pnl(today, user_id=user_id)

        # Step 6: 快照
        self.snapshot_svc.take_snapshot(today, is_trade_day=True, user_id=user_id)

        logger.info(f"用户 {user_id} 每日任务完成: 净值同步={sync_result}")
