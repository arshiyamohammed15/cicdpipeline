"""Tests for routing engine."""

import pytest
from datetime import datetime

from tests.sin.conftest import SignalEnvelope, SignalKind, Environment, RoutingClass


def test_routing_classification(routing_engine):
    """Test routing class classification."""
    signal = SignalEnvelope(
        signal_id="signal_1",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened"},
        schema_version="1.0.0"
    )

    routing_classes = routing_engine.classify_signal(signal)
    assert RoutingClass.REALTIME_DETECTION in routing_classes


def test_tenant_aware_routing(routing_engine):
    """Test tenant-aware routing."""
    signal = SignalEnvelope(
        signal_id="signal_1",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened"},
        schema_version="1.0.0"
    )

    # Register consumer
    received_signals = []
    def consumer(signal):
        received_signals.append(signal)
        return True

    routing_engine.register_consumer("test_destination:tenant_1", consumer)

    # Register rule
    from tests.sin.conftest import RoutingRule
    rule = RoutingRule(
        routing_class=RoutingClass.REALTIME_DETECTION,
        condition=lambda s: True,
        destination="test_destination",
        tenant_aware=True
    )
    routing_engine.register_rule(RoutingClass.REALTIME_DETECTION, rule)

    # Route signal
    results = routing_engine.route_signal(signal)
    assert len(results) > 0
    assert any(success for _, _, success in results)

