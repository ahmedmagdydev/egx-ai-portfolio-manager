import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")
logger = logging.getLogger("egx-api")


def configure_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), force=True)


def log_request(
    *,
    level: str,
    route: str,
    duration_ms: float,
    error_code: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "level": level,
        "service": "egx-api",
        "correlation_id": correlation_id_var.get(),
        "route": route,
        "duration_ms": round(duration_ms, 2),
        "error_code": error_code,
    }
    logger.log(
        getattr(logging, level.upper(), logging.INFO),
        json.dumps(payload, ensure_ascii=False),
    )
