"""
Tests for validation engine - TC-SIN-002: Schema Violation → DLQ.
"""

import pytest
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, ErrorCode, registered_producer
)


@pytest.mark.unit
def test_tc_sin_002_schema_violation_dlq(ingestion_service, registered_producer, sample_signal):
    """TC-SIN-002: Schema violation routes to DLQ."""
    # Create signal with missing required field
    invalid_signal = SignalEnvelope(
        signal_id="signal_invalid",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={},  # Missing required fields
        schema_version="1.0.0"
    )

    # Ingest signal
    result = ingestion_service.ingest_signal(invalid_signal)

    # Should be rejected initially (retry)
    assert result.status.value in ["rejected", "dlq"]
    # Retry until it goes to DLQ
    for _ in range(4):
        result = ingestion_service.ingest_signal(invalid_signal)
        if result.status.value == "dlq":
            break

    # Should eventually route to DLQ
    assert result.status.value == "dlq"
    assert result.error_code == ErrorCode.SCHEMA_VIOLATION
    assert result.dlq_id is not None


@pytest.mark.unit
def test_validation_producer_not_registered(ingestion_service, sample_signal):
    """Test validation fails for unregistered producer."""
    result = ingestion_service.ingest_signal(sample_signal)
    assert result.status.value == "rejected"
    assert result.error_code == ErrorCode.PRODUCER_NOT_REGISTERED

