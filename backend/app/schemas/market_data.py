from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MarketDataSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_encoders={Decimal: str},
    )


class QuoteResponse(MarketDataSchema):
    symbol: str
    price: Decimal
    currency: str
    source: str
    market_timestamp: datetime
    fetched_at: datetime
    freshness: str
    status: str


class BarResponse(MarketDataSchema):
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    currency: str
    source: str
    fetched_at: datetime


class HistoryResponse(MarketDataSchema):
    symbol: str
    interval: str
    start: datetime
    end: datetime
    source: str | None
    items: list[BarResponse]
    generated_at: datetime


class VolumeResponse(MarketDataSchema):
    symbol: str
    timestamp: datetime
    volume: int
    source: str
