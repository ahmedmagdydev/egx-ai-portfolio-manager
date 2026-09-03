from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..domain.portfolio import (
    HoldingState,
    InvalidTransactionError,
    PortfolioError,
    TxnEvent,
    compute_cash,
    compute_holdings,
)
from ..models import Stock, Transaction, TransactionType


class UnknownStockError(PortfolioError):
    code = "UNKNOWN_STOCK"

    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Unknown stock: {symbol}")


def transaction_events(rows: Iterable[Transaction]) -> list[TxnEvent]:
    return [
        TxnEvent(
            type=row.type.value,
            symbol=row.stock.symbol if row.stock else None,
            quantity=row.quantity,
            price=row.price,
            fees=row.fees,
            amount=row.amount,
            executed_at=row.executed_at,
            sequence=row.sequence,
        )
        for row in rows
    ]


def load_transactions(session: Session) -> list[Transaction]:
    statement = (
        select(Transaction)
        .options(joinedload(Transaction.stock))
        .order_by(Transaction.executed_at, Transaction.sequence)
    )
    return list(session.scalars(statement))


def current_events(session: Session) -> list[TxnEvent]:
    return transaction_events(load_transactions(session))


def current_holdings(session: Session) -> dict[str, HoldingState]:
    return compute_holdings(current_events(session))


def current_cash(session: Session) -> Decimal:
    return compute_cash(current_events(session))


def add_transaction(
    session: Session,
    *,
    transaction_type: TransactionType,
    symbol: str | None,
    quantity: Decimal | None,
    price: Decimal | None,
    fees: Decimal,
    amount: Decimal | None,
    executed_at: datetime,
    note: str | None,
) -> Transaction:
    stock = None
    if symbol is not None:
        normalized_symbol = symbol.upper()
        stock = session.scalar(select(Stock).where(Stock.symbol == normalized_symbol))
        if stock is None:
            raise UnknownStockError(normalized_symbol)
        symbol = normalized_symbol
    if transaction_type in {TransactionType.BUY, TransactionType.SELL, TransactionType.DIVIDEND}:
        if stock is None:
            raise InvalidTransactionError("BUY, SELL, and DIVIDEND transactions require a symbol")
    elif symbol is not None:
        raise InvalidTransactionError("Cash transactions cannot have a symbol")
    if transaction_type in {TransactionType.BUY, TransactionType.SELL} and (
        quantity is None or price is None
    ):
        raise InvalidTransactionError("BUY and SELL transactions require quantity and price")
    if (
        transaction_type
        in {TransactionType.DEPOSIT, TransactionType.WITHDRAWAL, TransactionType.DIVIDEND}
        and amount is None
    ):
        raise InvalidTransactionError("Cash transactions require amount")
    rows = load_transactions(session)
    next_sequence = max((row.sequence for row in rows), default=0) + 1
    event = TxnEvent(
        type=transaction_type.value,
        symbol=symbol,
        quantity=quantity,
        price=price,
        fees=fees,
        amount=amount,
        executed_at=executed_at,
        sequence=next_sequence,
    )
    events = transaction_events(rows) + [event]
    compute_holdings(events)
    compute_cash(events)
    result = Transaction(
        stock_id=stock.id if stock else None,
        type=transaction_type,
        quantity=quantity,
        price=price,
        fees=fees,
        amount=amount,
        executed_at=executed_at,
        note=note,
    )
    session.add(result)
    session.flush()
    return result


def get_transaction(session: Session, transaction_id: str) -> Transaction | None:
    return session.scalar(
        select(Transaction)
        .options(joinedload(Transaction.stock))
        .where(Transaction.id == transaction_id)
    )


def update_transaction(
    session: Session,
    transaction_id: str,
    *,
    transaction_type: TransactionType,
    symbol: str | None,
    quantity: Decimal | None,
    price: Decimal | None,
    fees: Decimal,
    amount: Decimal | None,
    executed_at: datetime,
    note: str | None,
) -> Transaction:
    row = get_transaction(session, transaction_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "TRANSACTION_NOT_FOUND", "message": "Transaction not found"},
        )
    stock = None
    if symbol is not None:
        stock = session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
        if stock is None:
            raise UnknownStockError(symbol)
    if transaction_type in {TransactionType.BUY, TransactionType.SELL, TransactionType.DIVIDEND}:
        if stock is None:
            raise InvalidTransactionError("BUY, SELL, and DIVIDEND transactions require a symbol")
    elif symbol is not None:
        raise InvalidTransactionError("Cash transactions cannot have a symbol")
    if transaction_type in {TransactionType.BUY, TransactionType.SELL} and (
        quantity is None or price is None
    ):
        raise InvalidTransactionError(
            "BUY and SELL transactions require quantity and price"
        )
    if transaction_type in {
        TransactionType.DEPOSIT,
        TransactionType.WITHDRAWAL,
        TransactionType.DIVIDEND,
    } and amount is None:
        raise InvalidTransactionError("Cash transactions require amount")
    row.stock_id = stock.id if stock else None
    row.type = transaction_type
    row.quantity = quantity
    row.price = price
    row.fees = fees
    row.amount = amount
    row.executed_at = executed_at
    row.note = note
    session.flush()
    return row


def delete_transaction(session: Session, transaction_id: str) -> None:
    row = get_transaction(session, transaction_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "TRANSACTION_NOT_FOUND", "message": "Transaction not found"},
        )
    session.delete(row)
    session.flush()


def count_transactions(session: Session, symbol: str | None = None) -> int:
    statement = select(func.count()).select_from(Transaction)
    if symbol:
        statement = statement.join(Transaction.stock).where(Stock.symbol == symbol.upper())
    return int(session.scalar(statement) or 0)
