"""用户基金持仓"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class FundHolding(Base):
    __tablename__ = "fund_holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    fund_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    total_shares: Mapped[float] = mapped_column(Float, default=0.0)
    available_shares: Mapped[float] = mapped_column(Float, default=0.0)
    frozen_shares: Mapped[float] = mapped_column(Float, default=0.0)
    avg_cost_nav: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_cost: Mapped[float] = mapped_column(Float, default=0.0)
    current_value: Mapped[float] = mapped_column(Float, default=0.0)
    total_profit: Mapped[float] = mapped_column(Float, default=0.0)
    profit_rate: Mapped[float] = mapped_column(Float, default=0.0)
    daily_profit: Mapped[float] = mapped_column(Float, default=0.0)
    daily_profit_rate: Mapped[float] = mapped_column(Float, default=0.0)
    hold_days: Mapped[int] = mapped_column(Integer, default=0)
    source_account_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="holding")
    first_buy_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    last_update: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
