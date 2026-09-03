from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..domain.portfolio import (
    AllocationReport,
    PriceQuote,
    compute_allocation,
    compute_cash,
    compute_holdings,
    value_holdings,
)
from ..models import Stock
from ..repositories.documents import get_documents
from ..services.financial import get_snapshot as get_financial_snapshot
from ..services.market_data import get_historical_prices, get_quote
from ..services.portfolio_service import current_events
from ..services.rag import search_documents
from ..services.technical import get_technical_snapshot


def _stock_not_found(symbol: str) -> dict:
    return {
        "error": "UNKNOWN_STOCK",
        "message": f"Stock {symbol} not found",
        "symbol": symbol.upper(),
    }


def _http_error(exc: HTTPException, symbol: str) -> dict:
    detail = exc.detail
    code = detail.get("code", "UNKNOWN") if isinstance(detail, dict) else "UNKNOWN"
    message = str(detail)
    return {"error": code, "message": message, "symbol": symbol.upper()}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _build_allocation(session: Session, settings: Settings) -> AllocationReport:
    events = current_events(session)
    holdings = compute_holdings(events)
    cash = compute_cash(events)
    symbols = list(holdings.keys())
    stocks = {
        stock.symbol: stock
        for stock in session.scalars(select(Stock).where(Stock.symbol.in_(symbols))).all()
    }
    raw_quotes = {symbol: get_quote(session, settings, symbol) for symbol in symbols}
    quotes: dict[str, PriceQuote | None] = {
        symbol: PriceQuote(
            symbol=q.symbol,
            price=q.price,
            currency=q.currency,
            source=q.source,
            observed_at=q.market_timestamp,
            freshness=q.freshness,
        )
        if q is not None
        else None
        for symbol, q in raw_quotes.items()
    }
    sectors = {symbol: stock.sector for symbol, stock in stocks.items()}
    valuations = value_holdings(holdings, quotes, sectors)
    return compute_allocation(valuations, cash)


def get_portfolio(session: Session, settings: Settings) -> dict:
    events = current_events(session)
    holdings = compute_holdings(events)
    allocation = _build_allocation(session, settings)
    return {
        "holdings_count": len(holdings),
        "allocation_by_symbol": [
            {"symbol": line.name, "weight": float(line.weight), "value": str(line.value)}
            for line in allocation.by_symbol
        ],
        "cash": str(allocation.cash.value),
        "source": "portfolio",
        "as_of": _now(),
    }


def get_position(session: Session, settings: Settings, symbol: str) -> dict:
    stock = session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if stock is None:
        return _stock_not_found(symbol)
    events = [
        event for event in current_events(session) if event.symbol == symbol.upper()
    ]
    holdings = compute_holdings(events)
    state = holdings.get(symbol.upper())
    return {
        "symbol": symbol.upper(),
        "quantity": str(state.quantity) if state else "0",
        "source": "portfolio",
        "as_of": _now(),
    }


def get_quote_adapter(session: Session, settings: Settings, symbol: str) -> dict:
    try:
        quote = get_quote(session, settings, symbol)
    except HTTPException as exc:
        return _http_error(exc, symbol)
    if quote is None:
        return {
            "error": "QUOTE_UNAVAILABLE",
            "message": f"No quote for {symbol}",
            "symbol": symbol.upper(),
        }
    return {
        "symbol": quote.symbol,
        "price": str(quote.price),
        "currency": quote.currency,
        "freshness": quote.freshness,
        "source": quote.source,
        "as_of": quote.market_timestamp.isoformat(),
    }


def get_historical_prices_adapter(
    session: Session, settings: Settings, symbol: str, days: int
) -> dict:
    end = datetime.now(UTC)
    start = end - timedelta(days=days)
    try:
        bars = get_historical_prices(session, settings, symbol, start, end)
    except HTTPException as exc:
        return _http_error(exc, symbol)
    source = settings.market_data_provider
    return {
        "symbol": symbol.upper(),
        "count": len(bars),
        "first": bars[0].timestamp.isoformat() if bars else None,
        "last": bars[-1].timestamp.isoformat() if bars else None,
        "source": source,
        "as_of": end.isoformat(),
    }


