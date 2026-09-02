from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ...domain.portfolio import PriceQuote
from ...models import Freshness, PriceSnapshot, Stock


def upsert_quotes(
    session: Session,
    stocks: dict[str, Stock],
    quotes: dict[str, PriceQuote | None],
) -> None:
    fetched_at = datetime.now(UTC)
    for symbol, quote in quotes.items():
        stock = stocks.get(symbol)
        if stock is None or quote is None:
            continue
        existing = session.scalar(
            select(PriceSnapshot).where(
                PriceSnapshot.stock_id == stock.id,
                PriceSnapshot.source == quote.source,
                PriceSnapshot.observed_at == quote.observed_at,
            )
        )
        if existing is None:
            session.add(
                PriceSnapshot(
                    stock_id=stock.id,
                    price=quote.price,
                    currency=quote.currency,
                    source=quote.source,
                    observed_at=quote.observed_at,
                    fetched_at=fetched_at,
                    freshness=Freshness(quote.freshness),
                )
            )
        else:
            existing.price = quote.price
            existing.currency = quote.currency
            existing.fetched_at = fetched_at
            existing.freshness = Freshness(quote.freshness)
