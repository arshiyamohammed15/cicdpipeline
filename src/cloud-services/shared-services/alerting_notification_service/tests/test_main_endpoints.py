from fastapi.testclient import TestClient

from ..main import app


def test_health_and_metrics_endpoints():
    with TestClient(app) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        payload = health.json()
        assert payload["status"] == "UP"
        assert "stream_subscribers" in payload

        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert b"alerting_service" in metrics.content

