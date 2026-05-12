"""定投 / 自动转入计划"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class InvestmentPlan(Base):
    __tablename__ = "investment_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_name: Mapped[str] = mapped_column(String(128), nullable=False)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False)
    from_account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    frequency: Mapped[str] = mapped_column(String(16), nullable=False)
    execute_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    next_execute_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    total_rounds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_rounds: Mapped[int] = mapped_column(Integer, default=0)
    last_execute_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    start_date: Mapped[str] = mapped_column(String(16), nullable=False)
    end_date: Mapped[str | None] = mapped_column(String(16), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
