
# Imports handled by conftest.py
from fastapi.testclient import TestClient

import pytest

from mmm_engine.main import app


client = TestClient(app)


@pytest.mark.unit
def test_metrics_endpoint_accessible():
    """Test that metrics endpoint is accessible and returns Prometheus format."""
    response = client.get("/v1/mmm/metrics")
    assert response.status_code == 200
    # Metrics endpoint may return empty string if no metrics registered yet
    # This is valid Prometheus behavior - empty response is acceptable
    assert response.headers.get("content-type", "").startswith("text/plain")

