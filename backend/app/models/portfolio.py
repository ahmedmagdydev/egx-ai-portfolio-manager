from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .documents import Document
    from .financial import FinancialStatement
    from .market_data import StockPrice


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    DIVIDEND = "DIVIDEND"


class Freshness(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNAVAILABLE = "unavailable"


transaction_type_enum = SAEnum(TransactionType, name="transaction_type", native_enum=True)
freshness_enum = SAEnum(
    Freshness,
    name="freshness",
    native_enum=True,
    values_callable=lambda values: [item.value for item in values],
)


class Stock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name_en: Mapped[str] = mapped_column(String, nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    transactions: Mapped[list[Transaction]] = relationship(back_populates="stock")
    price_snapshots: Mapped[list[PriceSnapshot]] = relationship(back_populates="stock")
    stock_prices: Mapped[list[StockPrice]] = relationship(back_populates="stock")
    financial_statements: Mapped[list[FinancialStatement]] = relationship(back_populates="stock")
    documents: Mapped[list[Document]] = relationship(back_populates="stock")


class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="ck_transactions_quantity_positive",
        ),
        CheckConstraint("price IS NULL OR price >= 0", name="ck_transactions_price_nonnegative"),
        CheckConstraint("fees >= 0", name="ck_transactions_fees_nonnegative"),
        Index("ix_transactions_stock_executed_sequence", "stock_id", "executed_at", "sequence"),
    )

    stock_id: Mapped[UUID | None] = mapped_column(ForeignKey("stocks.id"), nullable=True)
    type: Mapped[TransactionType] = mapped_column(transaction_type_enum, nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    fees: Mapped[Decimal] = mapped_column(Numeric(20, 2), default=0, nullable=False)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(20, 2), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    sequence: Mapped[int] = mapped_column(BigInteger, Identity(), nullable=False, unique=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    stock: Mapped[Stock | None] = relationship(back_populates="transactions")


class PriceSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "price_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "source",
            "observed_at",
            name="uq_price_snapshots_stock_source_observed",
        ),
    )

    stock_id: Mapped[UUID] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    freshness: Mapped[Freshness] = mapped_column(freshness_enum, nullable=False)

    stock: Mapped[Stock] = relationship(back_populates="price_snapshots")
