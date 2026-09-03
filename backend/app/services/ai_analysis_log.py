from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models import AIAnalysisLog


def log_analysis(
    session: Session,
    *,
    analysis_type: str,
    symbol: str | None,
    model: str,
    prompt_version: str,
    request_payload: dict[str, Any],
    response_payload: dict[str, Any] | None,
    raw_output: str | None,
    duration_ms: int | None,
    status: str,
    error_message: str | None,
) -> AIAnalysisLog:
    log = AIAnalysisLog(
        analysis_type=analysis_type,
        symbol=symbol,
        model=model,
        prompt_version=prompt_version,
        request_payload=request_payload,
        response_payload=response_payload,
        raw_output=raw_output,
        duration_ms=duration_ms,
        status=status,
        error_message=error_message,
        created_at=datetime.now(UTC),
    )
    session.add(log)
    session.commit()
    return log
