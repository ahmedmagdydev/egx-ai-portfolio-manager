from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import FinancialStatement, Stock, UnitScale


def _parse_datetime(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def upsert_statement(session: Session, stock: Stock, data: dict) -> FinancialStatement:
    """Persist or update a financial statement keyed by stock/period/scope/source/version."""
    fetched_at = datetime.now(UTC)
    period_start = _parse_datetime(data.get("period_start"))
    period_end = _parse_datetime(data["period_end"])
    published_at = _parse_datetime(data["published_at"])
    existing = session.scalar(
        select(FinancialStatement).where(
            FinancialStatement.stock_id == stock.id,
            FinancialStatement.period_end == period_end,
            FinancialStatement.period_type == data["period_type"],
            FinancialStatement.scope == data["scope"],
            FinancialStatement.source == data["source"],
            FinancialStatement.version == data.get("version", 0),
        )
    )
    if existing is not None:
        for key, value in data.items():
            if key == "period_type":
                continue
            if key == "scope":
                continue
            if key == "unit_scale":
                continue
            setattr(existing, key, value)
        existing.fetched_at = fetched_at
        return existing

    statement = FinancialStatement(
        stock_id=stock.id,
        period_start=period_start,
        period_end=period_end,
        period_type=data["period_type"],
        scope=data["scope"],
        currency=data.get("currency", "EGP"),
        unit_scale=data.get("unit_scale", UnitScale.UNITS),
        revenue=data.get("revenue"),
        gross_profit=data.get("gross_profit"),
        operating_profit=data.get("operating_profit"),
        net_income=data.get("net_income"),
        eps=data.get("eps"),
        assets=data.get("assets"),
        liabilities=data.get("liabilities"),
        equity=data.get("equity"),
        cash=data.get("cash"),
        operating_cash_flow=data.get("operating_cash_flow"),
        investing_cash_flow=data.get("investing_cash_flow"),
        financing_cash_flow=data.get("financing_cash_flow"),
        shares_outstanding=data.get("shares_outstanding"),
        dividends_per_share=data.get("dividends_per_share"),
        source=data["source"],
        source_url=data.get("source_url"),
        published_at=published_at,
        fetched_at=fetched_at,
        version=data.get("version", 0),
    )
    session.add(statement)
    return statement


def get_latest_statement(
    session: Session,
    stock: Stock,
    period_type: str,
    scope: str,
    as_of: datetime | None = None,
) -> FinancialStatement | None:
    statement = select(FinancialStatement).where(
        FinancialStatement.stock_id == stock.id,
        FinancialStatement.period_type == period_type,
        FinancialStatement.scope == scope,
    )
    if as_of is not None:
        statement = statement.where(FinancialStatement.published_at <= as_of)
    statement = statement.order_by(
        FinancialStatement.period_end.desc(),
        FinancialStatement.published_at.desc(),
    )
    return session.scalars(statement).first()


def get_prior_statement(
    session: Session,
    stock: Stock,
    period_end: datetime,
    period_type: str,
    scope: str,
) -> FinancialStatement | None:
    statement = (
        select(FinancialStatement)
        .where(
            FinancialStatement.stock_id == stock.id,
            FinancialStatement.period_type == period_type,
            FinancialStatement.scope == scope,
            FinancialStatement.period_end < period_end,
        )
        .order_by(FinancialStatement.period_end.desc())
    )
    return session.scalars(statement).first()
