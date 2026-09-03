from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.config import Settings
from app.providers.market.mock import MockMarketDataProvider
from app.providers.market_data import UnsupportedSymbolError


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


def test_mock_provider_get_quote() -> None:
    provider = MockMarketDataProvider(Settings(quote_stale_after_seconds=86400))
    now = datetime(2025, 1, 15, 12, 0, 1, tzinfo=UTC)
    quote = provider.get_quote("COMI", now=now)
    assert quote is not None
    assert quote.symbol == "COMI"
    assert quote.price == 72.5
    assert quote.currency == "EGP"
    assert quote.freshness == "fresh"


def test_mock_provider_get_quote_unavailable() -> None:
    provider = MockMarketDataProvider(Settings(quote_stale_after_seconds=86400))
    assert provider.get_quote("HRHO") is None
    assert provider.get_quote("UNKNOWN") is None


def test_mock_provider_get_historical_prices() -> None:
    provider = MockMarketDataProvider(Settings())
    start = datetime(2025, 1, 13, 0, 0, 0, tzinfo=UTC)
    end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
    bars = provider.get_historical_prices("COMI", start, end, interval="1d")
    assert len(bars) == 3
    assert bars[0].timestamp == datetime(2025, 1, 13, 10, 0, tzinfo=UTC)
    assert bars[-1].close == Decimal("72.9")


def test_mock_provider_rejects_unsupported_interval() -> None:
    provider = MockMarketDataProvider(Settings())
    start = datetime(2025, 1, 13, 0, 0, 0, tzinfo=UTC)
    end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
    with pytest.raises(UnsupportedSymbolError):
        provider.get_historical_prices("COMI", start, end, interval="1w")


def test_mock_provider_get_volume() -> None:
    provider = MockMarketDataProvider(Settings())
    volume = provider.get_volume("COMI")
    assert volume is not None
    assert volume.symbol == "COMI"
    assert volume.volume == 110000
