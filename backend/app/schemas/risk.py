from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RiskLimits(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    max_single_position_percent: Decimal = Field(..., ge=Decimal("0"), le=Decimal("100"))
    max_sector_exposure_percent: Decimal = Field(..., ge=Decimal("0"), le=Decimal("100"))
    min_cash_percent: Decimal = Field(..., ge=Decimal("0"), le=Decimal("100"))
    max_portfolio_volatility_annual: Decimal | None = None
    max_drawdown_percent: Decimal | None = None
    rebalancing_threshold_percent: Decimal = Field(
        default=Decimal("5.0"), ge=Decimal("0"), le=Decimal("100")
    )


class RiskBreach(BaseModel):
    rule: str
    severity: str
    current_value: Decimal
    limit_value: Decimal
    message_en: str
    message_ar: str
    suggested_action_en: str
    suggested_action_ar: str


class RiskReport(BaseModel):
    total_portfolio_value: Decimal
    cash_percent: Decimal
    largest_position_symbol: str
    largest_position_percent: Decimal
    sector_exposure: dict[str, Decimal]
    largest_sector: str
    largest_sector_percent: Decimal
    annualized_volatility: Decimal | None
    max_drawdown: Decimal | None
    beta: Decimal | None
    sharpe_ratio: Decimal | None
    correlation_matrix: dict[str, dict[str, Decimal | None]] | None
    breaches: list[RiskBreach]
    missing_data: list[str]
    missing_data_ar: list[str]
    data_as_of: datetime


class RebalancingSuggestion(BaseModel):
    symbol: str
    action: str
    action_ar: str
    current_percent: Decimal
    target_percent: Decimal
    delta_shares_estimate: int | None
    reason_ar: str
    reason_en: str


class RiskLimitsRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    max_single_position_percent: Decimal
    max_sector_exposure_percent: Decimal
    min_cash_percent: Decimal
    max_portfolio_volatility_annual: Decimal | None
    max_drawdown_percent: Decimal | None
    rebalancing_threshold_percent: Decimal
    updated_at: datetime
