from datetime import datetime


def test_live(client):
    response = client.get("/health/live")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ok"
    assert body["service"] == "egx-api"
    assert body["version"] == "0.0.1"
    assert body["checks"] == {}
    assert body["timestamp"].endswith("Z") or body["timestamp"].endswith("+00:00")
    datetime.fromisoformat(body["timestamp"].replace("Z", "+00:00"))
