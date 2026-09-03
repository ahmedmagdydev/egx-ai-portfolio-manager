from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..ai.schemas import ToolDefinition
from ..config import Settings
from ..tools.schemas import (
    EmptyArgs,
    FinancialSnapshotArgs,
    HistoricalPricesArgs,
    LatestNewsArgs,
    SearchDocumentsArgs,
    SymbolArgs,
    pydantic_to_json_schema,
)
from . import domain_adapters


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    version: str
    callable: Callable[..., dict]


def _wrap(
    model: type[BaseModel], fn: Callable[..., dict]
) -> Callable[[dict, Session, Settings], dict]:
    def wrapped(raw: dict, session: Session, settings: Settings) -> dict:
        validated = model(**raw)
        return fn(session, settings, **validated.model_dump(exclude_none=False))
    return wrapped


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        fn: Callable[..., dict],
        version: str = "1.0",
    ) -> None:
        self._tools[name] = Tool(
            name=name,
            description=description,
            input_schema=pydantic_to_json_schema(input_model),
            version=version,
            callable=_wrap(input_model, fn),
        )

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_definitions(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name=tool.name,
                description=tool.description,
                input_schema=tool.input_schema,
                version=tool.version,
            )
            for tool in self._tools.values()
        ]

    def tool_names(self) -> set[str]:
        return set(self._tools.keys())


_registry = ToolRegistry()
_registry.register(
    "get_portfolio",
    "Return the current portfolio summary, including holdings and allocation.",
    EmptyArgs,
    domain_adapters.get_portfolio,
)
_registry.register(
    "get_position",
    "Return the current position (share quantity) for a given stock symbol.",
    SymbolArgs,
    domain_adapters.get_position,
)
_registry.register(
    "get_quote",
    "Return the latest market quote for a stock symbol, with freshness and source.",
    SymbolArgs,
    domain_adapters.get_quote_adapter,
)
_registry.register(
    "get_historical_prices",
    "Return historical OHLCV bar count and range for a symbol over a number of days.",
    HistoricalPricesArgs,
    domain_adapters.get_historical_prices_adapter,
)
_registry.register(
    "get_financial_snapshot",
    "Return the latest financial snapshot (P/E, P/B, ROE, etc.) for a symbol.",
    FinancialSnapshotArgs,
    domain_adapters.get_financial_snapshot_adapter,
)
_registry.register(
    "get_technical_indicators",
    "Return technical indicators (SMA, RSI, MACD) for a symbol.",
    SymbolArgs,
    domain_adapters.get_technical_indicators_adapter,
)
_registry.register(
    "search_documents",
    "Search the document store for evidence relevant to a query, optionally filtered by symbol.",
    SearchDocumentsArgs,
    domain_adapters.search_documents_adapter,
)
_registry.register(
    "get_latest_news",
    "Return the most recent NEWS documents, optionally filtered by symbol.",
    LatestNewsArgs,
    domain_adapters.get_latest_news_adapter,
)
_registry.register(
    "calculate_portfolio_allocation",
    "Calculate current portfolio allocation by symbol.",
    EmptyArgs,
    domain_adapters.calculate_portfolio_allocation_adapter,
)
_registry.register(
    "calculate_sector_allocation",
    "Calculate current portfolio allocation by sector.",
    EmptyArgs,
    domain_adapters.calculate_sector_allocation_adapter,
)


def get_tool_registry() -> ToolRegistry:
    return _registry
