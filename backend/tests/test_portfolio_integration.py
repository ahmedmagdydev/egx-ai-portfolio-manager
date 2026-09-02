from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.mark.integration
def test_portfolio_api_fixture_and_validation() -> None:
    app = create_app()
    with TestClient(app) as client:
        with app.state.engine.begin() as connection:
            connection.execute(
                text("TRUNCATE price_snapshots, transactions, stocks RESTART IDENTITY CASCADE")
            )
        for symbol, name, sector in [
            ("COMI", "Commercial International Bank", "Banks"),
            ("HRHO", "EFG Holding", "Financial Services"),
        ]:
            response = client.post(
                "/portfolio/stocks",
                json={"symbol": symbol, "name_en": name, "sector": sector},
            )
            assert response.status_code == 201
        duplicate = client.post(
            "/portfolio/stocks",
            json={"symbol": "comi", "name_en": "Duplicate"},
        )
        assert duplicate.status_code == 409
        assert duplicate.json()["code"] == "STOCK_EXISTS"

        transactions = [
            {"type": "DEPOSIT", "amount": "100000", "executed_at": "2025-01-01T09:00:00Z"},
            {
                "type": "BUY", "symbol": "COMI", "quantity": "100", "price": "50",
                "fees": "25", "executed_at": "2025-01-02T09:00:00Z",
            },
            {
                "type": "BUY", "symbol": "COMI", "quantity": "100", "price": "60",
                "fees": "30", "executed_at": "2025-01-03T09:00:00Z",
            },
            {
                "type": "SELL", "symbol": "COMI", "quantity": "50", "price": "70",
                "fees": "20", "executed_at": "2025-01-04T09:00:00Z",
            },
            {
                "type": "BUY", "symbol": "HRHO", "quantity": "200", "price": "20",
                "fees": "10", "executed_at": "2025-01-05T09:00:00Z",
            },
            {
                "type": "DIVIDEND", "symbol": "COMI", "amount": "150",
                "executed_at": "2025-01-06T09:00:00Z",
            },
            {"type": "WITHDRAWAL", "amount": "1000", "executed_at": "2025-01-07T09:00:00Z"},
        ]
        for payload in transactions:
            assert client.post("/portfolio/transactions", json=payload).status_code == 201

        holdings = client.get("/portfolio/holdings")
        assert holdings.status_code == 200
        body = holdings.json()
        comi = next(item for item in body["holdings"] if item["symbol"] == "COMI")
        hrho = next(item for item in body["holdings"] if item["symbol"] == "HRHO")
        assert comi["avg_cost"] == "55.2750"
        assert comi["total_cost"] == "8291.25"
        assert comi["realized_pnl"] == "866.25"
        assert body["summary"]["cash"] == "87565.00"
        assert hrho["price"]["status"] == "unavailable"

        oversell = client.post(
            "/portfolio/transactions",
            json={
                "type": "SELL",
                "symbol": "COMI",
                "quantity": "151",
                "price": "70",
                "executed_at": datetime.now(UTC).isoformat(),
            },
        )
        assert oversell.status_code == 422
        assert oversell.json()["code"] == "INSUFFICIENT_HOLDINGS"

        page = client.get("/portfolio/transactions?limit=2&offset=2")
        assert page.status_code == 200
        assert page.json()["total"] == 7
        assert len(page.json()["items"]) == 2
