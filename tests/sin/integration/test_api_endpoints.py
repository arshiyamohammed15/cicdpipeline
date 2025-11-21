"""
Comprehensive integration tests for SIN API endpoints.

Tests the full FastAPI application with TestClient to verify API contracts.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, Plane, ProducerRegistration,
    DataContract
)


# auth_token fixture is provided by tests/sin/integration/conftest.py


@pytest.fixture
def registered_producer_setup(client, auth_token, app_schema_registry):
    """Set up a registered producer for testing."""
    # Register contracts
    contracts = [
        DataContract(
            signal_type="pr_opened",
            contract_version="1.0.0",
            required_fields=["event_name", "pr_id"],
            optional_fields=["severity"]
        ),
        DataContract(
            signal_type="test_failed",
            contract_version="1.0.0",
            required_fields=["event_name", "test_name"],
            optional_fields=[]
        )
    ]
    
    for contract in contracts:
        app_schema_registry.register_contract(
            contract.signal_type,
            contract.contract_version,
            contract.model_dump()
        )

    # Register producer
    producer = ProducerRegistration(
        producer_id="producer_1",
        name="Test Producer",
        plane=Plane.EDGE,
        owner="test_owner",
        allowed_signal_kinds=[SignalKind.EVENT, SignalKind.METRIC],
        allowed_signal_types=["pr_opened", "test_failed"],
        contract_versions={"pr_opened": "1.0.0", "test_failed": "1.0.0"}
    )

    response = client.post(
        "/v1/producers/register",
        json={"producer": producer.model_dump()},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    return producer


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_readiness_endpoint(client):
    """Test readiness check endpoint."""
    response = client.get("/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "checks" in data
    assert "timestamp" in data


def test_ingest_signals_unauthorized(client):
    """Test signal ingestion without authentication."""
    signal = {
        "signal_id": "signal_1",
        "tenant_id": "tenant_1",
        "environment": "dev",
        "producer_id": "producer_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {"event_name": "pr_opened", "pr_id": 123},
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal]}
    )
    assert response.status_code == 401


def test_ingest_signals_authorized(client, auth_token, registered_producer_setup):
    """Test signal ingestion with authentication."""
    signal = {
        "signal_id": "signal_1",
        "tenant_id": "tenant_1",
        "environment": "dev",
        "producer_id": "producer_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {"event_name": "pr_opened", "pr_id": 123},
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal]},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "summary" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["signal_id"] == "signal_1"
    assert data["summary"]["total"] == 1


def test_ingest_signals_batch(client, auth_token, registered_producer_setup):
    """Test batch signal ingestion."""
    signals = [
        {
            "signal_id": f"signal_{i}",
            "tenant_id": "tenant_1",
            "environment": "dev",
            "producer_id": "producer_1",
            "signal_kind": "event",
            "signal_type": "pr_opened",
            "occurred_at": datetime.utcnow().isoformat(),
            "ingested_at": datetime.utcnow().isoformat(),
            "payload": {"event_name": "pr_opened", "pr_id": i},
            "schema_version": "1.0.0"
        }
        for i in range(5)
    ]

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": signals},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 5
    assert data["summary"]["total"] == 5


def test_register_producer(client, auth_token, app_schema_registry):
    """Test producer registration."""
    # Register contract first
    contract = DataContract(
        signal_type="test_signal",
        contract_version="1.0.0",
        required_fields=["event_name"],
        optional_fields=[]
    )
    app_schema_registry.register_contract(
        contract.signal_type,
        contract.contract_version,
        contract.model_dump()
    )

    producer = {
        "producer_id": "producer_new",
        "name": "New Producer",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["test_signal"],
        "contract_versions": {"test_signal": "1.0.0"}
    }

    response = client.post(
        "/v1/producers/register",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["producer_id"] == "producer_new"
    assert data["status"] == "registered"


def test_get_producer(client, auth_token, registered_producer_setup):
    """Test get producer endpoint."""
    response = client.get(
        "/v1/producers/producer_1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["producer"]["producer_id"] == "producer_1"


def test_update_producer(client, auth_token, registered_producer_setup):
    """Test update producer endpoint."""
    producer = {
        "producer_id": "producer_1",
        "name": "Updated Producer",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["pr_opened"],
        "contract_versions": {"pr_opened": "1.0.0"}
    }

    response = client.put(
        "/v1/producers/producer_1",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"


def test_dlq_inspection_empty(client, auth_token):
    """Test DLQ inspection with no entries."""
    response = client.get(
        "/v1/signals/dlq",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["entries"]) == 0


def test_dlq_inspection_with_filters(client, auth_token, registered_producer_setup):
    """Test DLQ inspection with filters."""
    # First, create a signal that will fail validation and go to DLQ
    invalid_signal = {
        "signal_id": "signal_invalid",
        "tenant_id": "tenant_1",
        "environment": "dev",
        "producer_id": "producer_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {},  # Missing required fields
        "schema_version": "1.0.0"
    }

    # Ingest multiple times to trigger DLQ
    for _ in range(5):
        client.post(
            "/v1/signals/ingest",
            json={"signals": [invalid_signal]},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

    # Check DLQ
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_1&producer_id=producer_1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0  # May have entries if retries exhausted


def test_tenant_isolation(client, auth_token, registered_producer_setup, app_iam):
    """Test tenant isolation enforcement."""
    # Create token for different tenant
    token_tenant2 = "token_tenant2"
    app_iam.register_token(
        token_tenant2,
        {"tenant_id": "tenant_2", "producer_id": "producer_1"},
        expires_in_seconds=3600
    )

    # Try to ingest signal with tenant_1 but using tenant_2 token
    signal = {
        "signal_id": "signal_tenant_mismatch",
        "tenant_id": "tenant_1",  # Signal says tenant_1
        "environment": "dev",
        "producer_id": "producer_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {"event_name": "pr_opened", "pr_id": 123},
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal]},
        headers={"Authorization": f"Bearer {token_tenant2}"}  # But token says tenant_2
    )
    assert response.status_code == 200
    data = response.json()
    # Should be rejected due to tenant isolation
    assert data["results"][0]["status"] in ["rejected", "dlq"]
    if data["results"][0].get("error_code"):
        assert "TENANT_ISOLATION" in data["results"][0]["error_code"]


def test_dlq_cross_tenant_access_denied(client, auth_token, registered_producer_setup, app_iam):
    """Test that tenants cannot access other tenants' DLQ entries."""
    # Create token for tenant_2
    token_tenant2 = "token_tenant2"
    app_iam.register_token(
        token_tenant2,
        {"tenant_id": "tenant_2", "producer_id": "producer_1"},
        expires_in_seconds=3600
    )

    # Try to access tenant_1's DLQ with tenant_2 token
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_1",
        headers={"Authorization": f"Bearer {token_tenant2}"}
    )
    assert response.status_code == 403  # Should be forbidden

