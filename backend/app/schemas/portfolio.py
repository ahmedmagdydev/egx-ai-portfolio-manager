from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models import TransactionType


class PortfolioSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_encoders={Decimal: str},
    )


class StockCreate(PortfolioSchema):
    symbol: str
    name_en: str
    name_ar: str | None = None
    sector: str | None = None


class StockResponse(PortfolioSchema):
    id: UUID
    symbol: str
    name_en: str
    name_ar: str | None
    sector: str | None
    is_active: bool
    created_at: datetime
    currency: str = "EGP"
    generated_at: datetime


class TransactionCreate(PortfolioSchema):
    type: TransactionType
    symbol: str | None = None
    quantity: Decimal | None = None
    price: Decimal | None = None
    fees: Decimal = Decimal("0")
    amount: Decimal | None = None
    executed_at: datetime
    note: str | None = None


class TransactionResponse(PortfolioSchema):
    id: UUID
    stock_id: UUID | None
    type: TransactionType
    symbol: str | None
    quantity: Decimal | None
    price: Decimal | None
    fees: Decimal
    amount: Decimal | None
    executed_at: datetime
    sequence: int
    note: str | None
    created_at: datetime
    currency: str = "EGP"
    generated_at: datetime


class TransactionPage(PortfolioSchema):
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
    currency: str = "EGP"
    generated_at: datetime


class PriceResponse(PortfolioSchema):
    value: Decimal | None
    source: str | None
    observed_at: datetime | None
    freshness: str | None
    status: str


class HoldingResponse(PortfolioSchema):
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    total_cost: Decimal
    market_value: Decimal | None
    unrealized_pnl: Decimal | None
    unrealized_pnl_pct: Decimal | None
    realized_pnl: Decimal
    price: PriceResponse


class SummaryResponse(PortfolioSchema):
    total_market_value: Decimal
    total_cost: Decimal
    cash: Decimal
    total_value: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    data_as_of: datetime | None
    unpriced_count: int


class HoldingsResponse(PortfolioSchema):
    holdings: list[HoldingResponse]
    summary: SummaryResponse
    data_as_of: datetime | None
    currency: str = "EGP"
    generated_at: datetime


class AllocationLineResponse(PortfolioSchema):
    name: str
    value: Decimal
    weight: Decimal


class AllocationResponse(PortfolioSchema):
    by_symbol: list[AllocationLineResponse]
    by_sector: list[AllocationLineResponse]
    cash: AllocationLineResponse
    unpriced_symbols: list[str]
    currency: str = "EGP"
    generated_at: datetime


class CashResponse(PortfolioSchema):
    cash: Decimal
    currency: str = "EGP"
    generated_at: datetime


class ErrorResponse(PortfolioSchema):
    code: str
    message: str
    details: dict[str, Any] | None = None
