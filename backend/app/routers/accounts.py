"""账户管理 —— 银行卡 + 基金账户"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.account import SavingsAccount
from app.models.fund import Fund
from app.models.holding import FundHolding
from app.schemas.common import (
    SavingsAccountCreate, SavingsAccountUpdate, SavingsAccountOut, MessageOut,
)
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def _sync_account_to_holding(acct: SavingsAccount, db: Session):
    """基金账户变更时同步创建/更新 FundHolding，确保 Dashboard 和持仓列表可见"""
    if acct.account_type != "fund" or not acct.fund_code:
        return

    holding = (
        db.query(FundHolding)
        .filter_by(
            user_id=acct.user_id,
            fund_code=acct.fund_code,
        )
        .first()
    )

    if holding:
        # 已有持仓：更新市值（净值同步会覆盖为精确值）
        holding.current_value = acct.balance
        if holding.total_cost == 0:
            holding.total_cost = acct.balance  # 初始录入视为成本
    else:
        # 无持仓：创建新记录
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
        db.flush()
        logger.info("自动创建持仓: fund=%s user=%d value=%.2f", acct.fund_code, acct.user_id, acct.balance)


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
    _sync_account_to_holding(acct, db)
    db.commit()
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
    _sync_account_to_holding(acct, db)
    db.commit()
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
