from datetime import datetime
from typing import Protocol

from ...domain.portfolio import PriceQuote


class MarketDataProvider(Protocol):
    def get_quotes(
        self,
        symbols: list[str],
        *,
        now: datetime | None = None,
    ) -> dict[str, PriceQuote | None]:
        ...
