from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

from .money import ZERO, as_decimal

TransactionKind = Literal["BUY", "SELL", "DEPOSIT", "WITHDRAWAL", "DIVIDEND"]


class PortfolioError(Exception):
    code = "INVALID_TRANSACTION"


class InvalidTransactionError(PortfolioError):
    code = "INVALID_TRANSACTION"


class InsufficientHoldingsError(PortfolioError):
    code = "INSUFFICIENT_HOLDINGS"

    def __init__(self, symbol: str, held: Decimal, requested: Decimal):
        self.symbol = symbol
        self.held = held
        self.requested = requested
        super().__init__(f"Insufficient holdings for {symbol}: held {held}, requested {requested}")


class InsufficientCashError(PortfolioError):
    code = "INSUFFICIENT_CASH"

    def __init__(self, held: Decimal, requested: Decimal):
        self.held = held
        self.requested = requested
        super().__init__(f"Insufficient cash: held {held}, requested {requested}")


@dataclass(frozen=True)
class TxnEvent:
    type: TransactionKind
    symbol: str | None
    quantity: Decimal | None
    price: Decimal | None
    fees: Decimal
    amount: Decimal | None
    executed_at: datetime
    sequence: int


@dataclass(frozen=True)
class HoldingState:
    symbol: str
    quantity: Decimal
    total_cost: Decimal
    avg_cost: Decimal
    realized_pnl: Decimal


@dataclass(frozen=True)
class PriceQuote:
    symbol: str
    price: Decimal
    currency: str
    source: str
    observed_at: datetime
    freshness: str


@dataclass(frozen=True)
class HoldingValuation:
    symbol: str
    quantity: Decimal
    total_cost: Decimal
    avg_cost: Decimal
    realized_pnl: Decimal
    market_value: Decimal | None
    unrealized_pnl: Decimal | None
    unrealized_pnl_pct: Decimal | None
    price: PriceQuote | None
    price_status: str
    sector: str | None = None


@dataclass(frozen=True)
class AllocationLine:
    name: str
    value: Decimal
    weight: Decimal


@dataclass(frozen=True)
class AllocationReport:
    by_symbol: list[AllocationLine]
    by_sector: list[AllocationLine]
    cash: AllocationLine
    unpriced_symbols: list[str]


@dataclass(frozen=True)
class PortfolioSummary:
    total_market_value: Decimal
    total_cost: Decimal
    cash: Decimal
    total_value: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    data_as_of: datetime | None
    unpriced_count: int


def _required_event(
    event: TxnEvent, *, quantity: bool = False, price: bool = False
) -> tuple[Decimal, ...]:
    if (
        event.symbol is None
        or (quantity and event.quantity is None)
        or (price and event.price is None)
    ):
        raise InvalidTransactionError("Transaction is missing required stock fields")
    values: list[Decimal] = []
    if quantity:
        values.append(as_decimal(event.quantity))  # type: ignore[arg-type]
    if price:
        values.append(as_decimal(event.price))  # type: ignore[arg-type]
    return tuple(values)


def _ordered(transactions: list[TxnEvent]) -> list[TxnEvent]:
    return sorted(transactions, key=lambda event: (event.executed_at, event.sequence))


def compute_holdings(transactions: list[TxnEvent]) -> dict[str, HoldingState]:
    states: dict[str, dict[str, Decimal]] = {}
    for event in _ordered(transactions):
        if event.type not in {"BUY", "SELL", "DIVIDEND"}:
            continue
        symbol = event.symbol
        if symbol is None:
            raise InvalidTransactionError("Stock transaction requires a symbol")
        state = states.setdefault(
            symbol,
            {"quantity": ZERO, "total_cost": ZERO, "avg_cost": ZERO, "realized_pnl": ZERO},
        )
        fees = as_decimal(event.fees)
        if fees < ZERO:
            raise InvalidTransactionError("Fees cannot be negative")
        if event.type == "DIVIDEND":
            if event.amount is None or event.amount < ZERO:
                raise InvalidTransactionError("Dividend requires a non-negative amount")
            state["realized_pnl"] += as_decimal(event.amount)
            continue
        quantity, price = _required_event(event, quantity=True, price=True)
        if quantity <= ZERO or price < ZERO:
            raise InvalidTransactionError("Quantity must be positive and price cannot be negative")
        if event.type == "BUY":
            state["total_cost"] += quantity * price + fees
            state["quantity"] += quantity
            state["avg_cost"] = state["total_cost"] / state["quantity"]
        else:
            if quantity > state["quantity"]:
                raise InsufficientHoldingsError(symbol, state["quantity"], quantity)
            state["realized_pnl"] += quantity * price - fees - quantity * state["avg_cost"]
            state["total_cost"] -= quantity * state["avg_cost"]
            state["quantity"] -= quantity
            if state["quantity"] == ZERO:
                state["avg_cost"] = ZERO
                state["total_cost"] = ZERO
    return {
        symbol: HoldingState(symbol=symbol, **values)
        for symbol, values in states.items()
        if values["quantity"] > ZERO or values["realized_pnl"] != ZERO
    }


