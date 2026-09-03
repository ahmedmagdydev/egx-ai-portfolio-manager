from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict


class TechnicalSnapshotResponse(BaseModel):
    model_config = ConfigDict(json_encoders={Decimal: str})

    symbol: str
    interval: str
    last_timestamp: datetime | None
    observations: int
    parameters: dict[str, Any]
    sma_20: Decimal | None
    sma_50: Decimal | None
    sma_200: Decimal | None
    rsi_14: Decimal | None
    macd: Decimal | None
    macd_signal: Decimal | None
    macd_histogram: Decimal | None
    latest_volume: int | None
    source: str
    freshness: str
    warnings: list[str]