def get_financial_snapshot_adapter(
    session: Session, settings: Settings, symbol: str, as_of: datetime | None
) -> dict:
    try:
        snapshot = get_financial_snapshot(session, settings, symbol, as_of)
    except HTTPException as exc:
        return _http_error(exc, symbol)
    return {
        "symbol": snapshot.symbol,
        "pe_ratio": str(snapshot.pe) if snapshot.pe is not None else None,
        "pb_ratio": str(snapshot.pb) if snapshot.pb is not None else None,
        "roe": str(snapshot.roe) if snapshot.roe is not None else None,
        "source": "mock",
        "freshness": "fresh" if snapshot.price is not None else "stale",
        "warnings": snapshot.warnings,
        "as_of": snapshot.period_end.isoformat() if snapshot.period_end else None,
    }


def get_technical_indicators_adapter(session: Session, settings: Settings, symbol: str) -> dict:
    try:
        snapshot = get_technical_snapshot(session, settings, symbol)
    except HTTPException as exc:
        return _http_error(exc, symbol)
    return {
        "symbol": snapshot.symbol,
        "observations": snapshot.observations,
        "sma_20": str(snapshot.sma_20) if snapshot.sma_20 is not None else None,
        "sma_50": str(snapshot.sma_50) if snapshot.sma_50 is not None else None,
        "sma_200": str(snapshot.sma_200) if snapshot.sma_200 is not None else None,
        "rsi_14": str(snapshot.rsi_14) if snapshot.rsi_14 is not None else None,
        "macd": str(snapshot.macd) if snapshot.macd is not None else None,
        "source": "mock",
        "freshness": snapshot.freshness,
        "warnings": snapshot.warnings,
        "as_of": snapshot.last_timestamp.isoformat() if snapshot.last_timestamp else None,
    }


def search_documents_adapter(
    session: Session,
    settings: Settings,
    query: str,
    symbol: str | None,
    document_type: str | None,
    as_of: datetime | None,
    top_k: int,
) -> dict:
    results = search_documents(
        session,
        settings,
        query=query,
        symbol=symbol,
        document_type=document_type,
        as_of=as_of,
        top_k=top_k,
    )
    return {
        "query": query,
        "count": len(results),
        "results": results,
        "source": "rag",
        "as_of": _now(),
    }


def get_latest_news_adapter(
    session: Session, settings: Settings, symbol: str | None, limit: int
) -> dict:
    documents = get_documents(
        session,
        symbol=symbol,
        document_type="NEWS",
        language=None,
        as_of=None,
    )
    items = [
        {
            "id": str(doc.id),
            "symbol": doc.symbol,
            "title": doc.title,
            "published_at": doc.published_at.isoformat() if doc.published_at else None,
            "source": doc.source,
            "source_url": doc.source_url,
        }
        for doc in documents[:limit]
    ]
    return {
        "symbol": symbol,
        "count": len(items),
        "items": items,
        "source": "documents",
        "as_of": _now(),
    }


def calculate_portfolio_allocation_adapter(session: Session, settings: Settings) -> dict:
    allocation = _build_allocation(session, settings)
    return {
        "by_symbol": [
            {"symbol": line.name, "weight": float(line.weight), "value": str(line.value)}
            for line in allocation.by_symbol
        ],
        "total_weight": str(sum(line.weight for line in allocation.by_symbol)),
        "source": "portfolio",
        "as_of": _now(),
    }


def calculate_sector_allocation_adapter(session: Session, settings: Settings) -> dict:
    allocation = _build_allocation(session, settings)
    return {
        "by_sector": [
            {"sector": line.name, "weight": float(line.weight), "value": str(line.value)}
            for line in allocation.by_sector
        ],
        "source": "portfolio",
        "as_of": _now(),
    }
