from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.providers.market.oanor import OanorProvider
from app.providers.market_data import ProviderError, UnsupportedSymbolError


@pytest.fixture
def settings() -> Settings:
    return Settings(
        market_data_provider="oanor",
        oanor_api_key="test_key",
        oanor_base_url="https://api.oanor.com",
        oanor_history_symbol_suffix=".CA",
    )


def _mock_response(json_data: dict | None = None, status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.raise_for_status.return_value = None
    return response


def _mock_client(response: MagicMock) -> MagicMock:
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=None)
    client.get.return_value = response
    return client


def test_provider_requires_api_key() -> None:
    settings = Settings(market_data_provider="oanor", oanor_api_key=None)
    with pytest.raises(ProviderError):
        OanorProvider(settings)


def test_get_quote(settings: Settings) -> None:
    response = _mock_response(
        {
            "success": True,
            "data": {
                "quotes": [
                    {
                        "ticker": "COMI",
                        "price": 134.76,
                        "currency": "EGP",
                        "volume": 4254137,
                    }
                ]
            },
        }
    )
    with patch("app.providers.market.oanor.httpx.Client") as mock_client_class:
        mock_client_class.return_value = _mock_client(response)
        provider = OanorProvider(settings)
        quote = provider.get_quote("COMI")
    assert quote is not None
    assert quote.symbol == "COMI"
    assert quote.price == Decimal("134.76")
    assert quote.currency == "EGP"
    assert quote.source == "oanor/egx-api"


def test_get_quote_missing_symbol_returns_none(settings: Settings) -> None:
    response = _mock_response(
        {
            "success": True,
            "data": {"quotes": [{"ticker": "TMGH", "price": 95.68, "currency": "EGP"}]},
        }
    )
    with patch("app.providers.market.oanor.httpx.Client") as mock_client_class:
        mock_client_class.return_value = _mock_client(response)
        provider = OanorProvider(settings)
        assert provider.get_quote("COMI") is None


def test_get_quote_api_error_raises(settings: Settings) -> None:
    response = _mock_response({"success": False, "message": "invalid key"}, status_code=401)
    with patch("app.providers.market.oanor.httpx.Client") as mock_client_class:
        mock_client_class.return_value = _mock_client(response)
        provider = OanorProvider(settings)
        with pytest.raises(ProviderError):
            provider.get_quote("COMI")


def test_get_historical_prices(settings: Settings) -> None:
    start = datetime(2025, 1, 13, 0, 0, 0, tzinfo=UTC)
    end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
    response = _mock_response(
        {
            "success": True,
            "data": {
                "candles": [
                    {
                        "time": "2025-01-13T10:00:00.000Z",
                        "open": 71.0,
                        "high": 72.9,
                        "low": 70.8,
                        "close": 72.5,
                        "volume": 125000,
                    },
                    {
                        "time": "2025-01-16T10:00:00.000Z",
                        "open": 73.0,
                        "high": 73.5,
                        "low": 72.9,
                        "close": 73.2,
                        "volume": 100000,
                    },
                ]
            },
        }
    )
    with patch("app.providers.market.oanor.httpx.Client") as mock_client_class:
        mock_client_class.return_value = _mock_client(response)
        provider = OanorProvider(settings)
        bars = provider.get_historical_prices("COMI", start, end, interval="1d")
    assert len(bars) == 1
    assert bars[0].symbol == "COMI"
    assert bars[0].close == Decimal("72.5")
    assert bars[0].volume == 125000


def test_get_historical_prices_unsupported_interval(settings: Settings) -> None:
    start = datetime(2025, 1, 13, 0, 0, 0, tzinfo=UTC)
    end = datetime(2025, 1, 15, 23, 59, 59, tzinfo=UTC)
    provider = OanorProvider(settings)
    with pytest.raises(UnsupportedSymbolError):
        provider.get_historical_prices("COMI", start, end, interval="1w")


def test_get_volume(settings: Settings) -> None:
    response = _mock_response(
        {
            "success": True,
            "data": {
                "quotes": [
                    {
                        "ticker": "COMI",
                        "price": 134.76,
                        "currency": "EGP",
                        "volume": 4254137,
                    }
                ]
            },
        }
    )
    with patch("app.providers.market.oanor.httpx.Client") as mock_client_class:
        mock_client_class.return_value = _mock_client(response)
        provider = OanorProvider(settings)
        volume = provider.get_volume("COMI")
    assert volume is not None
    assert volume.symbol == "COMI"
    assert volume.volume == 4254137
    assert volume.source == "oanor/egx-api"


def test_oanor_range_mapping() -> None:
    from app.providers.market.oanor import _oanor_range

    start = datetime(2025, 1, 1, tzinfo=UTC)
    assert _oanor_range(start, start) == "5d"
    assert _oanor_range(start, start + timedelta(days=20)) == "1mo"
