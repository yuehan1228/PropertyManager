"""个人资产追踪系统 —— FastAPI 入口"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

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
        # 数据迁移：确保所有旧数据有 user_id（兼容升级）
        _migrate_existing_data(db)
        # DDL 迁移：补充缺失列
        _migrate_schema(db)
        # 将已有基金账户余额同步到持仓表
        _sync_existing_fund_accounts(db)

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


def _migrate_existing_data(db):
    """将没有 user_id 的旧数据迁移到默认用户"""
    from app.models.user import User
    from app.models.account import SavingsAccount
    from app.models.fund import Fund
    from app.models.holding import FundHolding
    from app.models.plan import InvestmentPlan
    from app.models.transaction import TransactionRecord
    from app.models.snapshot import DailyAssetSnapshot

    # 确保默认用户存在
    default_user = db.query(User).filter_by(openid="dev_user").first()
    if not default_user:
        default_user = User(id=1, openid="dev_user", nickname="默认用户")
        db.add(default_user)
        db.commit()
        db.refresh(default_user)
        logger.info("已创建默认用户 (id=1)")

    # 为各表 NULL user_id 的行设置默认值
    models = [
        (SavingsAccount, "savings_accounts"),
        (Fund, "funds"),
        (FundHolding, "fund_holdings"),
        (InvestmentPlan, "investment_plans"),
        (TransactionRecord, "transaction_records"),
        (DailyAssetSnapshot, "daily_asset_snapshots"),
    ]
    for model, table_name in models:
        try:
            count = (
                db.query(model)
                .filter(model.user_id.is_(None))
                .update({model.user_id: 1}, synchronize_session=False)
            )
            if count:
                db.commit()
                logger.info(f"已迁移 {table_name}: {count} 行 → user_id=1")
        except Exception:
            logger.exception(f"迁移 {table_name} 失败，可能列不存在")
    logger.info("数据迁移完成")


def _migrate_schema(db):
    """补充缺失的数据库列（DDL 迁移）"""
    from sqlalchemy import text

    migrations = [
        ("savings_accounts", "account_type", "VARCHAR(8) NOT NULL DEFAULT 'bank'"),
        ("savings_accounts", "fund_code", "VARCHAR(16)"),
        ("savings_accounts", "pending_amount", "FLOAT NOT NULL DEFAULT 0.0"),
    ]
    for table, column, col_def in migrations:
        try:
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
            db.commit()
            logger.info(f"DDL 迁移: {table}.{column} 已添加")
        except Exception:
            db.rollback()
            # 列已存在则忽略
            logger.debug(f"DDL 迁移: {table}.{column} 已存在，跳过")


def _sync_existing_fund_accounts(db):
    """一次性将已有基金账户的 balance 同步到 FundHolding 表"""
    from app.models.account import SavingsAccount
    from app.models.fund import Fund
    from app.models.holding import FundHolding

    fund_accounts = (
        db.query(SavingsAccount)
        .filter_by(account_type="fund", is_active=1)
        .all()
    )
    created = 0
    for acct in fund_accounts:
        if not acct.fund_code or acct.balance <= 0:
            continue
        existing = (
            db.query(FundHolding)
            .filter_by(user_id=acct.user_id, fund_code=acct.fund_code)
            .first()
        )
        if existing:
            continue  # 已有持仓，跳过
        fund = db.query(Fund).filter_by(code=acct.fund_code, user_id=acct.user_id).first()
        holding = FundHolding(
            user_id=acct.user_id,
            fund_code=acct.fund_code,
            fund_name=fund.name if fund else acct.fund_code,
            total_cost=acct.balance,
            current_value=acct.balance,
            status="holding",
        )
        db.add(holding)
        created += 1

    if created:
        db.commit()
        logger.info(f"一次性同步: 为 {created} 个已有基金账户创建持仓记录")

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
from app.routers import accounts, funds, holdings, transactions, plans, dashboard, admin, auth

app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(funds.router)
app.include_router(holdings.router)
app.include_router(transactions.router)
app.include_router(plans.router)
app.include_router(dashboard.router)
app.include_router(admin.router)

# ---------------------------------------------------------------------------
# 静态文件
# ---------------------------------------------------------------------------
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ---------------------------------------------------------------------------
# 基础端点
# ---------------------------------------------------------------------------
@app.get("/")
def root():
    """返回 Web 前端页面"""
    index_path = os.path.join(static_dir, "index.html")
    return FileResponse(index_path)

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
