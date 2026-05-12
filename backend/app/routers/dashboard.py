"""总资产看板"""
import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.account import SavingsAccount
from app.models.holding import FundHolding
from app.models.snapshot import DailyAssetSnapshot
from app.schemas.common import DashboardOut, FundHoldingOut, SavingsAccountOut, SnapshotOut
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的资产总览"""
    accounts = (
        db.query(SavingsAccount)
        .filter_by(user_id=current_user.id, is_active=1)
        .order_by(SavingsAccount.sort_order)
        .all()
    )
    holdings = (
        db.query(FundHolding)
        .filter(
            FundHolding.user_id == current_user.id,
            FundHolding.status.in_(["holding", "partial_redeem"]),
        )
        .order_by(FundHolding.updated_at.desc())
        .all()
    )

    # 银行卡余额（仅 bank 类型）
    total_savings = sum(a.balance for a in accounts if a.account_type == "bank")
    # 基金市值来自持仓
    total_fund_value = sum(h.current_value or 0 for h in holdings)
    # 待确认金额（仅基金账户）
    total_pending = sum(a.pending_amount or 0 for a in accounts if a.account_type == "fund")
    total_assets = total_savings + total_fund_value + total_pending
    daily_profit = sum(h.daily_profit or 0 for h in holdings)
    cumulative_profit = sum(h.total_profit or 0 for h in holdings)
    total_cost = sum(h.total_cost or 0 for h in holdings)

    daily_profit_rate = 0.0
    prev_snapshot = (
        db.query(DailyAssetSnapshot)
        .filter_by(user_id=current_user.id)
        .order_by(DailyAssetSnapshot.snapshot_date.desc())
        .first()
    )
    if prev_snapshot and prev_snapshot.total_assets > 0:
        daily_profit_rate = round(
            (total_assets - prev_snapshot.total_assets) / prev_snapshot.total_assets * 100,
            4,
        )

    cumulative_rate = round(
        (cumulative_profit / total_cost * 100) if total_cost > 0 else 0.0,
        4,
    )

    def _safe(v, default=0.0):
        return default if v is None or (isinstance(v, float) and math.isnan(v)) else v

    return DashboardOut(
        total_savings=round(_safe(total_savings), 2),
        total_fund_value=round(_safe(total_fund_value), 2),
        total_assets=round(_safe(total_assets), 2),
        total_pending=round(_safe(total_pending), 2),
        daily_profit=round(_safe(daily_profit), 2),
        daily_profit_rate=_safe(daily_profit_rate),
        cumulative_profit=round(_safe(cumulative_profit), 2),
        cumulative_rate=_safe(cumulative_rate),
        holding_count=len(holdings),
        holdings=[FundHoldingOut.model_validate(h) for h in holdings],
        accounts=[SavingsAccountOut.model_validate(a) for a in accounts],
    )


@router.get("/snapshots", response_model=list[SnapshotOut])
def list_snapshots(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(DailyAssetSnapshot)
        .filter_by(user_id=current_user.id)
        .order_by(DailyAssetSnapshot.snapshot_date.desc())
        .limit(limit)
        .all()
    )
