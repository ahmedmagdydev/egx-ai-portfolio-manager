from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..domain.finance import (
    FinancialSnapshot,
    book_value_per_share,
    dividend_yield,
    growth,
    liabilities_to_equity,
    price_to_book,
    price_to_earnings,
    profit_margin,
    return_on_assets,
    return_on_equity,
)
from ..models import FinancialStatement, Stock
from ..providers.finance.mock import MockFinancialDataProvider
from ..repositories.finance import (
    get_latest_statement,
    get_prior_statement,
    upsert_statement,
)
from ..services.market_data import get_quote


def _load_stock(session: Session, symbol: str) -> Stock:
    stock = session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if stock is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "UNKNOWN_STOCK", "message": f"Unknown stock: {symbol}"},
        )
    return stock


def import_statements(session: Session, symbol: str) -> list[FinancialStatement]:
    provider = MockFinancialDataProvider()
    stock = _load_stock(session, symbol)
    records = provider.get_statements(symbol)
    statements: list[FinancialStatement] = []
    for record in records:
        statements.append(upsert_statement(session, stock, record))
    return statements


def _metric(value: Decimal | None, warning: str | None = None) -> dict:
    return {
        "value": value,
        "status": "ok" if value is not None else "not_available",
        "warning": warning,
    }


def _build_snapshot(
    symbol: str,
    statement: FinancialStatement,
    prior: FinancialStatement | None,
    quote,
) -> FinancialSnapshot:
    warnings: list[str] = []
    price = None
    price_as_of = None
    if quote is not None:
        price = quote.price
        price_as_of = quote.market_timestamp
    else:
        warnings.append("No price available; valuation ratios omitted")

    scale = str(statement.unit_scale)

    pe = price_to_earnings(price, statement.eps) if price is not None else None
    pb = None
    if price is not None:
        bvps = book_value_per_share(statement.equity, statement.shares_outstanding, scale)  # type: ignore[arg-type]
        pb = price_to_book(price, bvps)
        if pb is None:
            warnings.append("P/B unavailable: missing equity or shares outstanding")

    roe = return_on_equity(statement.net_income, statement.equity, scale)  # type: ignore[arg-type]
    if roe is None:
        warnings.append("ROE unavailable: missing net income or equity")

    roa = return_on_assets(statement.net_income, statement.assets, scale)  # type: ignore[arg-type]
    if roa is None:
        warnings.append("ROA unavailable: missing net income or assets")

    le = liabilities_to_equity(statement.liabilities, statement.equity, scale)  # type: ignore[arg-type]
    if le is None:
        warnings.append("Liabilities-to-equity unavailable: missing liabilities or equity")

    pm = profit_margin(statement.net_income, statement.revenue)
    if pm is None:
        warnings.append("Profit margin unavailable: missing net income or revenue")

    revenue_growth = None
    earnings_growth = None
    if prior is not None:
        if str(prior.unit_scale) != scale:
            warnings.append("Prior statement uses a different unit scale; growth omitted")
        else:
            revenue_growth = growth(statement.revenue, prior.revenue)
            earnings_growth = growth(statement.net_income, prior.net_income)
    else:
        warnings.append("No prior comparable statement; growth metrics omitted")

    dy = dividend_yield(statement.dividends_per_share, price) if price is not None else None
    if dy is None and price is not None:
        warnings.append("Dividend yield unavailable: missing dividends per share")

    return FinancialSnapshot(
        symbol=symbol.upper(),
        period_end=statement.period_end,
        period_type=statement.period_type,
        scope=statement.scope,
        currency=statement.currency,
        unit_scale=scale,
        price=price,
        price_as_of=price_as_of,
        pe=pe,
        pb=pb,
        roe=roe,
        roa=roa,
        liabilities_to_equity=le,
        profit_margin=pm,
        revenue_growth=revenue_growth,
        earnings_growth=earnings_growth,
        dividend_yield=dy,
        warnings=warnings,
    )


def get_snapshot(
    session: Session,
    settings: Settings,
    symbol: str,
    as_of: datetime | None = None,
) -> FinancialSnapshot:
    stock = _load_stock(session, symbol)
    statements = import_statements(session, symbol)
    if not statements:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "STATEMENTS_UNAVAILABLE",
                "message": f"No financial statements available for {symbol.upper()}",
            },
        )
    statement = get_latest_statement(
        session, stock, period_type="annual", scope="consolidated", as_of=as_of
    )
    if statement is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "STATEMENTS_UNAVAILABLE",
                "message": f"No financial statements available for {symbol.upper()}",
            },
        )
    prior = get_prior_statement(session, stock, statement.period_end, "annual", "consolidated")
    quote = get_quote(session, settings, symbol)
    return _build_snapshot(symbol, statement, prior, quote)
