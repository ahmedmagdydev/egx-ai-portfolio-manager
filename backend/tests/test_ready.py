from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_engine
from app.main import create_app


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class FakeConnection:
    def __init__(self, fail=False):
        self.fail = fail

    def __enter__(self):
        if self.fail:
            raise OperationalError("connect", {}, Exception("down"))
        return self

    def __exit__(self, *_):
        return None

    def execute(self, statement, parameters=None):
        if "SELECT 1" in str(statement):
            return FakeResult(1)
        return FakeResult("0.8.5")


class FakeEngine:
    def __init__(self, fail=False):
        self.fail = fail

    def connect(self):
        return FakeConnection(self.fail)


def test_ready_success():
    app = create_app()
    app.dependency_overrides[get_engine] = lambda: FakeEngine()
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"]["pgvector"]["status"] == "ok"


def test_ready_failure_does_not_leak_credentials():
    app = create_app()
    app.dependency_overrides[get_engine] = lambda: FakeEngine(fail=True)
    with TestClient(app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 503
    body = response.text
    assert response.json()["detail"]["code"] == "DB_UNAVAILABLE"
    assert "change_me" not in body
    assert "postgresql" not in body
