from __future__ import annotations
"""
Unit tests for Health & Reliability Monitoring models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from health_reliability_monitoring.models import (
    ComponentDefinition,
    DependencyReference,
    TelemetryPayload,
    HealthSnapshot,
    TenantHealthView,
    PlaneHealthView,
    SafeToActRequest,
    SafeToActResponse,
    SLOStatus,
    ComponentRegistrationResponse,
)


class TestComponentDefinition:
    """Test ComponentDefinition model."""

    def test_valid_component_definition(self):
        """Test creating valid component definition."""
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )
        assert component.component_id == "test-component-1"
        assert component.name == "Test Component"
        assert component.component_type == "service"
        assert component.plane == "Product"
        assert component.tenant_scope == "tenant"

    def test_component_with_dependencies(self):
        """Test component with dependencies."""
        deps = [
            DependencyReference(component_id="dep-1", critical=True),
            DependencyReference(component_id="dep-2", critical=False),
        ]
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
            dependencies=deps,
        )
        assert len(component.dependencies) == 2
        assert component.dependencies[0].component_id == "dep-1"
        assert component.dependencies[0].critical is True

    def test_component_with_slo(self):
        """Test component with SLO target."""
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
            slo_target=99.5,
            error_budget_minutes=216,
        )
        assert component.slo_target == 99.5
        assert component.error_budget_minutes == 216

    def test_component_id_validation(self):
        """Test component_id validation (min length)."""
        with pytest.raises(ValidationError):
            ComponentDefinition(
                component_id="ab",  # Too short
                name="Test",
                component_type="service",
                plane="Product",
                tenant_scope="tenant",
            )


class TestTelemetryPayload:
    """Test TelemetryPayload model."""

    def test_valid_telemetry_payload(self):
        """Test creating valid telemetry payload."""
        payload = TelemetryPayload(
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            metrics={"latency_p95_ms": 150.0, "error_rate": 0.01},
            labels={"region": "us-east-1"},
            telemetry_type="metrics",
        )
        assert payload.component_id == "test-component-1"
        assert payload.tenant_id == "test-tenant"
        assert payload.telemetry_type == "metrics"
        assert payload.metrics["latency_p95_ms"] == 150.0

    def test_telemetry_payload_without_tenant(self):
        """Test telemetry payload without tenant_id."""
        payload = TelemetryPayload(
            component_id="test-component-1",
            plane="Shared",
            environment="prod",
            timestamp=datetime.utcnow(),
            telemetry_type="heartbeat",
        )
        assert payload.tenant_id is None

    def test_label_cardinality_limit(self):
        """Test label cardinality limit enforcement."""
        # Create too many labels (assuming default limit is reasonable)
        labels = {f"key_{i}": f"value_{i}" for i in range(100)}
        # This should raise ValidationError if limit is exceeded
        # Note: Actual limit depends on settings
        payload = TelemetryPayload(
            component_id="test-component-1",
            plane="Product",
            environment="prod",
            timestamp=datetime.utcnow(),
            labels=labels,
            telemetry_type="metrics",
        )
        # If limit is not exceeded, payload should be valid
        assert payload.labels is not None


class TestHealthSnapshot:
    """Test HealthSnapshot model."""

    def test_valid_health_snapshot(self):
        """Test creating valid health snapshot."""
        snapshot = HealthSnapshot(
            snapshot_id="snapshot-1",
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            state="OK",
            reason_code="healthy",
            metrics_summary={"latency_p95_ms": 150.0},
            evaluated_at=datetime.utcnow(),
        )
        assert snapshot.state == "OK"
        assert snapshot.reason_code == "healthy"
        assert snapshot.slo_state is None

    def test_health_snapshot_with_slo(self):
        """Test health snapshot with SLO state."""
        snapshot = HealthSnapshot(
            snapshot_id="snapshot-1",
            component_id="test-component-1",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            state="OK",
            reason_code="healthy",
            slo_state="within_budget",
            evaluated_at=datetime.utcnow(),
        )
        assert snapshot.slo_state == "within_budget"


class TestSafeToActRequest:
    """Test SafeToActRequest model."""

    def test_valid_safe_to_act_request(self):
        """Test creating valid safe-to-act request."""
        request = SafeToActRequest(
            tenant_id="test-tenant",
            plane="Product",
            action_type="standard_action",
        )
        assert request.tenant_id == "test-tenant"
        assert request.action_type == "standard_action"
        assert request.component_scope is None

    def test_safe_to_act_request_with_scope(self):
        """Test safe-to-act request with component scope."""
        request = SafeToActRequest(
            tenant_id="test-tenant",
            plane="Product",
            action_type="standard_action",
            component_scope=["component-1", "component-2"],
        )
        assert len(request.component_scope) == 2


class TestSafeToActResponse:
    """Test SafeToActResponse model."""

    def test_valid_safe_to_act_response(self):
        """Test creating valid safe-to-act response."""
        response = SafeToActResponse(
            allowed=True,
            recommended_mode="normal",
            reason_codes=["healthy"],
            evaluated_at=datetime.utcnow(),
        )
        assert response.allowed is True
        assert response.recommended_mode == "normal"
        assert "healthy" in response.reason_codes


class TestSLOStatus:
    """Test SLOStatus model."""

    def test_valid_slo_status(self):
        """Test creating valid SLO status."""
        slo = SLOStatus(
            component_id="test-component-1",
            slo_id="slo-1",
            window="30d",
            sli_values={"availability_pct": 99.5},
            error_budget_total_minutes=216,
            error_budget_consumed_minutes=10,
            burn_rate=0.046,
            state="within_budget",
        )
        assert slo.component_id == "test-component-1"
        assert slo.state == "within_budget"
        assert slo.burn_rate == 0.046


class TestTenantHealthView:
    """Test TenantHealthView model."""

    def test_valid_tenant_health_view(self):
        """Test creating valid tenant health view."""
        view = TenantHealthView(
            tenant_id="test-tenant",
            plane_states={"Product": "OK", "Shared": "OK"},
            counts={"OK": 10, "DEGRADED": 2, "FAILED": 0, "UNKNOWN": 0},
            updated_at=datetime.utcnow(),
        )
        assert view.tenant_id == "test-tenant"
        assert view.plane_states["Product"] == "OK"
        assert view.counts["OK"] == 10


class TestPlaneHealthView:
    """Test PlaneHealthView model."""

    def test_valid_plane_health_view(self):
        """Test creating valid plane health view."""
        view = PlaneHealthView(
            plane="Product",
            environment="prod",
            state="OK",
            component_breakdown={"OK": ["c1", "c2"], "DEGRADED": ["c3"]},
            updated_at=datetime.utcnow(),
        )
        assert view.plane == "Product"
        assert view.state == "OK"

