import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import create_app


@pytest.fixture
def documents_client():
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


def _ingest(documents_client: TestClient, payload: dict) -> dict:
    response = documents_client.post("/api/documents", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.mark.integration
def test_ingest_and_retrieve_documents(documents_client: TestClient) -> None:
    payload = {
        "symbol": "COMI",
        "document_type": "COMPANY_ANNOUNCEMENT",
        "title": "Q4 2024 Earnings Announcement",
        "language": "en",
        "content": "The bank reported net income of EGP 11.5 billion for 2024. " * 10,
        "source": "mock",
        "source_url": "https://example.com/comi-q4-2024",
        "published_at": "2025-02-20T08:00:00Z",
    }
    body = _ingest(documents_client, payload)
    assert body["symbol"] == "COMI"
    assert body["status"] == "indexed"
    assert body["chunk_count"] > 0

    response = documents_client.get("/api/documents")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["title"] == payload["title"]


@pytest.mark.integration
def test_document_search_returns_results(documents_client: TestClient) -> None:
    payload = {
        "symbol": "COMI",
        "document_type": "COMPANY_ANNOUNCEMENT",
        "title": "Annual Report 2024",
        "language": "en",
        "content": "Commercial International Bank achieved strong revenue growth in 2024. " * 20,
        "source": "mock",
        "published_at": "2025-03-01T08:00:00Z",
    }
    _ingest(documents_client, payload)
    response = documents_client.post(
        "/api/documents/search",
        json={"query": "revenue growth", "symbol": "COMI", "top_k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) > 0
    assert body["results"][0]["document"]["symbol"] == "COMI"


@pytest.mark.integration
def test_document_search_respects_as_of(documents_client: TestClient) -> None:
    _ingest(
        documents_client,
        {
            "symbol": "COMI",
            "document_type": "COMPANY_ANNOUNCEMENT",
            "title": "Old Announcement",
            "language": "en",
            "content": "Old disclosure content. " * 20,
            "source": "mock",
            "published_at": "2024-01-01T08:00:00Z",
        },
    )
    _ingest(
        documents_client,
        {
            "symbol": "COMI",
            "document_type": "COMPANY_ANNOUNCEMENT",
            "title": "Future Announcement",
            "language": "en",
            "content": "Future disclosure content. " * 20,
            "source": "mock",
            "published_at": "2025-12-01T08:00:00Z",
        },
    )
    response = documents_client.post(
        "/api/documents/search",
        json={"query": "disclosure", "symbol": "COMI", "as_of": "2025-06-01T00:00:00Z", "top_k": 5},
    )
    assert response.status_code == 200
    titles = {r["document"]["title"] for r in response.json()["results"]}
    assert "Old Announcement" in titles
    assert "Future Announcement" not in titles
