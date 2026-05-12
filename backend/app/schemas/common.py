"""Pydantic 请求/响应模型"""
import math
from datetime import date
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any


def _sanitize_nan(v: Any) -> Any:
    """递归清除 NaN，替换为 0.0"""
    if isinstance(v, float) and math.isnan(v):
        return 0.0
    if isinstance(v, list):
        return [_sanitize_nan(i) for i in v]
    if isinstance(v, dict):
        return {k: _sanitize_nan(vv) for k, vv in v.items()}
    return v


class NanSafeModel(BaseModel):
    """所有输出模型基类：自动清除 NaN"""

    @model_validator(mode="after")
    def _replace_nan(cls, model):
        for field_name, value in model.__dict__.items():
            if isinstance(value, float) and math.isnan(value):
                object.__setattr__(model, field_name, 0.0)
            elif isinstance(value, list):
                sanitized = [
                    _sanitize_nan(item) if not isinstance(item, BaseModel) else item
                    for item in value
                ]
                object.__setattr__(model, field_name, sanitized)
        return model


# ----------------------------------------------------------------
# 储蓄账户
# ----------------------------------------------------------------

class SavingsAccountCreate(BaseModel):
    account_type: str = Field("bank", description="bank / fund")
    label: str = Field(..., min_length=1, max_length=64, description="账户标识")
    bank_name: Optional[str] = Field(None, max_length=64)
    balance: float = Field(0.0, ge=0, description="初始余额/市值")
    pending_amount: float = Field(0.0, ge=0, description="待确认金额")
    currency: str = Field("CNY", max_length=8)
    fund_code: Optional[str] = Field(None, min_length=6, max_length=6, description="基金代码(fund类型)")
    sort_order: int = 0
    remark: Optional[str] = None


class SavingsAccountUpdate(BaseModel):
    account_type: Optional[str] = None
    label: Optional[str] = None
    bank_name: Optional[str] = None
    balance: Optional[float] = None
    pending_amount: Optional[float] = None
    currency: Optional[str] = None
    fund_code: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[int] = None
    remark: Optional[str] = None


class SavingsAccountOut(NanSafeModel):
    id: int
    account_type: str
    label: str
    bank_name: Optional[str]
    balance: float
    pending_amount: float
    currency: str
    fund_code: Optional[str]
    sort_order: int
    is_active: int
    remark: Optional[str]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ----------------------------------------------------------------
# 基金
# ----------------------------------------------------------------

class FundCreate(BaseModel):
    code: str = Field(..., min_length=6, max_length=6, description="基金代码")
    settle_cycle: str = Field("T+1")
    redeem_cycle: str = Field("T+3")


class FundUpdate(BaseModel):
    fund_type: Optional[str] = None
    settle_cycle: Optional[str] = None
    redeem_cycle: Optional[str] = None
    is_active: Optional[int] = None


class FundOut(NanSafeModel):
    id: int
    code: str
    name: Optional[str]
    full_name: Optional[str]
    fund_type: Optional[str]
    settle_cycle: str
    redeem_cycle: str
    nav: Optional[float]
    nav_date: Optional[str]
    acc_nav: Optional[float]
    daily_change: float
    estimate_nav: Optional[float]
    estimate_time: Optional[str]
    is_active: int
    last_sync_at: Optional[str]

    model_config = {"from_attributes": True}


# ----------------------------------------------------------------
# 持仓
# ----------------------------------------------------------------

class FundHoldingOut(NanSafeModel):
    id: int
    fund_code: str
    fund_name: Optional[str]
    total_shares: float
    available_shares: float
    frozen_shares: float
    avg_cost_nav: Optional[float]
    total_cost: float
    current_value: float
    total_profit: float
    profit_rate: float
    daily_profit: float
    daily_profit_rate: float
    hold_days: int
    source_account_id: Optional[int]
    status: str
    first_buy_date: Optional[str]
    last_update: Optional[str]

    model_config = {"from_attributes": True}


# ----------------------------------------------------------------
# 交易记录
# ----------------------------------------------------------------

class TransactionCreate(BaseModel):
    trans_type: str = Field(..., description="buy / sell / dividend / split")
    fund_code: str
    amount: float = Field(..., gt=0)
    nav: Optional[float] = None
    fee: float = 0.0
    order_date: str = Field(..., description="YYYY-MM-DD")
    source_account_id: Optional[int] = None
    remark: Optional[str] = None


class TransactionOut(NanSafeModel):
    id: int
    trans_type: str
    fund_code: str
    fund_name: Optional[str]
    amount: float
    nav: Optional[float]
    shares: Optional[float]
    fee: float
    actual_amount: Optional[float]
    order_date: str
    confirm_date: Optional[str]
    settle_date: Optional[str]
    source_account_id: Optional[int]
    target_holding_id: Optional[int]
    plan_id: Optional[int]
    status: str
    confirm_shares: Optional[float]
    remark: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


# ----------------------------------------------------------------
# 定投计划
# ----------------------------------------------------------------

class InvestmentPlanCreate(BaseModel):
    plan_name: str = Field(..., min_length=1, max_length=128)
    fund_code: str = Field(..., min_length=6, max_length=6)
    from_account_id: int
    amount: float = Field(..., gt=0)
    frequency: str = Field(..., description="daily / weekly / biweekly / monthly")
    execute_day: Optional[int] = Field(None, ge=1, le=28)
    total_rounds: Optional[int] = Field(None, ge=1)
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: Optional[str] = None
    remark: Optional[str] = None


class InvestmentPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    amount: Optional[float] = None
    frequency: Optional[str] = None
    execute_day: Optional[int] = None
    status: Optional[str] = None
    total_rounds: Optional[int] = None
    remark: Optional[str] = None


class InvestmentPlanOut(NanSafeModel):
    id: int
    plan_name: str
    fund_code: str
    from_account_id: int
    amount: float
    frequency: str
    execute_day: Optional[int]
    next_execute_date: Optional[str]
    status: str
    total_rounds: Optional[int]
    completed_rounds: int
    last_execute_date: Optional[str]
    start_date: str
    end_date: Optional[str]
    remark: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


# ----------------------------------------------------------------
# 快照 & 看板
# ----------------------------------------------------------------

class SnapshotOut(NanSafeModel):
    id: int
    snapshot_date: str
    is_trade_day: int
    total_savings: float
    total_fund_value: float
    total_assets: float
    daily_fund_profit: float
    daily_profit_rate: float
    cumulative_profit: float
    cumulative_rate: float
    detail_json: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}


class DashboardOut(NanSafeModel):
    total_savings: float
    total_fund_value: float
    total_assets: float
    total_pending: float
    daily_profit: float
    daily_profit_rate: float
    cumulative_profit: float
    cumulative_rate: float
    holding_count: int
    holdings: list[FundHoldingOut]
    accounts: list[SavingsAccountOut]


# ----------------------------------------------------------------
# 通用
# ----------------------------------------------------------------

class MessageOut(BaseModel):
    message: str
