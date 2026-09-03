from datetime import datetime
from typing import Any, Protocol


class FinancialDataProvider(Protocol):
    def get_statements(self, symbol: str, *, as_of: datetime | None = None) -> list[dict[str, Any]]:
        """Return raw financial statement records for the symbol."""
        ...
