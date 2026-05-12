"""账户（银行卡 + 基金账户）"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class SavingsAccount(Base):
    __tablename__ = "savings_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, default=1)
    account_type: Mapped[str] = mapped_column(String(8), default="bank", nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(64), nullable=True)  # fund 时为基金名称
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # bank=余额 fund=当前市值
    pending_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 待确认金额（申购/赎回在途）
    currency: Mapped[str] = mapped_column(String(8), default="CNY")
    # 基金账户专用
    fund_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
