"""End-to-end integration tests for SIN module."""

import pytest
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, IngestStatus, registered_producer
)


@pytest.mark.integration
def test_end_to_end_ingestion_pipeline(ingestion_service, registered_producer, routing_engine):
    """Test complete ingestion pipeline."""
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

    signal = SignalEnvelope(
        signal_id="signal_e2e",
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

    # Ingest signal
    result = ingestion_service.ingest_signal(signal)

    # Should be accepted
    assert result.status == IngestStatus.ACCEPTED

