import httpx
from fastapi.testclient import TestClient

from app.main import create_app


def test_ollama_success(monkeypatch):
    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def get(self, url):
            return httpx.Response(200, json={"models": [{"name": "qwen3.5:9b"}]})

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: MockClient())
    with TestClient(create_app()) as client:
        response = client.get("/health/ollama")
    assert response.status_code == 200
    assert response.json()["checks"]["models"]["qwen3.5:9b"]["present"] is True


def test_ollama_unavailable(monkeypatch):
    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

        async def get(self, url):
            raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: MockClient())
    with TestClient(create_app()) as client:
        response = client.get("/health/ollama")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "OLLAMA_UNAVAILABLE"
