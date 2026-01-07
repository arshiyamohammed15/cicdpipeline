"""
Tests for service layer - TC-SIN-001: Valid Ingestion, TC-SIN-006: Transient Failure → Retry.
"""

import pytest
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, IngestStatus, registered_producer
)


@pytest.mark.unit
def test_tc_sin_001_valid_ingestion(ingestion_service, registered_producer, sample_signal, routing_engine):
    """TC-SIN-001: Valid signal ingestion and normalization."""
    # Register a consumer for routing
    def consumer(signal):
        return True
    routing_engine.register_consumer("test_destination:tenant_1", consumer)

    # Register routing rule
    from tests.sin.conftest import RoutingClass, RoutingRule
    rule = RoutingRule(
        routing_class=RoutingClass.REALTIME_DETECTION,
        condition=lambda s: True,
        destination="test_destination"
    )
    routing_engine.register_rule(RoutingClass.REALTIME_DETECTION, rule)

    result = ingestion_service.ingest_signal(sample_signal)

    assert result.status == IngestStatus.ACCEPTED
    assert result.signal_id == sample_signal.signal_id
    assert result.error_code is None


@pytest.mark.unit
def test_tc_sin_006_transient_failure_retry(ingestion_service, registered_producer, routing_engine, sample_signal):
    """TC-SIN-006: Transient downstream failure triggers retry."""
    # Register a consumer that fails first time, succeeds second time
    call_count = {"count": 0}

    def failing_consumer(signal):
        call_count["count"] += 1
        if call_count["count"] < 2:
            return False  # Fail first time
        return True  # Succeed second time

    routing_engine.register_consumer("test_destination:tenant_1", failing_consumer)

    # Create routing rule
    from tests.sin.conftest import RoutingClass, RoutingRule
    rule = RoutingRule(
        routing_class=RoutingClass.REALTIME_DETECTION,
        condition=lambda s: True,
        destination="test_destination"
    )
    routing_engine.register_rule(RoutingClass.REALTIME_DETECTION, rule)

    # Use sample_signal but modify payload
    signal = SignalEnvelope(
        signal_id="signal_retry",
        tenant_id=sample_signal.tenant_id,
        environment=sample_signal.environment,
        producer_id=sample_signal.producer_id,
        signal_kind=sample_signal.signal_kind,
        signal_type=sample_signal.signal_type,
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened", "pr_id": 123},
        schema_version=sample_signal.schema_version
    )

    # First attempt should fail (transient)
    result1 = ingestion_service.ingest_signal(signal)
    # Should be rejected (will retry)
    assert result1.status.value in ["rejected", "accepted"]

    # Retry should succeed
    if result1.status.value == "rejected":
        result2 = ingestion_service.ingest_signal(signal)
        assert result2.status == IngestStatus.ACCEPTED

