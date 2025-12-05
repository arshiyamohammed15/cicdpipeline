from __future__ import annotations
"""
Unit tests for ComponentRegistryService.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from health_reliability_monitoring.services.registry_service import ComponentRegistryService
from health_reliability_monitoring.models import ComponentDefinition, DependencyReference
try:
    from health_reliability_monitoring.database import models as db_models
except ImportError:
    db_models = None  # Database module not implemented


class TestComponentRegistryService:
    """Test ComponentRegistryService."""

    def test_register_new_component(self, db_session, policy_client, edge_client):
        """Test registering a new component."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )

        result = service.register_component(component)

        assert result.component_id == "test-component-1"
        assert result.enrolled is True

        # Verify component was persisted
        db_component = db_session.get(db_models.Component, "test-component-1")
        assert db_component is not None
        assert db_component.name == "Test Component"
        assert db_component.component_type == "service"

    def test_update_existing_component(self, db_session, policy_client, edge_client):
        """Test updating an existing component."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        # Register initial component
        component1 = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )
        service.register_component(component1)

        # Update component
        component2 = ComponentDefinition(
            component_id="test-component-1",
            name="Updated Component",
            component_type="agent",
            plane="Shared",
            tenant_scope="global",
        )
        result = service.register_component(component2)

        assert result.component_id == "test-component-1"

        # Verify update
        db_component = db_session.get(db_models.Component, "test-component-1")
        assert db_component.name == "Updated Component"
        assert db_component.component_type == "agent"
        assert db_component.plane == "Shared"

    def test_register_component_with_dependencies(self, db_session, policy_client, edge_client):
        """Test registering component with dependencies."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
            dependencies=[
                DependencyReference(component_id="dep-1", critical=True),
                DependencyReference(component_id="dep-2", critical=False),
            ],
        )

        result = service.register_component(component)
        assert result.enrolled is True

        # Verify dependencies
        db_component = db_session.get(db_models.Component, "test-component-1")
        assert len(db_component.dependencies) == 2
        assert db_component.dependencies[0].dependency_id == "dep-1"
        assert db_component.dependencies[0].critical is True

    def test_get_component(self, db_session, policy_client, edge_client):
        """Test retrieving a component."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        # Register component
        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
        )
        service.register_component(component)

        # Retrieve component
        retrieved = service.get_component("test-component-1")

        assert retrieved is not None
        assert retrieved.component_id == "test-component-1"
        assert retrieved.name == "Test Component"

    def test_get_nonexistent_component(self, db_session, policy_client, edge_client):
        """Test retrieving non-existent component."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        retrieved = service.get_component("nonexistent")

        assert retrieved is None

    def test_list_components(self, db_session, policy_client, edge_client):
        """Test listing all components."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        # Register multiple components
        for i in range(3):
            component = ComponentDefinition(
                component_id=f"test-component-{i}",
                name=f"Test Component {i}",
                component_type="service",
                plane="Product",
                tenant_scope="tenant",
            )
            service.register_component(component)

        # List components
        components = service.list_components()

        assert len(components) == 3
        assert all(c.component_id.startswith("test-component-") for c in components)

    def test_component_with_slo_target(self, db_session, policy_client, edge_client):
        """Test registering component with SLO target."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
            slo_target=99.5,
            error_budget_minutes=216,
        )

        result = service.register_component(component)
        assert result.enrolled is True

        db_component = db_session.get(db_models.Component, "test-component-1")
        assert db_component.slo_target == 99.5
        assert db_component.error_budget_minutes == 216

    def test_component_with_metrics_profile(self, db_session, policy_client, edge_client):
        """Test registering component with metrics profile."""
        service = ComponentRegistryService(db_session, policy_client, edge_client)

        component = ComponentDefinition(
            component_id="test-component-1",
            name="Test Component",
            component_type="service",
            plane="Product",
            tenant_scope="tenant",
            metrics_profile=["GOLDEN_SIGNALS", "RED"],
        )

        result = service.register_component(component)
        assert result.enrolled is True

        db_component = db_session.get(db_models.Component, "test-component-1")
        assert "GOLDEN_SIGNALS" in db_component.metrics_profile
        assert "RED" in db_component.metrics_profile

