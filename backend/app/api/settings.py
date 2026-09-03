from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db_session import get_session
from ..schemas.risk import RiskLimits, RiskLimitsRecord
from ..services.risk_limits import get_risk_limits, update_risk_limits

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/risk-limits", response_model=RiskLimitsRecord)
def get_limits(session: Session = Depends(get_session)) -> RiskLimitsRecord:
    row = get_risk_limits(session)
    return RiskLimitsRecord.model_validate(row)


@router.post("/risk-limits", response_model=RiskLimitsRecord)
def set_limits(
    limits: RiskLimits,
    session: Session = Depends(get_session),
) -> RiskLimitsRecord:
    row = update_risk_limits(session, limits)
    return RiskLimitsRecord.model_validate(row)
