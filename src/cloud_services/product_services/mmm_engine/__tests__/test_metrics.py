from fastapi.testclient import TestClient

from cloud_services.product_services.mmm_engine.main import app


client = TestClient(app)


def test_metrics_endpoint_accessible():
    response = client.get("/v1/mmm/metrics")
    assert response.status_code == 200
    assert "mmm" in response.text

