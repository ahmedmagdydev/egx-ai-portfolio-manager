from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FinancialSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_encoders={Decimal: str},
    )


class FinancialStatementCreate(FinancialSchema):
    period_start: datetime | None = None
    period_end: datetime
    period_type: str
    scope: str
    currency: str = "EGP"
    unit_scale: str = "units"
    revenue: Decimal | None = None
    gross_profit: Decimal | None = None
    operating_profit: Decimal | None = None
    net_income: Decimal | None = None
    eps: Decimal | None = None
    assets: Decimal | None = None
    liabilities: Decimal | None = None
    equity: Decimal | None = None
    cash: Decimal | None = None
    operating_cash_flow: Decimal | None = None
    investing_cash_flow: Decimal | None = None
    financing_cash_flow: Decimal | None = None
    shares_outstanding: Decimal | None = None
    dividends_per_share: Decimal | None = None
    source: str
    source_url: str | None = None
    published_at: datetime
    version: int = 0


class FinancialStatementResponse(FinancialSchema):
    id: UUID
    stock_id: UUID
    period_start: datetime | None
    period_end: datetime
    period_type: str
    scope: str
    currency: str
    unit_scale: str
    revenue: Decimal | None
    gross_profit: Decimal | None
    operating_profit: Decimal | None
    net_income: Decimal | None
    eps: Decimal | None
    assets: Decimal | None
    liabilities: Decimal | None
    equity: Decimal | None
    cash: Decimal | None
    operating_cash_flow: Decimal | None
    investing_cash_flow: Decimal | None
    financing_cash_flow: Decimal | None
    shares_outstanding: Decimal | None
    dividends_per_share: Decimal | None
    source: str
    source_url: str | None
    published_at: datetime
    fetched_at: datetime
    version: int
    created_at: datetime


class MetricValue(FinancialSchema):
    value: Decimal | None
    status: str
    warning: str | None = None


class FinancialSnapshotResponse(FinancialSchema):
    symbol: str
    period_end: datetime
    period_type: str
    scope: str
    currency: str
    unit_scale: str
    price: Decimal | None
    price_as_of: datetime | None
    data_as_of: datetime
    pe: MetricValue
    pb: MetricValue
    roe: MetricValue
    roa: MetricValue
    liabilities_to_equity: MetricValue
    profit_margin: MetricValue
    revenue_growth: MetricValue
    earnings_growth: MetricValue
    dividend_yield: MetricValue
    sources: dict[str, Any]
    warnings: list[str]
