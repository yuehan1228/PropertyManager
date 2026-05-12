"""交易记录（买入 / 卖出 / 分红 / 拆合 / 自动买入）"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class TransactionRecord(Base):
    __tablename__ = "transaction_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=1)
    trans_type: Mapped[str] = mapped_column(String(16), nullable=False)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    fund_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    nav: Mapped[float | None] = mapped_column(Float, nullable=True)
    shares: Mapped[float | None] = mapped_column(Float, nullable=True)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    actual_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    order_date: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    confirm_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    settle_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    source_account_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_holding_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plan_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    confirm_shares: Mapped[float | None] = mapped_column(Float, nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
