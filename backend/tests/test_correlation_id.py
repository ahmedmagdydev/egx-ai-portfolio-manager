def test_correlation_id_is_echoed(client):
    response = client.get("/health/live", headers={"X-Correlation-ID": "probe-123"})
    assert response.headers["X-Correlation-ID"] == "probe-123"
