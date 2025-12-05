
# Imports handled by conftest.py
import pytest
from fastapi.testclient import TestClient

from alerting_notification_service.main import app


@pytest.mark.alerting_regression
@pytest.mark.unit
def test_health_and_metrics_endpoints():
    # TestClient in FastAPI 0.104.1 uses deprecated httpx app= shortcut
    # This will be fixed by upgrading FastAPI/Starlette to versions compatible with httpx>=0.27
    with TestClient(app) as client:
        health = client.get("/healthz")
        assert health.status_code == 200
        payload = health.json()
        assert payload["status"] == "UP"
        assert "stream_subscribers" in payload

        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        assert b"alerting_service" in metrics.content

