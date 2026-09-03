from datetime import UTC, datetime
from decimal import Decimal

import httpx

from ...config import Settings
from ..market_data import Bar, ProviderError, Quote, UnsupportedSymbolError, Volume


class OanorProvider:
    """Real-web adapter for the Oanor EGX/Finance APIs.

    This adapter is opt-in (`MARKET_DATA_PROVIDER=oanor`) and is not declared
    production-ready until the public-source validation spike is accepted.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.oanor_api_key:
            raise ProviderError("OANOR_API_KEY is required for the Oanor market-data provider")
        self._headers = {"x-oanor-key": settings.oanor_api_key}
        self._timeout = httpx.Timeout(10.0, connect=5.0)

    def _client(self) -> httpx.Client:
        return httpx.Client(timeout=self._timeout, headers=self._headers)

    def get_quote(self, symbol: str, *, now: datetime | None = None) -> Quote | None:
        fetched_at = now or datetime.now(UTC)
        url = f"{self.settings.oanor_base_url}/egx-api/v1/quote"
        with self._client() as client:
            response = client.get(url, params={"codes": symbol.upper()})
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            raise ProviderError(f"Oanor API error: {payload.get('message')}")
        quotes = payload.get("data", {}).get("quotes", [])
        for quote in quotes:
            if quote.get("ticker", "").upper() == symbol.upper():
                return Quote(
                    symbol=symbol.upper(),
                    price=Decimal(str(quote["price"])),
                    currency=quote.get("currency", "EGP"),
                    source="oanor/egx-api",
                    market_timestamp=fetched_at,
                    fetched_at=fetched_at,
                    freshness="fresh",
                    status="ok",
                )
        return None

    def get_historical_prices(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[Bar]:
        if interval != "1d":
            raise UnsupportedSymbolError(
                f"Interval {interval} is not supported by the Oanor provider"
            )
        symbol_query = f"{symbol.upper()}{self.settings.oanor_history_symbol_suffix}"
        range_value = _oanor_range(start, end)
        fetched_at = datetime.now(UTC)
        url = f"{self.settings.oanor_base_url}/finance-api/v1/history"
        with self._client() as client:
            response = client.get(
                url,
                params={
                    "symbol": symbol_query,
                    "range": range_value,
                    "interval": "1d",
                },
            )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            raise ProviderError(f"Oanor API error: {payload.get('message')}")
        candles = payload.get("data", {}).get("candles", [])
        bars: list[Bar] = []
        for candle in candles:
            timestamp = datetime.fromisoformat(candle["time"].replace("Z", "+00:00"))
            if start <= timestamp <= end:
                bars.append(
                    Bar(
                        symbol=symbol.upper(),
                        timestamp=timestamp,
                        open=Decimal(str(candle["open"])),
                        high=Decimal(str(candle["high"])),
                        low=Decimal(str(candle["low"])),
                        close=Decimal(str(candle["close"])),
                        volume=int(candle["volume"]),
                        currency="EGP",
                        source="oanor/finance-api",
                        fetched_at=fetched_at,
                    )
                )
        return sorted(bars, key=lambda bar: bar.timestamp)

    def get_volume(self, symbol: str, *, now: datetime | None = None) -> Volume | None:
        fetched_at = now or datetime.now(UTC)
        url = f"{self.settings.oanor_base_url}/egx-api/v1/quote"
        with self._client() as client:
            response = client.get(url, params={"codes": symbol.upper()})
        response.raise_for_status()
        payload = response.json()
        if not payload.get("success"):
            raise ProviderError(f"Oanor API error: {payload.get('message')}")
        for quote in payload.get("data", {}).get("quotes", []):
            if quote.get("ticker", "").upper() == symbol.upper():
                return Volume(
                    symbol=symbol.upper(),
                    timestamp=fetched_at,
                    volume=int(quote["volume"]),
                    source="oanor/egx-api",
                )
        return None


def _oanor_range(start: datetime, end: datetime) -> str:
    """Pick the smallest Oanor Finance `range` value that covers the request."""
    days = (end - start).days + 1
    ranges = [
        (5, "5d"),
        (30, "1mo"),
        (90, "3mo"),
        (180, "6mo"),
        (365, "1y"),
        (365 * 2, "2y"),
        (365 * 5, "5y"),
    ]
    for max_days, value in ranges:
        if days <= max_days:
            return value
    return "max"
