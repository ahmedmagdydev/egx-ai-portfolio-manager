import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.fixture
def financial_client():
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
def test_financial_snapshot(financial_client: TestClient) -> None:
    _create_stock(financial_client, "COMI", "Commercial International Bank")
    response = financial_client.get("/api/stocks/COMI/financials/snapshot")
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "COMI"
    assert body["period_type"] == "annual"
    assert body["scope"] == "consolidated"
    assert body["currency"] == "EGP"
    assert body["unit_scale"] == "millions"
    assert body["pe"]["status"] == "ok"
    assert body["pb"]["status"] == "ok"
    assert body["roe"]["status"] == "ok"
    assert body["roa"]["status"] == "ok"
    assert body["revenue_growth"]["status"] == "ok"
    assert body["earnings_growth"]["status"] == "ok"
    assert body["dividend_yield"]["status"] == "ok"


@pytest.mark.integration
def test_financial_snapshot_unknown_stock(financial_client: TestClient) -> None:
    response = financial_client.get("/api/stocks/UNKNOWN/financials/snapshot")
    assert response.status_code == 404
    assert response.json()["code"] == "UNKNOWN_STOCK"


@pytest.mark.integration
def test_financial_snapshot_as_of_look_ahead(financial_client: TestClient) -> None:
    _create_stock(financial_client, "COMI", "Commercial International Bank")
    as_of = "2024-03-01T00:00:00Z"
    response = financial_client.get(f"/api/stocks/COMI/financials/snapshot?as_of={as_of}")
    assert response.status_code == 200
    body = response.json()
    assert body["period_end"] == "2023-12-31T00:00:00Z"
    assert body["revenue_growth"]["status"] == "not_available"
