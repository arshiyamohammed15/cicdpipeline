"""
Integration tests for multi-tenant isolation scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, Plane, ProducerRegistration,
    DataContract
)


# Client fixture is provided by tests/sin/integration/conftest.py


@pytest.fixture
def multi_tenant_setup(client, app_iam, app_schema_registry):
    """Set up multiple tenants with producers."""
    tenants = ["tenant_1", "tenant_2", "tenant_3"]
    tokens = {}

    for tenant_id in tenants:
        token = f"token_{tenant_id}"
        app_iam.register_token(
            token,
            {"tenant_id": tenant_id, "producer_id": f"producer_{tenant_id}"},
            expires_in_seconds=3600
        )
        tokens[tenant_id] = token

        # Register contract for each tenant (only once, contracts are shared)
        if tenant_id == tenants[0]:  # Only register once
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

        # Register producer for each tenant
        producer = ProducerRegistration(
            producer_id=f"producer_{tenant_id}",
            name=f"Producer {tenant_id}",
            plane=Plane.EDGE,
            owner="test_owner",
            allowed_signal_kinds=[SignalKind.EVENT],
            allowed_signal_types=["pr_opened"],
            contract_versions={"pr_opened": "1.0.0"}
        )

        response = client.post(
            "/v1/producers/register",
            json={"producer": producer.model_dump()},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201

    return tokens


def test_tenant_isolation_ingestion(client, multi_tenant_setup):
    """Test that tenants can only ingest signals for their own tenant."""
    token_tenant1 = multi_tenant_setup["tenant_1"]

    # Tenant 1 tries to send signal with tenant_1 (should work)
    signal_own = {
        "signal_id": "signal_tenant1_own",
        "tenant_id": "tenant_1",
        "environment": "dev",
        "producer_id": "producer_tenant_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {"event_name": "pr_opened", "pr_id": 123},
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal_own]},
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response.status_code == 200
    data = response.json()
    # May be rejected if producer_id doesn't match, but tenant check should pass

    # Tenant 1 tries to send signal with tenant_2 (should fail)
    signal_other = {
        "signal_id": "signal_tenant1_other",
        "tenant_id": "tenant_2",  # Different tenant
        "environment": "dev",
        "producer_id": "producer_tenant_1",
        "signal_kind": "event",
        "signal_type": "pr_opened",
        "occurred_at": datetime.utcnow().isoformat(),
        "ingested_at": datetime.utcnow().isoformat(),
        "payload": {"event_name": "pr_opened", "pr_id": 123},
        "schema_version": "1.0.0"
    }

    response = client.post(
        "/v1/signals/ingest",
        json={"signals": [signal_other]},
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["status"] in ["rejected", "dlq"]
    if data["results"][0].get("error_code"):
        assert "TENANT_ISOLATION" in data["results"][0]["error_code"]


def test_tenant_isolation_dlq(client, multi_tenant_setup):
    """Test that tenants can only access their own DLQ entries."""
    token_tenant1 = multi_tenant_setup["tenant_1"]
    token_tenant2 = multi_tenant_setup["tenant_2"]

    # Tenant 1 tries to access tenant_2's DLQ
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_2",
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response.status_code == 403  # Forbidden

    # Tenant 1 can access their own DLQ
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_1",
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response.status_code == 200

    # Tenant 2 can access their own DLQ
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_2",
        headers={"Authorization": f"Bearer {token_tenant2}"}
    )
    assert response.status_code == 200


def test_tenant_isolation_producer_registration(client, multi_tenant_setup):
    """Test that producer registration is tenant-aware."""
    token_tenant1 = multi_tenant_setup["tenant_1"]

    # Tenant 1 registers a producer
    producer = {
        "producer_id": "producer_tenant1_new",
        "name": "New Producer Tenant 1",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["pr_opened"],
        "contract_versions": {"pr_opened": "1.0.0"}
    }

    response = client.post(
        "/v1/producers/register",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response.status_code == 201

    # Producer should be accessible by tenant 1
    response = client.get(
        "/v1/producers/producer_tenant1_new",
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response.status_code == 200


def test_concurrent_tenant_operations(client, multi_tenant_setup):
    """Test concurrent operations from multiple tenants."""
    import concurrent.futures

    def ingest_for_tenant(tenant_id):
        token = multi_tenant_setup[tenant_id]
        signal = {
            "signal_id": f"signal_{tenant_id}_concurrent",
            "tenant_id": tenant_id,
            "environment": "dev",
            "producer_id": f"producer_{tenant_id}",
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
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.status_code == 200

    # Run concurrent operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(ingest_for_tenant, tenant_id)
            for tenant_id in ["tenant_1", "tenant_2", "tenant_3"]
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed
    assert all(results)


def test_tenant_data_separation(client, multi_tenant_setup):
    """Test that tenant data is properly separated."""
    token_tenant1 = multi_tenant_setup["tenant_1"]
    token_tenant2 = multi_tenant_setup["tenant_2"]

    # Tenant 1 ingests signals
    signals_tenant1 = [
        {
            "signal_id": f"signal_tenant1_{i}",
            "tenant_id": "tenant_1",
            "environment": "dev",
            "producer_id": "producer_tenant_1",
            "signal_kind": "event",
            "signal_type": "pr_opened",
            "occurred_at": datetime.utcnow().isoformat(),
            "ingested_at": datetime.utcnow().isoformat(),
            "payload": {"event_name": "pr_opened", "pr_id": i},
            "schema_version": "1.0.0"
        }
        for i in range(5)
    ]

    response1 = client.post(
        "/v1/signals/ingest",
        json={"signals": signals_tenant1},
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response1.status_code == 200

    # Tenant 2 ingests signals
    signals_tenant2 = [
        {
            "signal_id": f"signal_tenant2_{i}",
            "tenant_id": "tenant_2",
            "environment": "dev",
            "producer_id": "producer_tenant_2",
            "signal_kind": "event",
            "signal_type": "pr_opened",
            "occurred_at": datetime.utcnow().isoformat(),
            "ingested_at": datetime.utcnow().isoformat(),
            "payload": {"event_name": "pr_opened", "pr_id": i},
            "schema_version": "1.0.0"
        }
        for i in range(5)
    ]

    response2 = client.post(
        "/v1/signals/ingest",
        json={"signals": signals_tenant2},
        headers={"Authorization": f"Bearer {token_tenant2}"}
    )
    assert response2.status_code == 200

    # Verify tenant 1 cannot see tenant 2's data
    response = client.get(
        "/v1/signals/dlq?tenant_id=tenant_2",
        headers={"Authorization": f"Bearer {token_tenant1}"}
    )
    assert response.status_code == 403  # Forbidden

