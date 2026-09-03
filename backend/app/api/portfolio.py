from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from ..config import Settings, get_settings
from ..db_session import get_session
from ..domain.money import quantize_money, quantize_price
from ..domain.portfolio import (
    AllocationReport,
    PortfolioSummary,
    compute_allocation,
    compute_cash,
    compute_holdings,
    value_holdings,
)
from ..models import Stock, Transaction
from ..providers.market.mock import MockMarketDataProvider
from ..providers.market.snapshot_store import upsert_quotes
from ..schemas.portfolio import (
    AllocationLineResponse,
    AllocationResponse,
    CashResponse,
    HoldingResponse,
    HoldingsResponse,
    PriceResponse,
    StockCreate,
    StockResponse,
    SummaryResponse,
    TransactionCreate,
    TransactionPage,
    TransactionResponse,
)
from ..services.portfolio_service import (
    add_transaction,
    count_transactions,
    current_events,
    delete_transaction,
    update_transaction,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def now_utc() -> datetime:
    return datetime.now(UTC)


def stock_response(stock: Stock, generated_at: datetime) -> StockResponse:
    return StockResponse(
        id=stock.id,
        symbol=stock.symbol,
        name_en=stock.name_en,
        name_ar=stock.name_ar,
        sector=stock.sector,
        currency=stock.currency,
        is_active=stock.is_active,
        created_at=stock.created_at,
        generated_at=generated_at,
    )


def transaction_response(row: Transaction, generated_at: datetime) -> TransactionResponse:
    return TransactionResponse(
        id=row.id,
        stock_id=row.stock_id,
        type=row.type,
        symbol=row.stock.symbol if row.stock else None,
        quantity=row.quantity,
        price=row.price,
        fees=row.fees,
        amount=row.amount,
        executed_at=row.executed_at,
        sequence=row.sequence,
        note=row.note,
        created_at=row.created_at,
        generated_at=generated_at,
    )


def _provider(settings: Settings) -> MockMarketDataProvider:
    if settings.market_data_provider != "mock":
        raise ValueError("Only the mock market data provider is supported in Phase 01")
    return MockMarketDataProvider(settings)


def _valuations(session: Session, settings: Settings):
    holdings = compute_holdings(current_events(session))
    stocks = {
        stock.symbol: stock
        for stock in session.scalars(select(Stock).where(Stock.symbol.in_(holdings.keys())))
    }
    quotes = _provider(settings).get_quotes(list(holdings))
    upsert_quotes(session, stocks, quotes)
    session.commit()
    sectors = {symbol: stocks[symbol].sector for symbol in holdings if symbol in stocks}
    cash_value = compute_cash(current_events(session))
    return (
        holdings,
        value_holdings(holdings, quotes, sectors),
        cash_value,
    )


@router.post("/stocks", response_model=StockResponse, status_code=201)
def create_stock(
    body: StockCreate,
    session: Session = Depends(get_session),
) -> StockResponse:
    generated_at = now_utc()
    symbol = body.symbol.strip().upper()
    if not symbol or session.scalar(select(Stock).where(Stock.symbol == symbol)) is not None:
        raise HTTPException(
            status_code=409,
            detail={"code": "STOCK_EXISTS", "message": "Stock already exists"},
        )
    stock = Stock(
        symbol=symbol,
        name_en=body.name_en,
        name_ar=body.name_ar,
        sector=body.sector,
    )
    session.add(stock)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "STOCK_EXISTS", "message": "Stock already exists"},
        ) from None
    session.refresh(stock)
    return stock_response(stock, generated_at)


@router.get("/stocks", response_model=list[StockResponse])
def list_stocks(session: Session = Depends(get_session)) -> list[StockResponse]:
    generated_at = now_utc()
    stocks = session.scalars(select(Stock).order_by(Stock.symbol)).all()
    return [stock_response(stock, generated_at) for stock in stocks]


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
def create_transaction(
    body: TransactionCreate,
    session: Session = Depends(get_session),
) -> TransactionResponse:
    generated_at = now_utc()
    try:
        row = add_transaction(
            session,
            transaction_type=body.type,
            symbol=body.symbol,
            quantity=body.quantity,
            price=body.price,
            fees=body.fees,
            amount=body.amount,
            executed_at=body.executed_at,
            note=body.note,
        )
        session.commit()
        session.refresh(row)
        if row.stock is None and row.stock_id is not None:
            session.refresh(row, attribute_names=["stock"])
        return transaction_response(row, generated_at)
    except Exception:
        session.rollback()
        raise


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction_endpoint(
    transaction_id: str,
    body: TransactionCreate,
    session: Session = Depends(get_session),
) -> TransactionResponse:
    generated_at = now_utc()
    try:
        row = update_transaction(
            session,
            transaction_id,
            transaction_type=body.type,
            symbol=body.symbol,
            quantity=body.quantity,
            price=body.price,
            fees=body.fees,
            amount=body.amount,
            executed_at=body.executed_at,
            note=body.note,
        )
        session.commit()
        session.refresh(row)
        if row.stock is None and row.stock_id is not None:
            session.refresh(row, attribute_names=["stock"])
        return transaction_response(row, generated_at)
    except Exception:
        session.rollback()
        raise


