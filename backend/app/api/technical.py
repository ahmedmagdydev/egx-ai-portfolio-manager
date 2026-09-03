from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db_session import get_session
from ..schemas.technical import TechnicalSnapshotResponse
from ..services.technical import get_technical_snapshot

router = APIRouter(prefix="/api/stocks", tags=["technical"])


@router.get("/{symbol}/technical", response_model=TechnicalSnapshotResponse)
def read_technical_snapshot(
    symbol: str,
    as_of: datetime | None = Query(default=None, description="Snapshot as of ISO-8601 UTC"),
    interval: str = Query(default="1d", description="Interval (only 1d supported)"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> TechnicalSnapshotResponse:
    if as_of is not None and as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    snapshot = get_technical_snapshot(session, settings, symbol, as_of, interval)
    return TechnicalSnapshotResponse(
        symbol=snapshot.symbol,
        interval=snapshot.interval,
        last_timestamp=snapshot.last_timestamp,
        observations=snapshot.observations,
        parameters={
            "sma_periods": [20, 50, 200],
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
        },
        sma_20=snapshot.sma_20,
        sma_50=snapshot.sma_50,
        sma_200=snapshot.sma_200,
        rsi_14=snapshot.rsi_14,
        macd=snapshot.macd,
        macd_signal=snapshot.macd_signal,
        macd_histogram=snapshot.macd_histogram,
        latest_volume=snapshot.latest_volume,
        source="mock",
        freshness=snapshot.freshness,
        warnings=snapshot.warnings,
    )
