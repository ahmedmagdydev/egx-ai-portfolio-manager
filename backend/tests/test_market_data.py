import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.fixture
def market_client():
    app = create_app()
    with TestClient(app) as client:
        with app.state.engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE stock_prices, price_snapshots, transactions, stocks "
                    "RESTART IDENTITY CASCADE"
                )
            )
        yield client


def _create_stock(client: TestClient, symbol: str, name_en: str = "Test") -> None:
    response = client.post(
        "/portfolio/stocks",
        json={"symbol": symbol, "name_en": name_en},
    )
    assert response.status_code == 201


@pytest.mark.integration
def test_get_quote(market_client: TestClient) -> None:
    _create_stock(market_client, "COMI", "Commercial International Bank")
    response = market_client.get("/api/stocks/COMI/quote")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "COMI"
    assert body["price"] == "72.5000"
    assert body["currency"] == "EGP"
    assert body["freshness"] in {"fresh", "stale"}


@pytest.mark.integration
def test_get_quote_unknown(market_client: TestClient) -> None:
    response = market_client.get("/api/stocks/UNKNOWN/quote")
    assert response.status_code == 404
    assert response.json()["code"] == "QUOTE_UNAVAILABLE"


@pytest.mark.integration
def test_get_history(market_client: TestClient) -> None:
    _create_stock(market_client, "COMI", "Commercial International Bank")
    start = "2025-01-13T00:00:00Z"
    end = "2025-01-15T23:59:59Z"
    response = market_client.get(f"/api/stocks/COMI/history?start={start}&end={end}&interval=1d")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "COMI"
    assert body["interval"] == "1d"
    assert len(body["items"]) == 3
    assert body["items"][0]["open"] == "71.0000"


@pytest.mark.integration
def test_get_history_invalid_range(market_client: TestClient) -> None:
    _create_stock(market_client, "COMI", "Commercial International Bank")
    response = market_client.get(
        "/api/stocks/COMI/history?start=2025-01-15T00:00:00Z&end=2025-01-13T00:00:00Z&interval=1d"
    )
    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_RANGE"


@pytest.mark.integration
def test_get_volume(market_client: TestClient) -> None:
    _create_stock(market_client, "COMI", "Commercial International Bank")
    response = market_client.get("/api/stocks/COMI/volume")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "COMI"
    assert body["volume"] == 110000
