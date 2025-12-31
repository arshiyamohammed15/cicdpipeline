from __future__ import annotations
#!/usr/bin/env python3
"""
Integration tests for Data Governance & Privacy API routes.
"""


from fastapi.testclient import TestClient

from tests.privacy_imports import import_module

main_module = import_module("main")
app = main_module.app
client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/privacy/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"


def test_classification_endpoint() -> None:
    body = {
        "tenant_id": "tenant-int",
        "data_location": "db://table.records",
        "data_content": {"credit_card": "4111111111111111"},
        "context": {"actor_id": "integration-test"},
        "classification_hints": ["financial"],
    }
    response = client.post("/privacy/v1/classification", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert payload["classification_level"] == "restricted"
    assert "financial" in payload["sensitivity_tags"]


def test_rights_request_endpoint() -> None:
    body = {
        "tenant_id": "tenant-int",
        "data_subject_id": "subject-int",
        "right_type": "access",
        "verification_data": {"email": "integration@example.com"},
        "additional_info": "integration test",
    }
    response = client.post("/privacy/v1/rights/request", json=body)
    assert response.status_code == 202
    payload = response.json()
    assert payload["request_id"]
    assert payload["next_steps"]
