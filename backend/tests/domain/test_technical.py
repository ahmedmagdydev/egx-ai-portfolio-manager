from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.technical import (
    TechnicalError,
    macd,
    normalize_bars,
    rsi,
    sma,
)


def _bars_from_closes(closes: list[Decimal]) -> list[dict]:
    base = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
    bars: list[dict] = []
    prev = Decimal("0")
    for i, close in enumerate(closes):
        open_price = prev if prev else close
        high = max(open_price, close)
        low = min(open_price, close)
        bars.append(
            {
                "timestamp": (base + timedelta(days=i)).isoformat(),
                "open": str(open_price),
                "high": str(high),
                "low": str(low),
                "close": str(close),
                "volume": 1000,
            }
        )
        prev = close
    return bars


def test_sma() -> None:
    closes = [Decimal(str(v)) for v in range(1, 31)]
    assert sma(closes, 20) == Decimal("20.5000")


def test_sma_insufficient_data() -> None:
    closes = [Decimal("10")] * 19
    assert sma(closes, 20) is None


def test_rsi_flat_series() -> None:
    closes = [Decimal("100")] * 30
    assert rsi(closes) is None


def test_rsi_up_trend() -> None:
    closes = [Decimal("100")] * 15 + [Decimal(str(100 + i)) for i in range(1, 16)]
    value = rsi(closes)
    assert value is not None
    assert Decimal("0") <= value <= Decimal("100")


def test_rsi_down_trend() -> None:
    closes = [Decimal("100")] * 15 + [Decimal(str(100 - i)) for i in range(1, 16)]
    value = rsi(closes)
    assert value is not None
    assert Decimal("0") <= value <= Decimal("100")


def test_macd_flat() -> None:
    closes = [Decimal("100")] * 40
    m, s, h = macd(closes)
    assert m == Decimal("0.0000")
    assert s == Decimal("0.0000")
    assert h == Decimal("0.0000")


def test_macd_insufficient_history() -> None:
    closes = [Decimal("100")] * 25
    assert macd(closes) == (None, None, None)


def test_normalize_bars_sorts_and_validates() -> None:
    bars = [
        {
            "timestamp": "2024-01-02T10:00:00Z",
            "open": "10.0000",
            "high": "11.0000",
            "low": "9.5000",
            "close": "10.5000",
            "volume": 1000,
        },
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "open": "9.0000",
            "high": "10.5000",
            "low": "8.5000",
            "close": "10.0000",
            "volume": 1000,
        },
    ]
    result = normalize_bars(bars, symbol="COMI")
    assert [b.close for b in result] == [Decimal("10.0000"), Decimal("10.5000")]


def test_normalize_bars_rejects_duplicate_timestamp() -> None:
    bars = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "open": "10.0000",
            "high": "11.0000",
            "low": "9.5000",
            "close": "10.5000",
            "volume": 1000,
        },
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "open": "10.0000",
            "high": "11.0000",
            "low": "9.5000",
            "close": "10.5000",
            "volume": 1000,
        },
    ]
    with pytest.raises(TechnicalError):
        normalize_bars(bars, symbol="COMI")


def test_normalize_bars_rejects_invalid_ohlc() -> None:
    bars = [
        {
            "timestamp": "2024-01-01T10:00:00Z",
            "open": "10.0000",
            "high": "9.0000",
            "low": "11.0000",
            "close": "10.5000",
            "volume": 1000,
        }
    ]
    with pytest.raises(TechnicalError):
        normalize_bars(bars, symbol="COMI")
