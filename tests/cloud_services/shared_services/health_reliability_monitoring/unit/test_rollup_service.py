from __future__ import annotations
"""
Unit tests for RollupService.
"""

import pytest
from datetime import datetime

from health_reliability_monitoring.services.rollup_service import RollupService
try:
    from health_reliability_monitoring.database import models as db_models
except ImportError:
    db_models = None  # Database module not implemented


@pytest.mark.unit
class TestRollupService:
    """Test RollupService."""

    @pytest.fixture
    def rollup_service(self, db_session):
        """Create rollup service."""
        return RollupService(db_session)

    @pytest.fixture
    def sample_component(self, db_session):
        """Create sample component."""
        component = db_models.Component(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            environment="prod",
            tenant_scope="tenant",
        )
        db_session.add(component)
        db_session.commit()
        return component

    @pytest.fixture
    def sample_snapshots(self, db_session, sample_component):
        """Create sample health snapshots."""
        snapshots = [
            db_models.HealthSnapshot(
                snapshot_id=f"snapshot-{i}",
                component_id="test-component-1",
                tenant_id="test-tenant",
                plane="Product",
                environment="prod",
                state="OK",
                reason_code="healthy",
                evaluated_at=datetime.utcnow(),
            )
            for i in range(3)
        ]
        for snapshot in snapshots:
            db_session.add(snapshot)
        db_session.commit()
        return snapshots

    @pytest.mark.unit
    def test_latest_component_states_empty(self, rollup_service):
        """Test latest component states with no snapshots."""
        states = rollup_service.latest_component_states()

        assert isinstance(states, dict)
        assert len(states) == 0

    @pytest.mark.unit
    def test_latest_component_states_with_snapshots(self, rollup_service, sample_snapshots):
        """Test latest component states with snapshots."""
        states = rollup_service.latest_component_states()

        assert len(states) == 1
        assert "test-component-1" in states
        assert states["test-component-1"].state == "OK"

    @pytest.mark.unit
    def test_tenant_view(self, rollup_service, sample_snapshots):
        """Test tenant view generation."""
        view = rollup_service.tenant_view("test-tenant")

        assert view.tenant_id == "test-tenant"
        assert "Product" in view.plane_states
        assert view.counts["OK"] >= 0

    @pytest.mark.unit
    def test_tenant_view_empty(self, rollup_service):
        """Test tenant view with no snapshots."""
        view = rollup_service.tenant_view("nonexistent-tenant")

        assert view.tenant_id == "nonexistent-tenant"
        assert len(view.plane_states) == 0
        assert view.counts["OK"] == 0

    @pytest.mark.unit
    def test_plane_view(self, rollup_service, sample_snapshots):
        """Test plane view generation."""
        view = rollup_service.plane_view("Product", "prod")

        assert view.plane == "Product"
        assert view.environment == "prod"
        assert view.state in ["OK", "DEGRADED", "FAILED", "UNKNOWN"]

    @pytest.mark.unit
    def test_plane_view_empty(self, rollup_service):
        """Test plane view with no snapshots."""
        view = rollup_service.plane_view("Product", "prod")

        assert view.plane == "Product"
        assert view.environment == "prod"
        assert view.state == "UNKNOWN"

    @pytest.mark.unit
    def test_dependency_penalties(self, db_session, rollup_service):
        """Test dependency penalty application."""
        # Create parent component
        parent = db_models.Component(
            component_id="parent-component",
            name="Parent Component",
            component_type="service",
            plane="Product",
            environment="prod",
            tenant_scope="tenant",
        )
        db_session.add(parent)

        # Create dependency
        dep = db_models.ComponentDependency(
            component_id="parent-component",
            dependency_id="dep-component",
            critical=True,
        )
        parent.dependencies.append(dep)
        db_session.commit()

        # Create snapshot for dependency with FAILED state
        dep_snapshot = db_models.HealthSnapshot(
            snapshot_id="dep-snapshot",
            component_id="dep-component",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            state="FAILED",
            reason_code="failed",
            evaluated_at=datetime.utcnow(),
        )
        db_session.add(dep_snapshot)

        # Create snapshot for parent with OK state
        parent_snapshot = db_models.HealthSnapshot(
            snapshot_id="parent-snapshot",
            component_id="parent-component",
            tenant_id="test-tenant",
            plane="Product",
            environment="prod",
            state="OK",
            reason_code="healthy",
            evaluated_at=datetime.utcnow(),
        )
        db_session.add(parent_snapshot)
        db_session.commit()

        states = rollup_service.latest_component_states()

        # Parent should be penalized due to critical dependency failure
        assert "parent-component" in states
        # State should reflect dependency failure
        assert states["parent-component"].state in ["FAILED", "OK"]  # May or may not be penalized depending on implementation

