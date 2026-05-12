"""交易记录 CRUD + 买入/卖出核心流程"""
import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.transaction import TransactionRecord
from app.models.fund import Fund
from app.models.account import SavingsAccount
from app.models.holding import FundHolding
from app.schemas.common import TransactionCreate, TransactionOut, MessageOut
from app.services.trading_calendar import TradingCalendarService
from app.services.settlement import SettlementService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    fund_code: str | None = Query(None),
    status: str | None = Query(None),
    trans_type: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(TransactionRecord).order_by(TransactionRecord.created_at.desc())
    if fund_code:
        q = q.filter_by(fund_code=fund_code)
    if status:
        q = q.filter_by(status=status)
    if trans_type:
        q = q.filter_by(trans_type=trans_type)
    return q.limit(limit).all()


@router.get("/{txn_id}", response_model=TransactionOut)
def get_transaction(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(TransactionRecord).get(txn_id)
    if not txn:
        raise HTTPException(404, "交易记录不存在")
    return txn


@router.post("/buy", response_model=TransactionOut)
def buy_fund(data: TransactionCreate, db: Session = Depends(get_db)):
    """手动买入基金"""
    if data.trans_type != "buy":
        raise HTTPException(400, "请使用 /buy 端点进行买入操作")

    # 校验
    fund = db.query(Fund).filter_by(code=data.fund_code).first()
    if not fund:
        raise HTTPException(404, "基金不存在")

    if data.source_account_id:
        account = db.query(SavingsAccount).get(data.source_account_id)
        if not account:
            raise HTTPException(404, "扣款账户不存在")
        if account.balance < data.amount:
            raise HTTPException(400, "账户余额不足")

    # 计算份额
    cal = TradingCalendarService(db)
    settlement = SettlementService(db)

    order_d = date.fromisoformat(data.order_date)

    # 若下单日非交易日，自动顺延
    if not cal.is_trading_day(order_d):
        order_d = cal.get_next_trading_day(order_d)

    # 使用输入净值或基金当前净值
    nav = data.nav or fund.nav
    if not nav:
        raise HTTPException(400, "净值不可用，请手动输入或先同步数据")

    fee = data.fee
    actual_amount = data.amount - fee
    shares = actual_amount / nav
    confirm_date = settlement.compute_confirm_date(order_d, fund.fund_type)

    # 扣款
    if data.source_account_id:
        account = db.query(SavingsAccount).get(data.source_account_id)
        account.balance -= data.amount

    # 创建交易
    txn = TransactionRecord(
        trans_type="buy",
        fund_code=fund.code,
        fund_name=fund.name,
        amount=data.amount,
        nav=nav,
        shares=round(shares, 4),
        fee=fee,
        actual_amount=actual_amount,
        order_date=order_d.isoformat(),
        confirm_date=confirm_date.isoformat(),
        source_account_id=data.source_account_id,
        status="pending",
        confirm_shares=round(shares, 4),
        remark=data.remark,
    )
    db.add(txn)
    db.flush()

    # 冻结份额
    holding = (
        db.query(FundHolding)
        .filter_by(fund_code=fund.code, source_account_id=data.source_account_id)
        .first()
    )
    if not holding:
        holding = FundHolding(
            fund_code=fund.code,
            fund_name=fund.name,
            source_account_id=data.source_account_id,
        )
        db.add(holding)
        db.flush()
    holding.frozen_shares += round(shares, 4)

    db.commit()
    db.refresh(txn)
    logger.info(f"手动买入: {fund.name} 金额={data.amount} 确认日期={confirm_date}")
    return txn


@router.post("/sell", response_model=TransactionOut)
def sell_fund(data: TransactionCreate, db: Session = Depends(get_db)):
    """手动赎回基金"""
    if data.trans_type != "sell":
        raise HTTPException(400, "请使用 /sell 端点进行卖出操作")

    fund = db.query(Fund).filter_by(code=data.fund_code).first()
    if not fund:
        raise HTTPException(404, "基金不存在")

    # 查找持仓
    holding = (
        db.query(FundHolding)
        .filter_by(fund_code=fund.code, source_account_id=data.source_account_id)
        .first()
    )
    if not holding or holding.status == "closed":
        raise HTTPException(400, "无可用持仓")

    cal = TradingCalendarService(db)
    settlement = SettlementService(db)

    order_d = date.fromisoformat(data.order_date)
    if not cal.is_trading_day(order_d):
        order_d = cal.get_next_trading_day(order_d)

    nav = data.nav or fund.nav
    if not nav:
        raise HTTPException(400, "净值不可用")

    shares = data.amount / nav

    if shares > holding.available_shares:
        raise HTTPException(
            400,
            f"可用份额不足: 需要 {shares:.4f}, 可用 {holding.available_shares:.4f}",
        )

    fee = data.fee
    actual_amount = data.amount - fee
    settle_date = settlement.compute_redeem_date(order_d, fund.fund_type)

    # 扣减持仓
    holding.available_shares -= shares
    holding.total_shares -= shares
    holding.total_cost -= holding.avg_cost_nav * shares if holding.avg_cost_nav else 0
    if holding.total_shares <= 0.0001:
        holding.status = "closed"

    # 创建交易
    txn = TransactionRecord(
        trans_type="sell",
        fund_code=fund.code,
        fund_name=fund.name,
        amount=data.amount,
        nav=nav,
        shares=round(shares, 4),
        fee=fee,
        actual_amount=actual_amount,
        order_date=order_d.isoformat(),
        settle_date=settle_date.isoformat(),
        source_account_id=data.source_account_id,
        status="pending",
        remark=data.remark,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    logger.info(f"手动赎回: {fund.name} 份额={shares:.4f} 到账日期={settle_date}")
    return txn


@router.delete("/{txn_id}", response_model=MessageOut)
def delete_transaction(txn_id: int, db: Session = Depends(get_db)):
    txn = db.query(TransactionRecord).get(txn_id)
    if not txn:
        raise HTTPException(404, "交易记录不存在")
    if txn.status != "pending":
        raise HTTPException(400, "只能删除 pending 状态的交易")
    db.delete(txn)
    db.commit()
    return MessageOut(message="交易已删除")
