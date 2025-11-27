"""
Starter tests for Data Governance & Privacy routes.
"""

def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"


def test_versioned_api_prefix_exists(test_client):
    response = test_client.get("/privacy/v1/health")
    assert response.status_code == 200


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


def test_retention_endpoint_smoke(test_client):
    payload = {
        "tenant_id": "tenant-smoke",
        "data_subject_id": "user-123",
        "data_categories": ["logs"],
        "creation_timestamp": "2024-01-01T00:00:00Z",
        "requested_action": "delete",
    }
    response = test_client.post("/privacy/v1/retention/evaluate", json=payload)
    assert response.status_code in {200, 400}


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


def test_privacy_enforcement_smoke(test_client):
    payload = {
        "tenant_id": "tenant-smoke",
        "user_id": "user-123",
        "action": "read",
        "resource": "dashboard",
        "policy_id": "policy-1",
        "context": {"channel": "api"},
    }
    response = test_client.post("/privacy/v1/compliance", json=payload)
    assert response.status_code in {200, 400}

