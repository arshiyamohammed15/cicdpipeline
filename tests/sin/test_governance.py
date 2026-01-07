"""
Tests for governance - TC-SIN-003: Governance Violation, TC-SIN-008: Multi-Tenant Isolation.
"""

import pytest
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, ErrorCode, registered_producer
)


@pytest.mark.unit
def test_tc_sin_003_governance_violation(ingestion_service, registered_producer, mock_data_governance):
    """TC-SIN-003: Governance violation is detected and handled."""
    # Set disallowed field
    mock_data_governance.set_disallowed_fields(
        "tenant_1", "producer_1", "pr_opened", ["disallowed_field"]
    )

    signal = SignalEnvelope(
        signal_id="signal_gov_violation",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened", "pr_id": 123, "disallowed_field": "value"},
        schema_version="1.0.0"
    )

    result = ingestion_service.ingest_signal(signal)
    # Should be rejected or DLQ due to governance violation
    assert result.status.value in ["rejected", "dlq"]
    if result.error_code:
        assert result.error_code == ErrorCode.GOVERNANCE_VIOLATION


@pytest.mark.unit
def test_tc_sin_008_multi_tenant_isolation(ingestion_service, registered_producer):
    """TC-SIN-008: Multi-tenant isolation is enforced."""
    signal_tenant1 = SignalEnvelope(
        signal_id="signal_tenant1",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened", "pr_id": 123},
        schema_version="1.0.0"
    )

    # Try to ingest with wrong tenant
    result = ingestion_service.ingest_signal(signal_tenant1, tenant_id="tenant_2")
    assert result.status.value == "rejected"
    assert result.error_code == ErrorCode.TENANT_ISOLATION_VIOLATION

