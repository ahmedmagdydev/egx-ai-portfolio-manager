from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import Settings, get_settings
from ..db_session import get_session
from ..schemas.risk import RebalancingSuggestion, RiskReport
from ..services.risk_engine import calculate_portfolio_risk, generate_rebalancing_suggestions
from ..services.risk_limits import get_risk_limits

router = APIRouter(prefix="/api/risk", tags=["risk"])


@router.get("/portfolio", response_model=RiskReport)
def portfolio_risk(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RiskReport:
    try:
        return calculate_portfolio_risk(session, settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "NEGATIVE_VALUE", "message": str(exc)},
        ) from exc


@router.get("/portfolio/summary")
def portfolio_risk_summary(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    report = calculate_portfolio_risk(session, settings)
    limits = get_risk_limits(session)
    return {
        "total_portfolio_value": str(report.total_portfolio_value),
        "cash_percent": str(report.cash_percent),
        "largest_position_symbol": report.largest_position_symbol,
        "largest_position_percent": str(report.largest_position_percent),
        "largest_sector": report.largest_sector,
        "largest_sector_percent": str(report.largest_sector_percent),
        "breach_count": len(report.breaches),
        "limits": {
            "max_single_position_percent": str(limits.max_single_position_percent),
            "max_sector_exposure_percent": str(limits.max_sector_exposure_percent),
            "min_cash_percent": str(limits.min_cash_percent),
        },
        "data_as_of": report.data_as_of.isoformat(),
    }


@router.get("/portfolio/rebalancing", response_model=list[RebalancingSuggestion])
def rebalancing_suggestions(
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[RebalancingSuggestion]:
    return generate_rebalancing_suggestions(session, settings)
