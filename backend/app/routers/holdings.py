"""持仓查询与编辑 —— 按用户隔离"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.holding import FundHolding
from app.schemas.common import FundHoldingOut
from app.utils.auth import get_current_user


class HoldingUpdate(BaseModel):
    total_shares: float | None = None
    available_shares: float | None = None
    frozen_shares: float | None = None
    total_cost: float | None = None
    avg_cost_nav: float | None = None

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.get("", response_model=list[FundHoldingOut])
def list_holdings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(FundHolding)
        .filter(
            FundHolding.user_id == current_user.id,
            FundHolding.status.in_(["holding", "partial_redeem"]),
        )
        .order_by(FundHolding.updated_at.desc())
        .all()
    )


@router.get("/{holding_id}", response_model=FundHoldingOut)
def get_holding(
    holding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    h = (
        db.query(FundHolding)
        .filter_by(id=holding_id, user_id=current_user.id)
        .first()
    )
    if not h:
        raise HTTPException(404, "持仓记录不存在")
    return h


@router.put("/{holding_id}", response_model=FundHoldingOut)
def update_holding(
    holding_id: int,
    data: HoldingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动编辑持仓数据（份额、成本等）"""
    h = (
        db.query(FundHolding)
        .filter_by(id=holding_id, user_id=current_user.id)
        .first()
    )
    if not h:
        raise HTTPException(404, "持仓记录不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(h, key, value)
    db.commit()
    db.refresh(h)
    return h
