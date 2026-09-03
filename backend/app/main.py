import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from . import __version__
from .api.ai import router as ai_router
from .api.analysis import router as analysis_router
from .api.documents import router as documents_router
from .api.financial import router as financial_router
from .api.market_data import router as market_data_router
from .api.portfolio import router as portfolio_router
from .api.risk import router as risk_router
from .api.settings import router as settings_router
from .api.technical import router as technical_router
from .config import Settings
from .db import lifespan
from .domain.portfolio import PortfolioError
from .health import router as health_router
from .logging import configure_logging
from .middleware import CorrelationIdMiddleware


class UTF8JSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or Settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def app_lifespan(app: FastAPI):
        async with lifespan(app):
            yield

    app = FastAPI(
        title="EGX AI Portfolio Manager API",
        version=__version__,
        lifespan=app_lifespan,
        default_response_class=UTF8JSONResponse,
    )
    app.state.settings = app_settings
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(portfolio_router)
    app.include_router(market_data_router)
    app.include_router(financial_router)
    app.include_router(technical_router)
    app.include_router(documents_router)
    app.include_router(ai_router)
    app.include_router(analysis_router)
    app.include_router(risk_router)
    app.include_router(settings_router)

    @app.exception_handler(PortfolioError)
    async def portfolio_error_handler(_: Request, exc: PortfolioError) -> JSONResponse:
        details = {}
        for key in ("symbol", "held", "requested"):
            if hasattr(exc, key):
                details[key] = str(getattr(exc, key))
        return JSONResponse(
            status_code=422,
            content={"code": exc.code, "message": str(exc), "details": details or None},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                {
                    "code": "INVALID_TRANSACTION",
                    "message": "Request validation failed",
                    "details": {"errors": exc.errors()},
                }
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": "HTTP_ERROR", "message": str(exc.detail), "details": None},
        )
    return app


app = create_app()
