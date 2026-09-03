from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, Protocol

Freshness = Literal["fresh", "stale", "unavailable", "unknown"]


class ProviderError(Exception):
    """Base class for market-data provider failures."""

    code: str = "PROVIDER_ERROR"


class UnsupportedSymbolError(ProviderError):
    code = "UNSUPPORTED_SYMBOL"


class UpstreamError(ProviderError):
    code = "UPSTREAM_ERROR"


class StaleDataError(ProviderError):
    code = "STALE_DATA"


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: Decimal
    currency: str
    source: str
    market_timestamp: datetime
    fetched_at: datetime
    freshness: Freshness
    status: str = "ok"


@dataclass(frozen=True)
class Bar:
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


@dataclass(frozen=True)
class Volume:
    symbol: str
    timestamp: datetime
    volume: int
    source: str


class MarketDataProvider(Protocol):
    def get_quote(self, symbol: str, *, now: datetime | None = None) -> Quote | None:
        """Return the latest quote for a symbol, or None if the symbol is unsupported."""
        ...

    def get_historical_prices(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[Bar]:
        """Return OHLCV bars for the symbol in the requested range and interval."""
        ...

    def get_volume(self, symbol: str, *, now: datetime | None = None) -> Volume | None:
        """Return the latest volume for a symbol, or None if unavailable."""
        ...
