import subprocess
import sys

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.integration
def test_integration_database_and_health():
    for _ in range(2):
        subprocess.run(
            [sys.executable, "-m", "alembic", "-c", "alembic.ini", "upgrade", "head"],
            cwd="backend",
            check=True,
        )
    with TestClient(app) as client:
        ready = client.get("/health/ready")
        assert ready.status_code == 200
        assert ready.json()["checks"]["pgvector"]["version"]
        text = "محفظة الأسهم — EGX portfolio ✓"
        probe = client.post("/health/utf8-probe", json={"text": text})
        assert probe.json()["round_trip_ok"] is True
