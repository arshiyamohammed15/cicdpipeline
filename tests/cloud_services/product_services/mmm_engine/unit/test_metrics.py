
# Imports handled by conftest.py
from fastapi.testclient import TestClient

import pytest

from mmm_engine.main import app


client = TestClient(app)


@pytest.mark.unit
def test_metrics_endpoint_accessible():
    response = client.get("/v1/mmm/metrics")
    assert response.status_code == 200
    assert response.text

