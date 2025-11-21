"""
Tests for DLQ handler - TC-SIN-007: Persistent Failure → DLQ.
"""

import pytest
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, ErrorCode, registered_producer
)


def test_tc_sin_007_persistent_failure_dlq(ingestion_service, registered_producer, dlq_handler):
    """TC-SIN-007: Persistent downstream failure routes to DLQ."""
    # Create signal that will fail validation permanently
    invalid_signal = SignalEnvelope(
        signal_id="signal_persistent_fail",
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

    # Retry until it goes to DLQ
    result = None
    for _ in range(5):
        result = ingestion_service.ingest_signal(invalid_signal)
        if result.status.value == "dlq":
            break

    # Should be in DLQ
    assert result.status.value == "dlq"
    assert result.dlq_id is not None

    # Verify DLQ entry exists
    dlq_entry = dlq_handler.get_dlq_entry(result.dlq_id)
    assert dlq_entry is not None
    assert dlq_entry.signal_id == invalid_signal.signal_id
    assert dlq_entry.error_code == ErrorCode.SCHEMA_VIOLATION

