import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

FIXTURE_PATH = Path(__file__).with_name("fixtures") / "mock_financials.json"


class MockFinancialDataProvider:
    def __init__(self, fixture_path: Path = FIXTURE_PATH):
        self.fixture_path = fixture_path

    def _load(self) -> dict[str, list[dict[str, Any]]]:
        return json.loads(self.fixture_path.read_text(encoding="utf-8"))

    @staticmethod
    def _coerce_decimals(record: dict[str, Any]) -> dict[str, Any]:
        numeric = {
            "revenue",
            "gross_profit",
            "operating_profit",
            "net_income",
            "eps",
            "assets",
            "liabilities",
            "equity",
            "cash",
            "operating_cash_flow",
            "investing_cash_flow",
            "financing_cash_flow",
            "shares_outstanding",
            "dividends_per_share",
        }
        return {
            key: Decimal(value) if key in numeric and value is not None else value
            for key, value in record.items()
        }

    def get_statements(
        self,
        symbol: str,
        *,
        as_of: datetime | None = None,
    ) -> list[dict[str, Any]]:
        records = self._load().get(symbol.upper(), [])
        current = as_of or datetime.now(UTC)
        return [
            self._coerce_decimals(record)
            for record in records
            if datetime.fromisoformat(record["published_at"].replace("Z", "+00:00")) <= current
        ]
