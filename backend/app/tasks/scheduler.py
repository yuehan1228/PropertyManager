"""APScheduler 定时任务配置"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.config import get_settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)
settings = get_settings()

_scheduler: BackgroundScheduler | None = None


def _daily_job():
    """每日定时任务入口"""
    from app.tasks.daily_job import DailyJobOrchestrator

    db = SessionLocal()
    try:
        orch = DailyJobOrchestrator(db)
        summary = orch.run()
        logger.info(f"定时任务执行完成: {summary['date']}")
    except Exception:
        logger.exception("定时任务执行失败")
    finally:
        db.close()


def start_scheduler():
    """启动 APScheduler"""
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone=settings.timezone)
    _scheduler.add_job(
        _daily_job,
        trigger=CronTrigger(
            hour=settings.daily_job_hour,
            minute=settings.daily_job_minute,
            timezone=settings.timezone,
        ),
        id="daily_fund_job",
        name="每日净值同步与结算",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        f"定时任务已启动: 每日 "
        f"{settings.daily_job_hour:02d}:{settings.daily_job_minute:02d} "
        f"({settings.timezone})"
    )


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("定时任务已停止")
