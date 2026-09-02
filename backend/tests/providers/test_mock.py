from datetime import UTC, datetime

from app.config import Settings
from app.providers.market.mock import MockMarketDataProvider


def test_mock_provider_freshness_and_unavailable() -> None:
    provider = MockMarketDataProvider(Settings(quote_stale_after_seconds=86400))
    now = datetime(2025, 1, 15, 12, 0, 1, tzinfo=UTC)
    quotes = provider.get_quotes(["COMI", "HRHO", "UNKNOWN"], now=now)
    assert quotes["COMI"] is not None
    assert quotes["COMI"].freshness == "fresh"
    assert quotes["HRHO"] is None
    assert quotes["UNKNOWN"] is None


def test_mock_provider_marks_old_quote_stale() -> None:
    provider = MockMarketDataProvider(Settings(quote_stale_after_seconds=1))
    now = datetime(2025, 1, 15, 12, 0, 2, tzinfo=UTC)
    quote = provider.get_quotes(["COMI"], now=now)["COMI"]
    assert quote is not None
    assert quote.freshness == "stale"
