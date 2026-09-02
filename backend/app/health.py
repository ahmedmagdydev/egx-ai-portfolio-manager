import unicodedata
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Engine, text
from sqlalchemy.exc import SQLAlchemyError

from . import __version__
from .config import Settings, get_settings
from .db import get_engine

router = APIRouter(prefix="/health")


def utc_now() -> datetime:
    return datetime.now(UTC)


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str = "egx-api"
    version: str = __version__
    checks: dict[str, Any]
    timestamp: datetime
    detail: dict[str, str] | None = None


class Utf8ProbeRequest(BaseModel):
    text: str


class Utf8ProbeResponse(BaseModel):
    sent: str
    stored: str
    round_trip_ok: bool
    nfc_normalized: bool


@router.get("/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(status="ok", checks={}, timestamp=utc_now())


def ready_result(engine: Engine) -> tuple[bool, dict[str, Any], dict[str, str] | None]:
    checks: dict[str, Any] = {
        "database": {"status": "unavailable", "code": "DB_UNAVAILABLE"},
        "pgvector": {"status": "unknown"},
    }
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            extension_version = connection.execute(
                text("SELECT extversion FROM pg_extension WHERE extname='vector'")
            ).scalar()
        checks["database"] = {"status": "ok"}
        if extension_version:
            checks["pgvector"] = {"status": "ok", "version": extension_version}
        else:
            checks["pgvector"] = {"status": "missing"}
    except SQLAlchemyError:
        return False, checks, {
            "code": "DB_UNAVAILABLE",
            "hint": "Database is unavailable; check PostgreSQL and retry.",
        }
    ready = checks["database"]["status"] == "ok" and checks["pgvector"]["status"] == "ok"
    detail = None if ready else {
        "code": "PGVECTOR_MISSING",
        "hint": "The vector extension is missing; run migrations and retry.",
    }
    return ready, checks, detail


@router.get("/ready", response_model=HealthResponse)
def ready(response: Response, engine: Engine = Depends(get_engine)) -> HealthResponse:
    is_ready, checks, detail = ready_result(engine)
    response.status_code = 200 if is_ready else 503
    return HealthResponse(
        status="ok" if is_ready else "degraded",
        checks=checks,
        timestamp=utc_now(),
        detail=detail,
    )


@router.get("/ollama", response_model=HealthResponse)
async def ollama(response: Response, settings: Settings = Depends(get_settings)) -> HealthResponse:
    configured_models = [settings.ollama_reasoning_model, settings.ollama_embedding_model]
    try:
        async with httpx.AsyncClient(timeout=settings.health_timeout_seconds) as client:
            http_response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            if http_response.status_code >= 400:
                raise httpx.HTTPStatusError(
                    "Ollama returned an error",
                    request=httpx.Request("GET", http_response.url),
                    response=http_response,
                )
            models = {
                item.get("name")
                for item in http_response.json().get("models", [])
                if isinstance(item, dict)
            }
        checks = {
            "ollama": {"status": "ok"},
            "models": {model: {"present": model in models} for model in configured_models},
        }
        return HealthResponse(status="ok", checks=checks, timestamp=utc_now())
    except (httpx.HTTPError, ValueError, TypeError):
        # The response intentionally does not expose connection details.
        response.status_code = 503
        return HealthResponse(
            status="degraded",
            checks={"ollama": {"status": "unavailable"}},
            timestamp=utc_now(),
            detail={
                "code": "OLLAMA_UNAVAILABLE",
                "hint": "Ollama is unavailable; start it and retry.",
            },
        )


@router.post("/utf8-probe", response_model=Utf8ProbeResponse)
def utf8_probe(
    body: Utf8ProbeRequest,
    engine: Engine = Depends(get_engine),
) -> Utf8ProbeResponse:
    with engine.connect() as connection:
        stored = connection.execute(text("SELECT CAST(:t AS text)"), {"t": body.text}).scalar()
    if not isinstance(stored, str):
        stored = str(stored)
    return Utf8ProbeResponse(
        sent=body.text,
        stored=stored,
        round_trip_ok=body.text == stored,
        nfc_normalized=body.text == unicodedata.normalize("NFC", body.text),
    )
