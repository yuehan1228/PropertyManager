"""账户管理 —— 银行卡 + 基金账户"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.account import SavingsAccount
from app.schemas.common import (
    SavingsAccountCreate, SavingsAccountUpdate, SavingsAccountOut, MessageOut,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[SavingsAccountOut])
def list_accounts(
    account_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(SavingsAccount)
        .filter_by(user_id=current_user.id)
        .order_by(SavingsAccount.sort_order)
    )
    if account_type:
        q = q.filter_by(account_type=account_type)
    return q.all()


@router.post("", response_model=SavingsAccountOut)
def create_account(
    data: SavingsAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acct = SavingsAccount(user_id=current_user.id, **data.model_dump())
    db.add(acct)
    db.commit()
    db.refresh(acct)
    return acct


@router.get("/{account_id}", response_model=SavingsAccountOut)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acct = (
        db.query(SavingsAccount)
        .filter_by(id=account_id, user_id=current_user.id)
        .first()
    )
    if not acct:
        raise HTTPException(404, "账户不存在")
    return acct


@router.put("/{account_id}", response_model=SavingsAccountOut)
def update_account(
    account_id: int,
    data: SavingsAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acct = (
        db.query(SavingsAccount)
        .filter_by(id=account_id, user_id=current_user.id)
        .first()
    )
    if not acct:
        raise HTTPException(404, "账户不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(acct, key, value)
    db.commit()
    db.refresh(acct)
    return acct


@router.delete("/{account_id}", response_model=MessageOut)
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acct = (
        db.query(SavingsAccount)
        .filter_by(id=account_id, user_id=current_user.id)
        .first()
    )
    if not acct:
        raise HTTPException(404, "账户不存在")
    db.delete(acct)
    db.commit()
    return MessageOut(message="账户已删除")
