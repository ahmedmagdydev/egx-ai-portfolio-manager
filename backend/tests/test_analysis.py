import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.fixture
def analysis_client():
    app = create_app()
    with TestClient(app) as client:
        with app.state.engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE ai_analysis_logs, document_chunks, documents, "
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
def test_analyze_stock_returns_structured_response(analysis_client: TestClient) -> None:
    response = analysis_client.post(
        "/api/analysis/stock/COMI",
        json={"include_portfolio_context": True, "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "COMI"
    assert body["recommendation"] in [
        "BUY",
        "ACCUMULATE",
        "HOLD",
        "REDUCE",
        "SELL",
        "WATCH",
    ]
    assert 0 <= body["confidence"] <= 100
    assert body["valuation_assessment"]
    assert body["fundamental_assessment"]
    assert body["technical_assessment"]
    assert body["portfolio_assessment"]
    assert body["data_as_of"]
    assert body["sources"]


@pytest.mark.integration
def test_analyze_stock_unknown_symbol_returns_422(analysis_client: TestClient) -> None:
    response = analysis_client.post(
        "/api/analysis/stock/UNKNOWN",
        json={"include_portfolio_context": False, "language": "en"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "UNKNOWN_STOCK"


@pytest.mark.integration
def test_analyze_stock_arabic_returns_arabic_reasons(analysis_client: TestClient) -> None:
    response = analysis_client.post(
        "/api/analysis/stock/COMI",
        json={"include_portfolio_context": False, "language": "ar"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "ar"
    assert len(body["reasons_ar"]) > 0


@pytest.mark.integration
def test_analyze_portfolio_returns_structured_response(analysis_client: TestClient) -> None:
    response = analysis_client.post(
        "/api/analysis/portfolio",
        json={"language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["overall_recommendation"]
    assert 0 <= body["overall_confidence"] <= 100
    assert body["concentration_risk"]
    assert body["sector_exposure"]
    assert body["cash_position"]
    assert "holdings" in body
