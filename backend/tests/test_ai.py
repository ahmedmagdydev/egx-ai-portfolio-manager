import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.fixture
def ai_client():
    app = create_app()
    with TestClient(app) as client:
        with app.state.engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE document_chunks, documents, financial_statements, "
                    "stock_prices, price_snapshots, transactions, stocks "
                    "RESTART IDENTITY CASCADE"
                )
            )
        yield client


@pytest.mark.integration
def test_analyze_endpoint_returns_structure(ai_client: TestClient) -> None:
    response = ai_client.post(
        "/api/ai/analyze",
        json={"message": "Analyze COMI", "language": "en"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "interpretation" in body
    assert "verified_facts" in body
    assert "missing_information" in body
    assert body["language"] == "en"
