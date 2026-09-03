from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import Settings
from ..models import Stock
from ..providers.market.base import MarketDataProvider
from ..providers.market.mock import MockMarketDataProvider
from ..providers.market.oanor import OanorProvider
from ..providers.market_data import Bar, Quote, UnsupportedSymbolError, Volume
from ..repositories.market_data import upsert_bars


def get_provider(settings: Settings) -> MarketDataProvider:
    if settings.market_data_provider == "mock":
        return MockMarketDataProvider(settings)
    if settings.market_data_provider == "oanor":
        return OanorProvider(settings)
    raise ValueError(f"Unsupported market data provider: {settings.market_data_provider}")


def _get_stock(session: Session, symbol: str) -> Stock:
    stock = session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))
    if stock is None:
        raise UnsupportedSymbolError(f"Unknown stock: {symbol}")
    return stock


def get_quote(session: Session, settings: Settings, symbol: str) -> Quote | None:
    quote = get_provider(settings).get_quote(symbol)
    if quote is None:
        return None
    _get_stock(session, symbol)
    return quote


def get_historical_prices(
    session: Session,
    settings: Settings,
    symbol: str,
    start: datetime,
    end: datetime,
    interval: str = "1d",
) -> list[Bar]:
    provider = get_provider(settings)
    bars = provider.get_historical_prices(symbol, start, end, interval)
    if bars:
        stock = _get_stock(session, symbol)
        upsert_bars(session, stock, bars)
    return bars


def get_volume(session: Session, settings: Settings, symbol: str) -> Volume | None:
    return get_provider(settings).get_volume(symbol)
