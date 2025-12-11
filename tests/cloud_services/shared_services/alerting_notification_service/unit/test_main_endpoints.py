
# Imports handled by conftest.py
import pytest
import httpx
from httpx import ASGITransport

from alerting_notification_service.main import app


@pytest.mark.alerting_regression
@pytest.mark.unit
def test_health_and_metrics_endpoints():
    transport = ASGITransport(app=app)
    async def _run():
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            health = await client.get("/healthz")
            assert health.status_code == 200
            payload = health.json()
            assert payload["status"] == "UP"
            assert "stream_subscribers" in payload

            metrics = await client.get("/metrics")
            assert metrics.status_code == 200
            assert metrics.content

    import asyncio
    asyncio.run(_run())

