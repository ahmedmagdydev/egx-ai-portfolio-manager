from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from .db import get_engine


def get_session(request: Request) -> Generator[Session, None, None]:
    factory = sessionmaker(bind=get_engine(request), expire_on_commit=False)
    with factory() as session:
        yield session
