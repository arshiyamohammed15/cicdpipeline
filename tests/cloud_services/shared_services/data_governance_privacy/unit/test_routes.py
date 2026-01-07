"""
Starter tests for Data Governance & Privacy routes.
"""

import pytest
from fastapi.testclient import TestClient

from data_governance_privacy.main import app  # type: ignore


@pytest.fixture
@pytest.mark.unit
def test_client() -> TestClient:
    """FastAPI test client for privacy service routes."""
    return TestClient(app)


@pytest.mark.unit
def test_health_endpoint(test_client):
    response = test_client.get("/privacy/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"


@pytest.mark.unit
def test_versioned_api_prefix_exists(test_client):
    response = test_client.get("/privacy/v1/config")
    assert response.status_code == 200
    assert response.json()["api_endpoints"]["health"] == "/privacy/v1/health"


@pytest.mark.unit
def test_classification_endpoint_smoke(test_client):
    payload = {
        "tenant_id": "tenant-smoke",
        "data_location": "s3://bucket/path",
        "data_content": {"sample": "data"},
        "context": {"source_system": "test"},
        "classification_hints": ["pii"],
    }
    response = test_client.post("/privacy/v1/classification", json=payload)
    assert response.status_code in {200, 400}


@pytest.mark.unit
def test_retention_endpoint_smoke(test_client):
    payload = {
        "tenant_id": "tenant-smoke",
        "data_category": "logs",
        "last_activity_months": 18,
    }
    response = test_client.post("/privacy/v1/retention/evaluate", json=payload)
    assert response.status_code in {200, 400}


@pytest.mark.unit
def test_consent_check_smoke(test_client):
    payload = {
        "tenant_id": "tenant-smoke",
        "data_subject_id": "user-123",
        "purpose": "analytics",
        "data_categories": ["usage"],
        "legal_basis": "legitimate_interest",
    }
    response = test_client.post("/privacy/v1/consent/check", json=payload)
    assert response.status_code in {200, 400}


@pytest.mark.unit
def test_privacy_enforcement_smoke(test_client):
    payload = {
        "tenant_id": "tenant-smoke",
        "user_id": "user-123",
        "action": "read",
        "resource": "dashboard",
        "policy_id": "policy-1",
        "context": {"channel": "api"},
        "classification_record": {"classification_level": "public", "sensitivity_tags": ["public"]},
    }
    response = test_client.post("/privacy/v1/compliance", json=payload)
    # 422 = validation error (endpoint exists and validates), 200 = success, 400 = bad request
    assert response.status_code in {200, 400, 422}
