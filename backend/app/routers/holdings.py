"""持仓查询"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.holding import FundHolding
from app.schemas.common import FundHoldingOut

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.get("", response_model=list[FundHoldingOut])
def list_holdings(db: Session = Depends(get_db)):
    return (
        db.query(FundHolding)
        .filter(FundHolding.status.in_(["holding", "partial_redeem"]))
        .order_by(FundHolding.updated_at.desc())
        .all()
    )


@router.get("/{holding_id}", response_model=FundHoldingOut)
def get_holding(holding_id: int, db: Session = Depends(get_db)):
    h = db.query(FundHolding).get(holding_id)
    if not h:
        raise HTTPException(404, "持仓记录不存在")
    return h
