import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.fixture
def technical_client():
    app = create_app()
    with TestClient(app) as client:
        with app.state.engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE financial_statements, stock_prices, "
                    "price_snapshots, transactions, stocks RESTART IDENTITY CASCADE"
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
def test_technical_snapshot(technical_client: TestClient) -> None:
    _create_stock(technical_client, "COMI", "Commercial International Bank")
    response = technical_client.get("/api/stocks/COMI/technical")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "COMI"
    assert body["interval"] == "1d"
    assert body["observations"] >= 200  # long COMI history fixture supplies >= 200 bars
    assert body["sma_20"] is not None
    assert body["sma_50"] is not None
    assert body["sma_200"] is not None
    assert body["rsi_14"] is not None
    assert body["macd"] is not None
    assert body["macd_signal"] is not None


@pytest.mark.integration
def test_technical_snapshot_unknown_stock(technical_client: TestClient) -> None:
    response = technical_client.get("/api/stocks/UNKNOWN/technical")
    assert response.status_code == 404
    assert response.json()["code"] == "UNKNOWN_STOCK"


@pytest.mark.integration
def test_technical_snapshot_unsupported_interval(technical_client: TestClient) -> None:
    _create_stock(technical_client, "COMI", "Commercial International Bank")
    response = technical_client.get("/api/stocks/COMI/technical?interval=1h")
    assert response.status_code == 422
    assert response.json()["code"] == "UNSUPPORTED_INTERVAL"


@pytest.mark.integration
def test_technical_snapshot_insufficient_history(technical_client: TestClient) -> None:
    _create_stock(technical_client, "SWDY", "Sidi Kerir Petrochemicals")
    response = technical_client.get("/api/stocks/SWDY/technical")
    assert response.status_code == 200
    body = response.json()
    assert body["observations"] < 20
    assert body["sma_200"] is None
    assert any("Insufficient history" in warning for warning in body["warnings"])
