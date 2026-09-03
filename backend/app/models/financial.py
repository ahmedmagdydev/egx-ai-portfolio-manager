from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .portfolio import Stock


class PeriodType(str, Enum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class ScopeType(str, Enum):
    CONSOLIDATED = "consolidated"
    STANDALONE = "standalone"


class UnitScale(str, Enum):
    UNITS = "units"
    THOUSANDS = "thousands"
    MILLIONS = "millions"


class FinancialStatement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "period_end",
            "period_type",
            "scope",
            "source",
            "version",
            name="uq_financial_statements_stock_period_scope_source_version",
        ),
    )

    stock_id: Mapped[str] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    period_start: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    period_end: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EGP", nullable=False)
    unit_scale: Mapped[str] = mapped_column(String(20), default="units", nullable=False)

    revenue: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    gross_profit: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    operating_profit: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    net_income: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    eps: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    assets: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    liabilities: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    equity: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    cash: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    operating_cash_flow: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    investing_cash_flow: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    financing_cash_flow: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    shares_outstanding: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    dividends_per_share: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)

    source: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    published_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    stock: Mapped[Stock] = relationship(back_populates="financial_statements")
