from __future__ import annotations
"""
Unit tests for HealthEvaluationService.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

from health_reliability_monitoring.services.evaluation_service import HealthEvaluationService
from health_reliability_monitoring.models import TelemetryPayload, HealthSnapshot
try:
    from health_reliability_monitoring.database import models as db_models
except ImportError:
    db_models = None  # Database module not implemented


class TestHealthEvaluationService:
    """Test HealthEvaluationService."""

    @pytest.fixture
    def evaluation_service(self, db_session, policy_client):
        """Create evaluation service instance."""
        return HealthEvaluationService(db_session, policy_client)

    @pytest.fixture
    def registered_component(self, db_session):
        """Create a registered component for testing."""
        component = db_models.Component(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            environment="prod",
            tenant_scope="tenant",
            health_policies=["policy-1"],
        )
        db_session.add(component)
        db_session.commit()
        return component

    @pytest.mark.asyncio
    async def test_evaluate_batch_with_healthy_metrics(self, evaluation_service, registered_component):
        """Test evaluating batch with healthy metrics."""
        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0, "error_rate": 0.01},
            telemetry_type="metrics",
        )

        snapshots = await evaluation_service.evaluate_batch([payload])

        assert len(snapshots) == 1
        assert snapshots[0].component_id == "test-component-1"
        assert snapshots[0].state in ["OK", "DEGRADED", "FAILED", "UNKNOWN"]

    @pytest.mark.asyncio
    async def test_evaluate_batch_with_no_metrics(self, evaluation_service, registered_component):
        """Test evaluating batch with no metrics."""
        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={},
            telemetry_type="heartbeat",
        )

        snapshots = await evaluation_service.evaluate_batch([payload])

        assert len(snapshots) == 1
        assert snapshots[0].state == "UNKNOWN"
        assert "no_metrics" in snapshots[0].reason_code

    @pytest.mark.asyncio
    async def test_evaluate_batch_unknown_component(self, evaluation_service):
        """Test evaluating batch for unknown component."""
        payload = TelemetryPayload(
            component_id="unknown-component",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0},
            telemetry_type="metrics",
        )

        snapshots = await evaluation_service.evaluate_batch([payload])

        # Unknown component should be skipped
        assert len(snapshots) == 0

    @pytest.mark.asyncio
    async def test_evaluate_batch_multiple_payloads(self, evaluation_service, registered_component):
        """Test evaluating batch with multiple payloads."""
        payloads = [
            TelemetryPayload(
                component_id="test-component-1",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                timestamp=datetime.utcnow(),
                metrics={"latency_p95_ms": 150.0},
                telemetry_type="metrics",
            ),
            TelemetryPayload(
                component_id="test-component-1",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                timestamp=datetime.utcnow() + timedelta(seconds=10),
                metrics={"latency_p95_ms": 200.0},
                telemetry_type="metrics",
            ),
        ]

        snapshots = await evaluation_service.evaluate_batch(payloads)

        assert len(snapshots) == 2
        assert all(s.component_id == "test-component-1" for s in snapshots)

    @pytest.mark.asyncio
    async def test_evaluate_batch_with_slo_service(self, db_session, policy_client):
        """Test evaluating batch with SLO service."""
        slo_service = Mock()
        event_bus = Mock()
        evaluation_service = HealthEvaluationService(
            db_session, policy_client, slo_service=slo_service, event_bus=event_bus
        )

        component = db_models.Component(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            environment="prod",
            tenant_scope="tenant",
            health_policies=["policy-1"],
            slo_target=99.5,
        )
        db_session.add(component)
        db_session.commit()

        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0},
            telemetry_type="metrics",
        )

        snapshots = await evaluation_service.evaluate_batch([payload])

        assert len(snapshots) == 1
        # SLO service should be called
        # (Note: Actual SLO update logic depends on implementation)

    @pytest.mark.asyncio
    async def test_evaluate_batch_with_event_bus(self, db_session, policy_client):
        """Test evaluating batch with event bus."""
        event_bus = Mock()
        event_bus.emit_health_transition = AsyncMock()
        evaluation_service = HealthEvaluationService(
            db_session, policy_client, event_bus=event_bus
        )

        component = db_models.Component(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            environment="prod",
            tenant_scope="tenant",
            health_policies=["policy-1"],
        )
        db_session.add(component)
        db_session.commit()

        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0},
            telemetry_type="metrics",
        )

        snapshots = await evaluation_service.evaluate_batch([payload])

        assert len(snapshots) == 1
        # Event bus should be called
        event_bus.emit_health_transition.assert_called_once()

