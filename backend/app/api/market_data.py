from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db_session import get_session
from ..schemas.market_data import (
    BarResponse,
    HistoryResponse,
    QuoteResponse,
    VolumeResponse,
)
from ..services.market_data import (
    get_historical_prices,
    get_quote,
    get_volume,
)

router = APIRouter(prefix="/api/stocks", tags=["market-data"])


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _bar_response(bar) -> BarResponse:
    return BarResponse(
        symbol=bar.symbol,
        timestamp=bar.timestamp,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        currency=bar.currency,
        source=bar.source,
        fetched_at=bar.fetched_at,
    )


@router.get("/{symbol}/quote", response_model=QuoteResponse)
def read_quote(
    symbol: str,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> QuoteResponse:
    quote = get_quote(session, settings, symbol)
    if quote is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "QUOTE_UNAVAILABLE",
                "message": f"Quote unavailable for {symbol.upper()}",
            },
        )
    return QuoteResponse(
        symbol=quote.symbol,
        price=quote.price,
        currency=quote.currency,
        source=quote.source,
        market_timestamp=quote.market_timestamp,
        fetched_at=quote.fetched_at,
        freshness=quote.freshness,
        status=quote.status,
    )


@router.get("/{symbol}/history", response_model=HistoryResponse)
def read_history(
    symbol: str,
    start: datetime = Query(..., description="History start (ISO-8601 UTC)"),
    end: datetime = Query(..., description="History end (ISO-8601 UTC)"),
    interval: str = Query(default="1d", description="Bar interval"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> HistoryResponse:
    generated_at = _now_utc()
    if start.tzinfo is None:
        start = start.replace(tzinfo=UTC)
    if end.tzinfo is None:
        end = end.replace(tzinfo=UTC)
    if start > end:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "INVALID_RANGE",
                "message": "start must not be after end",
            },
        )
    bars = get_historical_prices(session, settings, symbol, start, end, interval)
    source = bars[0].source if bars else None
    return HistoryResponse(
        symbol=symbol.upper(),
        interval=interval,
        start=start,
        end=end,
        source=source,
        items=[_bar_response(bar) for bar in bars],
        generated_at=generated_at,
    )


@router.get("/{symbol}/volume", response_model=VolumeResponse)
def read_volume(
    symbol: str,
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> VolumeResponse:
    volume = get_volume(session, settings, symbol)
    if volume is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "VOLUME_UNAVAILABLE",
                "message": f"Volume unavailable for {symbol.upper()}",
            },
        )
    return VolumeResponse(
        symbol=volume.symbol,
        timestamp=volume.timestamp,
        volume=volume.volume,
        source=volume.source,
    )
