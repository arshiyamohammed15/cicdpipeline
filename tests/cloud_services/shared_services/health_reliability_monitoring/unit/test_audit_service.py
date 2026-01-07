from __future__ import annotations
"""
Unit tests for AuditService.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from health_reliability_monitoring.services.audit_service import AuditService
from health_reliability_monitoring.services.event_bus_service import EventBusService


@pytest.mark.unit
class TestAuditService:
    """Test AuditService."""

    @pytest.fixture
    def event_bus(self):
        """Create mock event bus."""
        bus = Mock(spec=EventBusService)
        bus.emit_receipt = AsyncMock()
        return bus

    @pytest.fixture
    def audit_service(self, event_bus):
        """Create audit service."""
        return AuditService(event_bus)

    @pytest.mark.asyncio
    async def test_record_access(self, audit_service, event_bus):
        """Test recording access."""
        actor = {"actor": "api", "tenant_id": "test-tenant"}
        resource = "tenant:test-tenant"
        action = "read_health"

        await audit_service.record_access(actor, resource, action)

        # Verify event bus was called
        event_bus.emit_receipt.assert_called_once()
        call_args = event_bus.emit_receipt.call_args
        assert call_args[0][0]["actor"] == actor
        assert call_args[0][0]["resource"] == resource
        assert call_args[0][0]["action"] == action
        assert call_args[1]["action"] == "meta_audit"

    @pytest.mark.asyncio
    async def test_record_access_different_resources(self, audit_service, event_bus):
        """Test recording access for different resources."""
        resources = [
            ("tenant:test-tenant", "read_health"),
            ("plane:Product:prod", "read_health"),
            ("component:test-component-1", "read_status"),
        ]

        for resource, action in resources:
            await audit_service.record_access(
                {"actor": "api"},
                resource,
                action,
            )

        assert event_bus.emit_receipt.call_count == 3

    @pytest.mark.asyncio
    async def test_record_access_with_timestamp(self, audit_service, event_bus):
        """Test that access records include timestamp."""
        await audit_service.record_access(
            {"actor": "api"},
            "tenant:test-tenant",
            "read_health",
        )

        call_args = event_bus.emit_receipt.call_args
        payload = call_args[0][0]
        assert "observed_at" in payload
        assert payload["observed_at"] is not None