@router.delete("/transactions/{transaction_id}", status_code=204)
def delete_transaction_endpoint(
    transaction_id: str,
    session: Session = Depends(get_session),
) -> None:
    try:
        delete_transaction(session, transaction_id)
        session.commit()
    except Exception:
        session.rollback()
        raise


@router.get("/transactions", response_model=TransactionPage)
def list_transactions(
    symbol: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> TransactionPage:
    generated_at = now_utc()
    statement = (
        select(Transaction)
        .options(joinedload(Transaction.stock))
        .order_by(Transaction.executed_at, Transaction.sequence)
        .limit(limit)
        .offset(offset)
    )
    if symbol:
        statement = statement.join(Transaction.stock).where(Stock.symbol == symbol.upper())
    rows = list(session.scalars(statement))
    return TransactionPage(
        items=[transaction_response(row, generated_at) for row in rows],
        total=count_transactions(session, symbol),
        limit=limit,
        offset=offset,
        generated_at=generated_at,
    )


def _summary(valuations, cash: Decimal) -> PortfolioSummary:
    priced = [item for item in valuations if item.market_value is not None]
    return PortfolioSummary(
        total_market_value=sum(
            (item.market_value or Decimal("0") for item in priced),
            Decimal("0"),
        ),
        total_cost=sum((item.total_cost for item in valuations), Decimal("0")),
        cash=cash,
        total_value=cash
        + sum((item.market_value or Decimal("0") for item in priced), Decimal("0")),
        realized_pnl=sum((item.realized_pnl for item in valuations), Decimal("0")),
        unrealized_pnl=sum((item.unrealized_pnl or Decimal("0") for item in priced), Decimal("0")),
        data_as_of=min((item.price.observed_at for item in priced if item.price), default=None),
        unpriced_count=len(valuations) - len(priced),
    )


def _holding_response(item) -> HoldingResponse:
    quote = item.price
    return HoldingResponse(
        symbol=item.symbol,
        quantity=item.quantity,
        avg_cost=quantize_price(item.avg_cost),
        total_cost=quantize_money(item.total_cost),
        market_value=quantize_money(item.market_value) if item.market_value is not None else None,
        unrealized_pnl=(
            quantize_money(item.unrealized_pnl)
            if item.unrealized_pnl is not None
            else None
        ),
        unrealized_pnl_pct=item.unrealized_pnl_pct,
        realized_pnl=quantize_money(item.realized_pnl),
        price=PriceResponse(
            value=quantize_price(quote.price) if quote else None,
            source=quote.source if quote else None,
            observed_at=quote.observed_at if quote else None,
            freshness=quote.freshness if quote else None,
            status=item.price_status,
        ),
    )


@router.get("/holdings", response_model=HoldingsResponse)
def holdings(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> HoldingsResponse:
    generated_at = now_utc()
    _, valuations, cash = _valuations(session, settings)
    summary = _summary(valuations, cash)
    return HoldingsResponse(
        holdings=[_holding_response(item) for item in valuations],
        summary=SummaryResponse(
            total_market_value=quantize_money(summary.total_market_value),
            total_cost=quantize_money(summary.total_cost),
            cash=quantize_money(summary.cash),
            total_value=quantize_money(summary.total_value),
            realized_pnl=quantize_money(summary.realized_pnl),
            unrealized_pnl=quantize_money(summary.unrealized_pnl),
            data_as_of=summary.data_as_of,
            unpriced_count=summary.unpriced_count,
        ),
        data_as_of=summary.data_as_of,
        generated_at=generated_at,
    )


def _allocation_response(report: AllocationReport, generated_at: datetime) -> AllocationResponse:
    def line(item):
        return AllocationLineResponse(
            name=item.name,
            value=quantize_money(item.value),
            weight=item.weight,
        )

    return AllocationResponse(
        by_symbol=[line(item) for item in report.by_symbol],
        by_sector=[line(item) for item in report.by_sector],
        cash=line(report.cash),
        unpriced_symbols=report.unpriced_symbols,
        generated_at=generated_at,
    )


@router.get("/allocation", response_model=AllocationResponse)
def allocation(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AllocationResponse:
    generated_at = now_utc()
    _, valuations, cash = _valuations(session, settings)
    return _allocation_response(compute_allocation(valuations, cash), generated_at)


@router.get("/cash", response_model=CashResponse)
def cash(session: Session = Depends(get_session)) -> CashResponse:
    return CashResponse(
        cash=quantize_money(compute_cash(current_events(session))),
        generated_at=now_utc(),
    )
