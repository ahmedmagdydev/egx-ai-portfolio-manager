from fastapi.testclient import TestClient
from test_ready import FakeEngine, FakeResult

from app.db import get_engine
from app.main import create_app


class Utf8Connection:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def execute(self, statement, parameters=None):
        return FakeResult(parameters["t"])


class Utf8Engine(FakeEngine):
    def connect(self):
        return Utf8Connection()


def test_utf8_probe_round_trip():
    app = create_app()
    app.dependency_overrides[get_engine] = lambda: Utf8Engine()
    text = "محفظة الأسهم — EGX portfolio ✓"
    with TestClient(app) as client:
        response = client.post("/health/utf8-probe", json={"text": text})
    assert response.status_code == 200
    assert response.json()["round_trip_ok"] is True
    assert text.encode("utf-8") in response.content
    assert b"\\u" not in response.content
