"""个人资产追踪系统 —— FastAPI 入口"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import get_engine
from app.models.base import Base

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# 屏蔽 sqlalchemy 和 apscheduler 的 debug 日志
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# 生命周期
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("正在初始化数据库...")
    Base.metadata.create_all(bind=get_engine())

    from datetime import date
    from app.database import SessionLocal
    from app.services.trading_calendar import TradingCalendarService

    db = SessionLocal()
    try:
        cal = TradingCalendarService(db)
        cal.sync_calendar_from_remote(date.today().year)
    except Exception:
        logger.exception("交易日历初始化同步失败（应用仍可运行）")
    finally:
        db.close()

    from app.tasks.scheduler import start_scheduler
    start_scheduler()

    logger.info("应用启动完成 ✓")
    yield

    from app.tasks.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("应用已关闭")

# ---------------------------------------------------------------------------
# 应用实例
# ---------------------------------------------------------------------------
app = FastAPI(
    title="个人资产追踪系统",
    description="储蓄卡管理 + 基金净值同步 + T+N 结算 + 定投 + 盈亏计算",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# 请求日志 & 耗时中间件
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response

# ---------------------------------------------------------------------------
# 全局异常处理
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("未捕获异常: %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误", "error": str(exc)},
    )

# ---------------------------------------------------------------------------
# 路由注册
# ---------------------------------------------------------------------------
from app.routers import accounts, funds, holdings, transactions, plans, dashboard, admin

app.include_router(accounts.router)
app.include_router(funds.router)
app.include_router(holdings.router)
app.include_router(transactions.router)
app.include_router(plans.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

# ---------------------------------------------------------------------------
# 基础端点
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    return {
        "app": "个人资产追踪系统",
        "version": "0.1.0",
        "docs": "/docs",
    }

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
