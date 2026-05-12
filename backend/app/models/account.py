"""储蓄卡 / 资金账户"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class SavingsAccount(Base):
    __tablename__ = "savings_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
