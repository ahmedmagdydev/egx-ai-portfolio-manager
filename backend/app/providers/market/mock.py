import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from ...config import Settings
from ...domain.portfolio import PriceQuote
from ..market_data import Bar, Freshness, Quote, UnsupportedSymbolError, Volume

FIXTURE_PATH = Path(__file__).with_name("fixtures") / "mock_quotes.json"


class MockMarketDataProvider:
    def __init__(self, settings: Settings, fixture_path: Path = FIXTURE_PATH):
        self.settings = settings
        self.fixture_path = fixture_path

    def _load(self) -> dict:
        return json.loads(self.fixture_path.read_text(encoding="utf-8"))

    def _freshness(self, observed_at: datetime, now: datetime) -> Freshness:
        age = (now - observed_at).total_seconds()
        return "fresh" if age <= self.settings.quote_stale_after_seconds else "stale"

    def get_quote(self, symbol: str, *, now: datetime | None = None) -> Quote | None:
        records = self._load()
        record = records.get("quotes", {}).get(symbol.upper())
        if record is None or not record.get("available", True):
            return None
        current = now or datetime.now(UTC)
        observed_at = datetime.fromisoformat(record["observed_at"].replace("Z", "+00:00"))
        return Quote(
            symbol=symbol.upper(),
            price=Decimal(record["price"]),
            currency=record.get("currency", "EGP"),
            source=record["source"],
            market_timestamp=observed_at,
            fetched_at=current,
            freshness=self._freshness(observed_at, current),
        )

    def get_quotes(
        self,
        symbols: list[str],
        *,
        now: datetime | None = None,
    ) -> dict[str, PriceQuote | None]:
        records = self._load()
        current = now or datetime.now(UTC)
        quotes: dict[str, PriceQuote | None] = {}
        for symbol in symbols:
            record = records.get("quotes", {}).get(symbol)
            if record is None or not record.get("available", True):
                quotes[symbol] = None
                continue
            observed_at = datetime.fromisoformat(record["observed_at"].replace("Z", "+00:00"))
            freshness = self._freshness(observed_at, current)
            quotes[symbol] = PriceQuote(
                symbol=symbol,
                price=Decimal(record["price"]),
                currency=record.get("currency", "EGP"),
                source=record["source"],
                observed_at=observed_at,
                freshness=freshness,
            )
        return quotes

    def get_historical_prices(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
    ) -> list[Bar]:
        if interval != "1d":
            raise UnsupportedSymbolError(
                f"Interval {interval} is not supported by the mock provider"
            )
        records = self._load()
        current = datetime.now(UTC)

        def _collect(source: list[dict]) -> list[Bar]:
            out: list[Bar] = []
            for raw in source:
                timestamp = datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
                if start <= timestamp <= end:
                    out.append(
                        Bar(
                            symbol=symbol.upper(),
                            timestamp=timestamp,
                            open=Decimal(raw["open"]),
                            high=Decimal(raw["high"]),
                            low=Decimal(raw["low"]),
                            close=Decimal(raw["close"]),
                            volume=int(raw["volume"]),
                            currency=raw.get("currency", "EGP"),
                            source=raw.get("source", "mock"),
                            fetched_at=current,
                        )
                    )
            return out

        history = records.get("history", {}).get(symbol.upper(), [])
        result = _collect(history)
        if not result:
            result = _collect(records.get("bars", {}).get(symbol.upper(), []))
        return sorted(result, key=lambda bar: bar.timestamp)

    def get_volume(self, symbol: str, *, now: datetime | None = None) -> Volume | None:
        records = self._load()
        bars = records.get("bars", {}).get(symbol.upper(), [])
        if not bars:
            return None
        latest = max(bars, key=lambda raw: raw["timestamp"])
        timestamp = datetime.fromisoformat(latest["timestamp"].replace("Z", "+00:00"))
        return Volume(
            symbol=symbol.upper(),
            timestamp=timestamp,
            volume=int(latest["volume"]),
            source=latest.get("source", "mock"),
        )
