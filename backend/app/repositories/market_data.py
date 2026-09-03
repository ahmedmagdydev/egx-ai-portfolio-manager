from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Stock, StockPrice
from ..providers.market_data import Bar


def upsert_bars(session: Session, stock: Stock, bars: list[Bar]) -> None:
    """Persist OHLCV bars idempotently, preserving the latest fetch time."""
    if not bars:
        return
    fetched_at = datetime.now(UTC)
    for bar in bars:
        existing = session.scalar(
            select(StockPrice).where(
                StockPrice.stock_id == stock.id,
                StockPrice.source == bar.source,
                StockPrice.timestamp == bar.timestamp,
            )
        )
        if existing is None:
            session.add(
                StockPrice(
                    stock_id=stock.id,
                    timestamp=bar.timestamp,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    currency=bar.currency,
                    source=bar.source,
                    fetched_at=fetched_at,
                )
            )
        else:
            existing.open = bar.open
            existing.high = bar.high
            existing.low = bar.low
            existing.close = bar.close
            existing.volume = bar.volume
            existing.currency = bar.currency
            existing.fetched_at = fetched_at
