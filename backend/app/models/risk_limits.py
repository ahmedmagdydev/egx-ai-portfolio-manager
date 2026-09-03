from datetime import datetime
from decimal import Decimal

from sqlalchemy import TIMESTAMP, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, utc_now


class RiskLimits(Base, TimestampMixin):
    __tablename__ = "risk_limits"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    max_single_position_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("25.0")
    )
    max_sector_exposure_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("40.0")
    )
    min_cash_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("10.0")
    )
    max_portfolio_volatility_annual: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    max_drawdown_percent: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    rebalancing_threshold_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("5.0")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
