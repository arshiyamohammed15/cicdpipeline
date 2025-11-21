"""
Tests for observability - TC-SIN-010: Pipeline Observability.
"""

import pytest
from datetime import datetime

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, registered_producer
)


def test_tc_sin_010_pipeline_observability(ingestion_service, registered_producer, metrics_registry, sample_signal, routing_engine):
    """TC-SIN-010: Pipeline observability metrics and logs."""
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

    # Ingest signal
    result = ingestion_service.ingest_signal(sample_signal)

    # Check metrics
    metrics = metrics_registry.get_metrics()
    assert metrics['signals_ingested_total'] > 0
    assert metrics['latency_samples_count'] > 0

