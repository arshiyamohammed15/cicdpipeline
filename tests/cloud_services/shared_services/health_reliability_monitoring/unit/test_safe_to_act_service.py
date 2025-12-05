from __future__ import annotations
"""
Unit tests for SafeToActService.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from health_reliability_monitoring.services.safe_to_act_service import SafeToActService
from health_reliability_monitoring.models import SafeToActRequest, SafeToActResponse
from health_reliability_monitoring.services.rollup_service import RollupService
from health_reliability_monitoring.services.telemetry_ingestion_service import TelemetryIngestionService
from health_reliability_monitoring.dependencies import DeploymentClient, PolicyClient


class TestSafeToActService:
    """Test SafeToActService."""

    @pytest.fixture
    def rollup_service(self, db_session):
        """Create rollup service."""
        return RollupService(db_session)

    @pytest.fixture
    def telemetry_service(self):
        """Create telemetry service."""
        service = TelemetryIngestionService()
        return service

    @pytest.fixture
    def safe_to_act_service(self, rollup_service, telemetry_service, deployment_client, policy_client):
        """Create safe-to-act service."""
        return SafeToActService(rollup_service, telemetry_service, deployment_client, policy_client)

    @pytest.mark.asyncio
    async def test_evaluate_allowed_healthy_tenant(self, safe_to_act_service):
        """Test safe-to-act evaluation for healthy tenant."""
        request = SafeToActRequest(
            tenant_id="test-tenant",
            plane="Product",
            action_type="standard_action",
        )

        response = await safe_to_act_service.evaluate(request)

        assert isinstance(response, SafeToActResponse)
        assert response.evaluated_at is not None
        assert len(response.reason_codes) > 0

    @pytest.mark.asyncio
    async def test_evaluate_with_component_scope(self, safe_to_act_service):
        """Test safe-to-act evaluation with component scope."""
        request = SafeToActRequest(
            tenant_id="test-tenant",
            plane="Product",
            action_type="standard_action",
            component_scope=["component-1", "component-2"],
        )

        response = await safe_to_act_service.evaluate(request)

        assert isinstance(response, SafeToActResponse)
        assert response.evaluated_at is not None

    @pytest.mark.asyncio
    async def test_evaluate_stale_telemetry(self, rollup_service, telemetry_service, deployment_client, policy_client):
        """Test safe-to-act evaluation with stale telemetry."""
        # Mock telemetry service to return stale age
        telemetry_service.last_ingest_age = Mock(return_value=1000)  # Very stale

        service = SafeToActService(rollup_service, telemetry_service, deployment_client, policy_client)

        request = SafeToActRequest(
            tenant_id="test-tenant",
            action_type="deployment",
        )

        response = await service.evaluate(request)

        assert isinstance(response, SafeToActResponse)
        # Should handle stale telemetry appropriately
        assert "health_system_unavailable" in response.reason_codes or response.allowed is False

    @pytest.mark.asyncio
    async def test_evaluate_different_action_types(self, safe_to_act_service):
        """Test safe-to-act evaluation for different action types."""
        action_types = ["deployment", "rollback", "scale", "migration"]

        for action_type in action_types:
            request = SafeToActRequest(
                tenant_id="test-tenant",
                plane="Product",
                action_type=action_type,
            )

            response = await safe_to_act_service.evaluate(request)

            assert isinstance(response, SafeToActResponse)
            assert response.evaluated_at is not None

    @pytest.mark.asyncio
    async def test_evaluate_deployment_notification(self, safe_to_act_service, deployment_client):
        """Test that deployment client is notified."""
        request = SafeToActRequest(
            tenant_id="test-tenant",
            action_type="deployment",
        )

        response = await safe_to_act_service.evaluate(request)

        # Verify deployment client was called
        assert deployment_client.safe_to_act_events is not None
        assert len(deployment_client.safe_to_act_events) > 0

