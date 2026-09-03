from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..config import Settings
from ..domain.technical import (
    Bar,
    TechnicalSnapshot,
    macd,
    rsi,
    sma,
)
from ..models import Stock
from ..services.market_data import get_historical_prices


class TechnicalServiceError(Exception):
    pass


def _load_stock(session: Session, symbol: str) -> Stock:
    from sqlalchemy import select

    stock = session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if stock is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "UNKNOWN_STOCK", "message": f"Unknown stock: {symbol}"},
        )
    return stock


def get_technical_snapshot(
    session: Session,
    settings: Settings,
    symbol: str,
    as_of: datetime | None = None,
    interval: str = "1d",
) -> TechnicalSnapshot:
    if interval != "1d":
        raise HTTPException(
            status_code=422,
            detail={
                "code": "UNSUPPORTED_INTERVAL",
                "message": f"Interval {interval} is not supported",
            },
        )
    end = as_of or datetime.now(UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    start = end - timedelta(days=1500)
    _load_stock(session, symbol)
    bars_data = get_historical_prices(session, settings, symbol, start, end, interval)
    warnings: list[str] = []
    freshness = "fresh"
    if not bars_data:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "HISTORY_UNAVAILABLE",
                "message": f"No historical data available for {symbol.upper()}",
            },
        )
    bars = [
        Bar(
            timestamp=b.timestamp,
            open=b.open,
            high=b.high,
            low=b.low,
            close=b.close,
            volume=b.volume,
        )
        for b in bars_data
    ]
    closes = [bar.close for bar in bars]
    if not bars:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "HISTORY_UNAVAILABLE",
                "message": f"No historical data available for {symbol.upper()}",
            },
        )
    if bars[-1].timestamp < end - timedelta(days=30):
        warnings.append("History is stale; indicators may not reflect current prices")
        freshness = "stale"
    sma_20 = sma(closes, 20)
    sma_50 = sma(closes, 50)
    sma_200 = sma(closes, 200)
    if sma_200 is None:
        warnings.append("Insufficient history for SMA 200")
    if sma_50 is None:
        warnings.append("Insufficient history for SMA 50")
    rsi_14 = rsi(closes)
    if rsi_14 is None:
        warnings.append("Insufficient history for RSI 14")
    macd_value, signal_value, histogram = macd(closes)
    if macd_value is None:
        warnings.append("Insufficient history for MACD")
    return TechnicalSnapshot(
        symbol=symbol.upper(),
        interval=interval,
        last_timestamp=bars[-1].timestamp,
        observations=len(bars),
        sma_20=sma_20,
        sma_50=sma_50,
        sma_200=sma_200,
        rsi_14=rsi_14,
        macd=macd_value,
        macd_signal=signal_value,
        macd_histogram=histogram,
        latest_volume=bars[-1].volume,
        freshness=freshness,
        warnings=warnings,
    )
