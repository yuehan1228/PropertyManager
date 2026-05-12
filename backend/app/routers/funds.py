"""基金管理 & 净值同步 —— 按用户隔离"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.fund import Fund, FundNavHistory
from app.schemas.common import FundCreate, FundUpdate, FundOut, MessageOut
from app.services.fund_sync import FundDataSyncService
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/funds", tags=["funds"])


@router.get("", response_model=list[FundOut])
def list_funds(
    is_active: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Fund).filter_by(user_id=current_user.id).order_by(Fund.code)
    if is_active is not None:
        q = q.filter_by(is_active=is_active)
    return q.all()


@router.post("", response_model=FundOut)
def add_fund(
    data: FundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = (
        db.query(Fund)
        .filter_by(user_id=current_user.id, code=data.code)
        .first()
    )
    if existing:
        raise HTTPException(409, "基金代码已存在")

    fund = Fund(user_id=current_user.id, **data.model_dump())
    db.add(fund)
    db.commit()

    # 后台拉取基本信息
    svc = FundDataSyncService(db)
    svc.sync_fund_info(fund.code)

    db.refresh(fund)
    return fund


@router.get("/{code}", response_model=FundOut)
def get_fund(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fund = (
        db.query(Fund)
        .filter_by(user_id=current_user.id, code=code)
        .first()
    )
    if not fund:
        raise HTTPException(404, "基金不存在")
    return fund


@router.put("/{code}", response_model=FundOut)
def update_fund(
    code: str,
    data: FundUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fund = (
        db.query(Fund)
        .filter_by(user_id=current_user.id, code=code)
        .first()
    )
    if not fund:
        raise HTTPException(404, "基金不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(fund, key, value)
    db.commit()
    db.refresh(fund)
    return fund


@router.delete("/{code}", response_model=MessageOut)
def delete_fund(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    fund = (
        db.query(Fund)
        .filter_by(user_id=current_user.id, code=code)
        .first()
    )
    if not fund:
        raise HTTPException(404, "基金不存在")
    db.delete(fund)
    db.commit()
    return MessageOut(message="基金已删除")


@router.post("/{code}/sync", response_model=dict)
def sync_fund(
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发净值/信息同步"""
    fund = (
        db.query(Fund)
        .filter_by(user_id=current_user.id, code=code)
        .first()
    )
    if not fund:
        raise HTTPException(404, "基金不存在")
    svc = FundDataSyncService(db)
    info = svc.sync_fund_info(code)
    nav_result = svc.sync_latest_nav(code)
    estimate = svc.sync_fund_estimate(code)
    return {"info": info.name if info else None, **nav_result, **estimate}


@router.get("/{code}/nav-history", response_model=list[dict])
def nav_history(
    code: str,
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 验证基金属于当前用户
    fund = (
        db.query(Fund)
        .filter_by(user_id=current_user.id, code=code)
        .first()
    )
    if not fund:
        raise HTTPException(404, "基金不存在")

    rows = (
        db.query(FundNavHistory)
        .filter_by(fund_code=code)
        .order_by(FundNavHistory.nav_date.desc())
        .limit(limit)
        .all()
    )
    return [
        {"nav_date": r.nav_date, "unit_nav": r.unit_nav, "daily_change": r.daily_change}
        for r in rows
    ]
