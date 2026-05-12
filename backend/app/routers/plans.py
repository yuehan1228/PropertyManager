"""定投计划管理"""
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.plan import InvestmentPlan
from app.models.fund import Fund
from app.models.account import SavingsAccount
from app.schemas.common import (
    InvestmentPlanCreate, InvestmentPlanUpdate, InvestmentPlanOut, MessageOut,
)

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("", response_model=list[InvestmentPlanOut])
def list_plans(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(InvestmentPlan).order_by(InvestmentPlan.created_at.desc())
    if status:
        q = q.filter_by(status=status)
    return q.all()


@router.post("", response_model=InvestmentPlanOut)
def create_plan(data: InvestmentPlanCreate, db: Session = Depends(get_db)):
    # 校验
    fund = db.query(Fund).filter_by(code=data.fund_code).first()
    if not fund:
        raise HTTPException(404, "基金不存在")
    account = db.query(SavingsAccount).get(data.from_account_id)
    if not account:
        raise HTTPException(404, "扣款账户不存在")

    plan = InvestmentPlan(**data.model_dump())
    plan.next_execute_date = data.start_date
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=InvestmentPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(InvestmentPlan).get(plan_id)
    if not plan:
        raise HTTPException(404, "定投计划不存在")
    return plan


@router.put("/{plan_id}", response_model=InvestmentPlanOut)
def update_plan(plan_id: int, data: InvestmentPlanUpdate,
                db: Session = Depends(get_db)):
    plan = db.query(InvestmentPlan).get(plan_id)
    if not plan:
        raise HTTPException(404, "定投计划不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{plan_id}", response_model=MessageOut)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(InvestmentPlan).get(plan_id)
    if not plan:
        raise HTTPException(404, "定投计划不存在")
    db.delete(plan)
    db.commit()
    return MessageOut(message="定投计划已删除")
