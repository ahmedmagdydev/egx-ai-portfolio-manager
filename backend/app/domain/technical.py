from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from .money import ZERO, quantize_price


class TechnicalError(Exception):
    pass


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class TechnicalSnapshot:
    symbol: str
    interval: str
    last_timestamp: datetime | None
    observations: int
    sma_20: Decimal | None
    sma_50: Decimal | None
    sma_200: Decimal | None
    rsi_14: Decimal | None
    macd: Decimal | None
    macd_signal: Decimal | None
    macd_histogram: Decimal | None
    latest_volume: int | None
    freshness: str
    warnings: list[str]


def normalize_bars(raw_bars: list[dict], *, symbol: str) -> list[Bar]:
    bars: list[Bar] = []
    seen: set[datetime] = set()
    for raw in raw_bars:
        timestamp = _to_datetime(raw["timestamp"])
        if timestamp in seen:
            raise TechnicalError(f"Duplicate timestamp in series: {timestamp}")
        seen.add(timestamp)
        bar = Bar(
            timestamp=timestamp,
            open=_to_decimal(raw["open"]),
            high=_to_decimal(raw["high"]),
            low=_to_decimal(raw["low"]),
            close=_to_decimal(raw["close"]),
            volume=int(raw["volume"]),
        )
        if not (
            bar.low <= bar.open
            and bar.low <= bar.close
            and bar.high >= bar.open
            and bar.high >= bar.close
        ):
            raise TechnicalError(f"OHLC invariant violated at {timestamp}")
        bars.append(bar)
    bars.sort(key=lambda b: b.timestamp)
    return bars


def _to_datetime(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _to_decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _mean(values: list[Decimal]) -> Decimal:
    return sum(values) / Decimal(len(values))


def sma(closes: list[Decimal], n: int) -> Decimal | None:
    if len(closes) < n:
        return None
    return quantize_price(_mean(closes[-n:]))


def ema_series(closes: list[Decimal], n: int) -> list[Decimal | None]:
    if len(closes) < n:
        return [None] * len(closes)
    alpha = Decimal("2") / Decimal(n + 1)
    seed = _mean(closes[:n])
    result: list[Decimal | None] = [None] * (n - 1) + [seed]
    prev = seed
    for price in closes[n:]:
        value = alpha * price + (Decimal("1") - alpha) * prev
        value = quantize_price(value)
        result.append(value)
        prev = value
    return result


def ema(closes: list[Decimal], n: int) -> Decimal | None:
    series = ema_series(closes, n)
    for value in reversed(series):
        if value is not None:
            return value
    return None


def rsi(closes: list[Decimal], period: int = 14) -> Decimal | None:
    if len(closes) <= period:
        return None
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for prev, curr in zip(closes, closes[1:], strict=False):
        change = curr - prev
        gains.append(max(change, ZERO))
        losses.append(max(-change, ZERO))
    if len(gains) < period:
        return None
    avg_gain = _mean(gains[:period])
    avg_loss = _mean(losses[:period])
    alpha = Decimal("1") / Decimal(period)
    for g, loss in zip(gains[period:], losses[period:], strict=False):
        avg_gain = alpha * g + (Decimal("1") - alpha) * avg_gain
        avg_loss = alpha * loss + (Decimal("1") - alpha) * avg_loss
    if avg_loss == ZERO:
        if avg_gain == ZERO:
            return None
        return Decimal("100")
    rs = avg_gain / avg_loss
    value = Decimal("100") - Decimal("100") / (Decimal("1") + rs)
    return quantize_price(value)


def macd(
    closes: list[Decimal], fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    if len(closes) < slow:
        return None, None, None
    ema_fast = ema_series(closes, fast)
    ema_slow = ema_series(closes, slow)
    macd_line: list[Decimal | None] = []
    for f, s in zip(ema_fast, ema_slow, strict=False):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(quantize_price(f - s))
    signal_line = ema_series([v for v in macd_line if v is not None], signal)  # type: ignore[arg-type]
    macd_last = _last_non_none(macd_line)
    if macd_last is None:
        return None, None, None
    signal_values: list[Decimal | None] = []
    idx = 0
    for value in macd_line:
        if value is None:
            signal_values.append(None)
        else:
            signal_values.append(signal_line[idx] if idx < len(signal_line) else None)
            idx += 1
    signal_last = _last_non_none(signal_values)
    histogram = None
    if macd_last is not None and signal_last is not None:
        histogram = quantize_price(macd_last - signal_last)
    return macd_last, signal_last, histogram


def _last_non_none(values: list[Decimal | None]) -> Decimal | None:
    for value in reversed(values):
        if value is not None:
            return value
    return None
