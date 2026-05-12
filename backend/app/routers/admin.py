"""管理接口：交易日历同步、手动触发定时任务"""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.trading_calendar import TradingCalendarService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/sync-calendar")
def sync_calendar(year: int | None = None, db: Session = Depends(get_db)):
    """手动同步交易日历"""
    if year is None:
        year = date.today().year
    svc = TradingCalendarService(db)
    count = svc.sync_calendar_from_remote(year)
    return {"year": year, "synced": count}


@router.post("/run-daily-job")
def run_daily_job(db: Session = Depends(get_db)):
    """手动触发每日定时任务（调试用）"""
    from app.tasks.daily_job import DailyJobOrchestrator
    orch = DailyJobOrchestrator(db)
    summary = orch.run()
    return summary
