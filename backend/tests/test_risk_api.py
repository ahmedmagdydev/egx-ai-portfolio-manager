import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.fixture
def risk_client():
    app = create_app()
    with TestClient(app) as client:
        with app.state.engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE ai_analysis_logs, risk_limits, document_chunks, documents, "
                    "financial_statements, stock_prices, price_snapshots, "
                    "transactions, stocks RESTART IDENTITY CASCADE"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO stocks (id, symbol, name_en, currency, is_active, created_at) "
                    "VALUES (gen_random_uuid(), 'COMI', 'Commercial International Bank', "
                    "'EGP', true, NOW())"
                )
            )
        yield client


@pytest.mark.integration
def test_get_risk_limits_defaults(risk_client: TestClient) -> None:
    response = risk_client.get("/api/settings/risk-limits")
    assert response.status_code == 200
    body = response.json()
    assert body["max_single_position_percent"] == "25.00"


@pytest.mark.integration
def test_update_risk_limits(risk_client: TestClient) -> None:
    response = risk_client.post(
        "/api/settings/risk-limits",
        json={
            "max_single_position_percent": "20.0",
            "max_sector_exposure_percent": "35.0",
            "min_cash_percent": "15.0",
            "rebalancing_threshold_percent": "5.0",
        },
    )
    assert response.status_code == 200
    assert response.json()["max_single_position_percent"] == "20.00"


@pytest.mark.integration
def test_portfolio_risk_report_empty(risk_client: TestClient) -> None:
    response = risk_client.get("/api/risk/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert body["total_portfolio_value"] == "0"
    assert body["cash_percent"] == "0"


@pytest.mark.integration
def test_risk_summary_empty(risk_client: TestClient) -> None:
    response = risk_client.get("/api/risk/portfolio/summary")
    assert response.status_code == 200
    assert response.json()["breach_count"] == 0
