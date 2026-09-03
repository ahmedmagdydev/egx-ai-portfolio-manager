from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SymbolArgs(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)


class HistoricalPricesArgs(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    days: int = Field(default=30, ge=1, le=1000)


class FinancialSnapshotArgs(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    as_of: datetime | None = None


class SearchDocumentsArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    symbol: str | None = None
    document_type: str | None = None
    as_of: datetime | None = None
    top_k: int = Field(default=5, ge=1, le=50)


class LatestNewsArgs(BaseModel):
    symbol: str | None = None
    limit: int = Field(default=5, ge=1, le=50)


class EmptyArgs(BaseModel):
    pass


def pydantic_to_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    return model.model_json_schema()
