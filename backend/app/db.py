from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlalchemy import Engine, create_engine

from .config import Settings


def create_db_engine(settings: Settings) -> Engine:
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": settings.health_timeout_seconds},
    )


def get_engine(request: Request) -> Engine:
    return request.app.state.engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    engine = create_db_engine(settings)
    app.state.engine = engine
    try:
        yield
    finally:
        engine.dispose()

