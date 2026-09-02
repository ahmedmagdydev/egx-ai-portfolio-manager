import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from ...config import Settings
from ...domain.portfolio import PriceQuote

FIXTURE_PATH = Path(__file__).with_name("fixtures") / "mock_quotes.json"


class MockMarketDataProvider:
    def __init__(self, settings: Settings, fixture_path: Path = FIXTURE_PATH):
        self.settings = settings
        self.fixture_path = fixture_path

    def get_quotes(
        self,
        symbols: list[str],
        *,
        now: datetime | None = None,
    ) -> dict[str, PriceQuote | None]:
        records = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        current = now or datetime.now(UTC)
        quotes: dict[str, PriceQuote | None] = {}
        for symbol in symbols:
            record = records.get(symbol)
            if record is None or not record.get("available", True):
                quotes[symbol] = None
                continue
            observed_at = datetime.fromisoformat(record["observed_at"].replace("Z", "+00:00"))
            age = (current - observed_at).total_seconds()
            freshness = "fresh" if age <= self.settings.quote_stale_after_seconds else "stale"
            quotes[symbol] = PriceQuote(
                symbol=symbol,
                price=Decimal(record["price"]),
                currency=record.get("currency", "EGP"),
                source=record["source"],
                observed_at=observed_at,
                freshness=freshness,
            )
        return quotes
