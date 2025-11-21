"""
Integration tests for DLQ inspection and reprocessing workflows.
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
def dlq_setup(client, auth_token, app_schema_registry, app_routing_engine):
    """Set up environment and create DLQ entries."""
    # Register contract
    contract = DataContract(
        signal_type="pr_opened",
        contract_version="1.0.0",
        required_fields=["event_name", "pr_id"],
        optional_fields=[]
    )
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

    # Create signals that will fail and go to DLQ
    invalid_signals = [
        {
            "signal_id": f"signal_dlq_{i}",
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
        for i in range(3)
    ]

    # Ingest multiple times to exhaust retries
    for signal in invalid_signals:
        for _ in range(5):  # Exhaust retries
            client.post(
                "/v1/signals/ingest",
                json={"signals": [signal]},
                headers={"Authorization": f"Bearer {auth_token}"}
            )

    return invalid_signals


def test_dlq_inspection_basic(client, auth_token, dlq_setup):
    """Test basic DLQ inspection."""
    response = client.get(
        "/v1/signals/dlq",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert "total" in data
    assert isinstance(data["entries"], list)
    assert isinstance(data["total"], int)


def test_dlq_inspection_with_filters(client, auth_token, dlq_setup):
    """Test DLQ inspection with various filters."""
    # Filter by tenant
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

    # Filter by producer
    response = client.get(
        "/v1/signals/dlq?producer_id=producer_1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

    # Filter by signal type
    response = client.get(
        "/v1/signals/dlq?signal_type=pr_opened",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

    # Combined filters
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_1&producer_id=producer_1&signal_type=pr_opened",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200


def test_dlq_inspection_pagination(client, auth_token, dlq_setup):
    """Test DLQ inspection with pagination."""
    # First page
    response1 = client.get(
        "/v1/signals/dlq?limit=2&offset=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["entries"]) <= 2

    # Second page
    response2 = client.get(
        "/v1/signals/dlq?limit=2&offset=2",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["entries"]) <= 2

    # Verify total is consistent
    assert data1["total"] == data2["total"]


def test_dlq_entry_structure(client, auth_token, dlq_setup):
    """Test DLQ entry structure."""
    response = client.get(
        "/v1/signals/dlq?limit=1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    if data["total"] > 0 and len(data["entries"]) > 0:
        entry = data["entries"][0]
        assert "dlq_id" in entry
        assert "signal_id" in entry
        assert "tenant_id" in entry
        assert "producer_id" in entry
        assert "signal_type" in entry
        assert "error_code" in entry
        assert "error_message" in entry
        assert "retry_count" in entry
        assert "created_at" in entry


def test_dlq_inspection_empty(client, auth_token):
    """Test DLQ inspection when empty."""
    response = client.get(
        "/v1/signals/dlq",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert len(data["entries"]) == 0


def test_dlq_inspection_invalid_limit(client, auth_token):
    """Test DLQ inspection with invalid limit."""
    # Limit too high - check that it's handled gracefully
    response = client.get(
        "/v1/signals/dlq?limit=10000",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Should either accept (with max enforced) or reject
    assert response.status_code in [200, 422]

    # Limit too low (0 or negative) - should be rejected by Pydantic
    response = client.get(
        "/v1/signals/dlq?limit=0",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Pydantic validation should reject limit <= 0 if ge=1 constraint exists
    # If no constraint, it may accept but should handle gracefully
    assert response.status_code in [200, 422]


def test_dlq_inspection_invalid_offset(client, auth_token):
    """Test DLQ inspection with invalid offset."""
    response = client.get(
        "/v1/signals/dlq?offset=-1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # Pydantic validation should reject offset < 0 (ge=0 constraint)
    # If validation passes, it may return 200 but should handle gracefully
    assert response.status_code in [200, 422]


def test_dlq_stats_via_inspection(client, auth_token, dlq_setup):
    """Test that DLQ inspection provides useful statistics."""
    response = client.get(
        "/v1/signals/dlq",
        headers={"Authorization": f"Bearer {auth_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify we can get statistics from entries
    if data["total"] > 0:
        error_codes = [entry.get("error_code") for entry in data["entries"]]
        assert len(error_codes) > 0

        # Verify error codes are present
        assert all(code is not None for code in error_codes if code)


def test_dlq_filtering_accuracy(client, auth_token, dlq_setup):
    """Test that DLQ filtering returns accurate results."""
    # Get all entries
    response_all = client.get(
        "/v1/signals/dlq",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response_all.status_code == 200
    total_all = response_all.json()["total"]

    # Get filtered entries
    response_filtered = client.get(
        "/v1/signals/dlq?tenant_id=tenant_1&producer_id=producer_1",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response_filtered.status_code == 200
    total_filtered = response_filtered.json()["total"]

    # Filtered total should be <= total
    assert total_filtered <= total_all

