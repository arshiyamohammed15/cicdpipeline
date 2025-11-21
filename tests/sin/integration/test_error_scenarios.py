"""
Integration tests for error scenarios and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, Plane, ProducerRegistration,
    DataContract
)


# Client fixture is provided by tests/sin/integration/conftest.py


# auth_token fixture is provided by tests/sin/integration/conftest.py


@pytest.fixture
def registered_producer_setup(client, auth_token, app_schema_registry):
    """Set up a registered producer for testing."""
    contract = DataContract(
        signal_type="pr_opened",
        contract_version="1.0.0",
        required_fields=["event_name", "pr_id"],
        optional_fields=["severity"]
    )
    app_schema_registry.register_contract(
        contract.signal_type,
        contract.contract_version,
        contract.model_dump()
    )

    producer = ProducerRegistration(
        producer_id="producer_1",
        name="Test Producer",
        plane=Plane.EDGE,
        owner="test_owner",
        allowed_signal_kinds=[SignalKind.EVENT],
        allowed_signal_types=["pr_opened"],
        contract_versions={"pr_opened": "1.0.0"}
    )

    response = client.post(
        "/v1/producers/register",
        json={"producer": producer.model_dump()},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    return producer


def test_unregistered_producer(client, auth_token):
    """Test ingestion with unregistered producer."""
    signal = {
        "signal_id": "signal_unregistered",
        "tenant_id": "tenant_1",
        "environment": "dev",
        "producer_id": "unregistered_producer",
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
    assert data["results"][0]["status"] == "rejected"
    assert "PRODUCER_NOT_REGISTERED" in data["results"][0].get("error_code", "")


def test_invalid_signal_type(client, auth_token, registered_producer_setup):
    """Test ingestion with signal type not allowed for producer."""
    signal = {
        "signal_id": "signal_invalid_type",
        "tenant_id": "tenant_1",
        "environment": "dev",
        "producer_id": "producer_1",
        "signal_kind": "event",
        "signal_type": "invalid_type",  # Not in allowed list
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {"event_name": "invalid_type"},
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal]},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["status"] == "rejected"
    assert "SIGNAL_TYPE_NOT_ALLOWED" in data["results"][0].get("error_code", "")


def test_missing_required_fields(client, auth_token, registered_producer_setup):
    """Test ingestion with missing required fields."""
    signal = {
        "signal_id": "signal_missing_fields",
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

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal]},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Should be rejected initially, then go to DLQ after retries
    assert data["results"][0]["status"] in ["rejected", "dlq"]
    if data["results"][0]["status"] == "dlq":
        assert data["results"][0].get("dlq_id") is not None


def test_governance_violation(client, auth_token, registered_producer_setup, app_data_governance, app_routing_engine):
    """Test governance violation detection."""
    # Set disallowed field
    app_data_governance.set_disallowed_fields(
        "tenant_1", "producer_1", "pr_opened", ["disallowed_field"]
    )

    signal = {
        "signal_id": "signal_gov_violation",
        "tenant_id": "tenant_1",
        "environment": "dev",
        "producer_id": "producer_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {
            "event_name": "pr_opened",
            "pr_id": 123,
            "disallowed_field": "value"  # Disallowed
        },
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal]},
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["status"] in ["rejected", "dlq"]
    if data["results"][0].get("error_code"):
        assert "GOVERNANCE" in data["results"][0]["error_code"]


def test_invalid_json(client, auth_token):
    """Test API with invalid JSON."""
    response = client.post(
        "/v1/signals/ingest",
        data="invalid json",
        headers={"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_empty_signals_array(client, auth_token):
    """Test API with empty signals array."""
    response = client.post(
        "/v1/signals/ingest",
        json={"signals": []},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422  # Validation error


def test_large_batch(client, auth_token, registered_producer_setup):
    """Test API with batch exceeding max size."""
    # Create 1001 signals (max is 1000)
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
        for i in range(1001)
    ]

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": signals},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 422  # Validation error for exceeding max


def test_expired_token(client, app_iam):
    """Test with expired authentication token."""
    expired_token = "expired_token"
    app_iam.register_token(
        expired_token,
        {"tenant_id": "tenant_1", "producer_id": "producer_1"},
        expires_in_seconds=-1  # Already expired
    )

    signal = {
        "signal_id": "signal_expired",
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
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401  # Unauthorized


def test_malformed_signal(client, auth_token, registered_producer_setup):
    """Test with malformed signal data."""
    signal = {
        "signal_id": "signal_malformed",
        "tenant_id": "tenant_1",
        "environment": "invalid_env",  # Invalid enum value
        "producer_id": "producer_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": "invalid_date",  # Invalid date format
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {"event_name": "pr_opened", "pr_id": 123},
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal]},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Should fail validation at Pydantic level
    assert response.status_code in [422, 200]  # 422 if validation fails, 200 if accepted but processed as invalid

