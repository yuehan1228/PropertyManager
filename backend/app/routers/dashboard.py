"""总资产看板"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.account import SavingsAccount
from app.models.holding import FundHolding
from app.models.snapshot import DailyAssetSnapshot
from app.schemas.common import DashboardOut, FundHoldingOut, SavingsAccountOut, SnapshotOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    accounts = db.query(SavingsAccount).filter_by(is_active=1).order_by(SavingsAccount.sort_order).all()
    holdings = (
        db.query(FundHolding)
        .filter(FundHolding.status.in_(["holding", "partial_redeem"]))
        .order_by(FundHolding.updated_at.desc())
        .all()
    )

    total_savings = sum(a.balance for a in accounts)
    total_fund_value = sum(h.current_value for h in holdings)
    total_assets = total_savings + total_fund_value
    daily_profit = sum(h.daily_profit for h in holdings)
    cumulative_profit = sum(h.total_profit for h in holdings)
    total_cost = sum(h.total_cost for h in holdings)

    daily_profit_rate = 0.0
    prev_snapshot = (
        db.query(DailyAssetSnapshot)
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

    return DashboardOut(
        total_savings=round(total_savings, 2),
        total_fund_value=round(total_fund_value, 2),
        total_assets=round(total_assets, 2),
        daily_profit=round(daily_profit, 2),
        daily_profit_rate=daily_profit_rate,
        cumulative_profit=round(cumulative_profit, 2),
        cumulative_rate=cumulative_rate,
        holding_count=len(holdings),
        holdings=[FundHoldingOut.model_validate(h) for h in holdings],
        accounts=[SavingsAccountOut.model_validate(a) for a in accounts],
    )


@router.get("/snapshots", response_model=list[SnapshotOut])
def list_snapshots(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return (
        db.query(DailyAssetSnapshot)
        .order_by(DailyAssetSnapshot.snapshot_date.desc())
        .limit(limit)
        .all()
    )
