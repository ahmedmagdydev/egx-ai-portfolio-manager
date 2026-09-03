from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import RiskLimits as RiskLimitsModel
from ..schemas.risk import RiskLimits

_DEFAULTS = {
    "max_single_position_percent": Decimal("25.0"),
    "max_sector_exposure_percent": Decimal("40.0"),
    "min_cash_percent": Decimal("10.0"),
    "max_portfolio_volatility_annual": None,
    "max_drawdown_percent": None,
    "rebalancing_threshold_percent": Decimal("5.0"),
}


def get_risk_limits(session: Session) -> RiskLimitsModel:
    row = session.scalars(select(RiskLimitsModel).order_by(RiskLimitsModel.id)).first()
    if row is None:
        now = datetime.now(UTC)
        row = RiskLimitsModel(
            **_DEFAULTS,
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
    return row


def update_risk_limits(session: Session, limits: RiskLimits) -> RiskLimitsModel:
    row = get_risk_limits(session)
    row.max_single_position_percent = limits.max_single_position_percent
    row.max_sector_exposure_percent = limits.max_sector_exposure_percent
    row.min_cash_percent = limits.min_cash_percent
    row.max_portfolio_volatility_annual = limits.max_portfolio_volatility_annual
    row.max_drawdown_percent = limits.max_drawdown_percent
    row.rebalancing_threshold_percent = limits.rebalancing_threshold_percent
    row.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(row)
    return row
