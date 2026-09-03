from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db_session import get_session
from ..schemas.financial import FinancialSnapshotResponse, MetricValue
from ..services.financial import get_snapshot

router = APIRouter(prefix="/api/stocks", tags=["financials"])


def _metric_response(value, warning):
    return MetricValue(
        value=value,
        status="ok" if value is not None else "not_available",
        warning=warning,
    )


@router.get("/{symbol}/financials/snapshot", response_model=FinancialSnapshotResponse)
def read_financial_snapshot(
    symbol: str,
    as_of: datetime | None = Query(default=None, description="Snapshot as of ISO-8601 UTC"),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> FinancialSnapshotResponse:
    if as_of is not None and as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=UTC)
    snapshot = get_snapshot(session, settings, symbol, as_of)
    return FinancialSnapshotResponse(
        symbol=snapshot.symbol,
        period_end=snapshot.period_end,
        period_type=snapshot.period_type,
        scope=snapshot.scope,
        currency=snapshot.currency,
        unit_scale=snapshot.unit_scale,
        price=snapshot.price,
        price_as_of=snapshot.price_as_of,
        data_as_of=datetime.now(UTC),
        pe=_metric_response(snapshot.pe, None),
        pb=_metric_response(snapshot.pb, None),
        roe=_metric_response(snapshot.roe, None),
        roa=_metric_response(snapshot.roa, None),
        liabilities_to_equity=_metric_response(snapshot.liabilities_to_equity, None),
        profit_margin=_metric_response(snapshot.profit_margin, None),
        revenue_growth=_metric_response(snapshot.revenue_growth, None),
        earnings_growth=_metric_response(snapshot.earnings_growth, None),
        dividend_yield=_metric_response(snapshot.dividend_yield, None),
        sources={
            "statement_source": "mock",
            "price_source": "mock" if snapshot.price is not None else None,
        },
        warnings=snapshot.warnings,
    )
