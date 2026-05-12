"""基金信息缓存表 + 净值历史表"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Fund(Base):
    __tablename__ = "funds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    fund_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    settle_cycle: Mapped[str] = mapped_column(String(8), default="T+1")
    redeem_cycle: Mapped[str] = mapped_column(String(8), default="T+3")
    management_fee: Mapped[float] = mapped_column(Float, default=0.0)
    custodian_fee: Mapped[float] = mapped_column(Float, default=0.0)
    nav: Mapped[float | None] = mapped_column(Float, nullable=True)
    nav_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    acc_nav: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_change: Mapped[float] = mapped_column(Float, default=0.0)
    estimate_nav: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimate_time: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    last_sync_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


class FundNavHistory(Base):
    __tablename__ = "fund_nav_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    nav_date: Mapped[str] = mapped_column(String(16), nullable=False)
    unit_nav: Mapped[float] = mapped_column(Float, nullable=False)
    acc_nav: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_change: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