def compute_cash(transactions: list[TxnEvent]) -> Decimal:
    cash = ZERO
    for event in _ordered(transactions):
        fees = as_decimal(event.fees)
        if fees < ZERO:
            raise InvalidTransactionError("Fees cannot be negative")
        if event.type in {"DEPOSIT", "WITHDRAWAL", "DIVIDEND"}:
            if event.amount is None or event.amount < ZERO:
                raise InvalidTransactionError("Cash transaction requires a non-negative amount")
            change = as_decimal(event.amount)
            if event.type == "WITHDRAWAL":
                change = -change
            cash += change
        elif event.type in {"BUY", "SELL"}:
            quantity, price = _required_event(event, quantity=True, price=True)
            change = quantity * price - fees
            if event.type == "BUY":
                change = -quantity * price - fees
            previous_cash = cash
            cash += change
            if cash < ZERO:
                raise InsufficientCashError(previous_cash, -change)
            continue
        if cash < ZERO:
            raise InsufficientCashError(cash - change, -change)
    return cash


def value_holdings(
    holdings: dict[str, HoldingState],
    prices: dict[str, PriceQuote | None],
    sectors: dict[str, str | None] | None = None,
) -> list[HoldingValuation]:
    valuations: list[HoldingValuation] = []
    for symbol, holding in holdings.items():
        quote = prices.get(symbol)
        if quote is None:
            valuations.append(
                HoldingValuation(
                    symbol=symbol,
                    quantity=holding.quantity,
                    total_cost=holding.total_cost,
                    avg_cost=holding.avg_cost,
                    realized_pnl=holding.realized_pnl,
                    market_value=None,
                    unrealized_pnl=None,
                    unrealized_pnl_pct=None,
                    price=None,
                    price_status="unavailable",
                    sector=(sectors or {}).get(symbol),
                )
            )
            continue
        market_value = holding.quantity * quote.price
        unrealized = market_value - holding.total_cost
        pct = None if holding.total_cost == ZERO else unrealized / holding.total_cost
        valuations.append(
            HoldingValuation(
                symbol=symbol,
                quantity=holding.quantity,
                total_cost=holding.total_cost,
                avg_cost=holding.avg_cost,
                realized_pnl=holding.realized_pnl,
                market_value=market_value,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=pct,
                price=quote,
                price_status=quote.freshness,
                sector=(sectors or {}).get(symbol),
            )
        )
    return valuations


def compute_allocation(
    valuations: list[HoldingValuation],
    cash: Decimal,
) -> AllocationReport:
    cash = as_decimal(cash)
    priced = [item for item in valuations if item.market_value is not None]
    total = cash + sum((item.market_value or ZERO for item in priced), ZERO)

    def weight(value: Decimal) -> Decimal:
        return ZERO if total == ZERO else value / total

    by_symbol = [
        AllocationLine(
            name=item.symbol,
            value=item.market_value or ZERO,
            weight=weight(item.market_value or ZERO),
        )
        for item in priced
    ]
    sector_values: dict[str, Decimal] = {}
    for item in priced:
        sector = item.sector or "Unclassified"
        sector_values[sector] = sector_values.get(sector, ZERO) + (item.market_value or ZERO)
    by_sector = [
        AllocationLine(name=sector, value=value, weight=weight(value))
        for sector, value in sorted(sector_values.items())
    ]
    return AllocationReport(
        by_symbol=by_symbol,
        by_sector=by_sector,
        cash=AllocationLine(name="cash", value=cash, weight=weight(cash)),
        unpriced_symbols=[item.symbol for item in valuations if item.market_value is None],
    )
