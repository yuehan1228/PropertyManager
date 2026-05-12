"""储蓄账户 CRUD"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.account import SavingsAccount
from app.schemas.common import (
    SavingsAccountCreate, SavingsAccountUpdate, SavingsAccountOut, MessageOut,
)

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[SavingsAccountOut])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(SavingsAccount).order_by(SavingsAccount.sort_order).all()


@router.post("", response_model=SavingsAccountOut)
def create_account(data: SavingsAccountCreate, db: Session = Depends(get_db)):
    acct = SavingsAccount(**data.model_dump())
    db.add(acct)
    db.commit()
    db.refresh(acct)
    return acct


@router.get("/{account_id}", response_model=SavingsAccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    acct = db.query(SavingsAccount).get(account_id)
    if not acct:
        raise HTTPException(404, "账户不存在")
    return acct


@router.put("/{account_id}", response_model=SavingsAccountOut)
def update_account(account_id: int, data: SavingsAccountUpdate,
                   db: Session = Depends(get_db)):
    acct = db.query(SavingsAccount).get(account_id)
    if not acct:
        raise HTTPException(404, "账户不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(acct, key, value)
    db.commit()
    db.refresh(acct)
    return acct


@router.delete("/{account_id}", response_model=MessageOut)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    acct = db.query(SavingsAccount).get(account_id)
    if not acct:
        raise HTTPException(404, "账户不存在")
    db.delete(acct)
    db.commit()
    return MessageOut(message="账户已删除")
