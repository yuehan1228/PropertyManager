"""A 股交易日历缓存"""
from datetime import datetime
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class TradingCalendar(Base):
    __tablename__ = "trading_calendar"

    date: Mapped[str] = mapped_column(String(16), primary_key=True)
    is_trade: Mapped[int] = mapped_column(Integer, nullable=False)
    week_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    holiday: Mapped[str | None] = mapped_column(String(32), nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
