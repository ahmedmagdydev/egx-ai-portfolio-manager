import json
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from starlette.responses import JSONResponse

from . import __version__
from .config import Settings
from .db import lifespan
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
    app.include_router(health_router)
    return app


app = create_app()
