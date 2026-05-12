"""每日资产快照"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class DailyAssetSnapshot(Base):
    __tablename__ = "daily_asset_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    is_trade_day: Mapped[int] = mapped_column(Integer, default=1)
    total_savings: Mapped[float] = mapped_column(Float, default=0.0)
    total_fund_value: Mapped[float] = mapped_column(Float, default=0.0)
    total_assets: Mapped[float] = mapped_column(Float, default=0.0)
    daily_fund_profit: Mapped[float] = mapped_column(Float, default=0.0)
    daily_profit_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cumulative_profit: Mapped[float] = mapped_column(Float, default=0.0)
    cumulative_rate: Mapped[float] = mapped_column(Float, default=0.0)
    detail_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
