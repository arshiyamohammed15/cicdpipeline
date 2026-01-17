"""
Unit tests for ActionExecutor.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ...correlation.trace_context import TraceContext
from ..action_executor import ActionExecutor
from ..action_policy import ActionPolicyConfig


class TestActionExecutor:
    """Test action executor."""

    @pytest.fixture
    def action_policy_config(self):
        """Create test action policy config."""
        return ActionPolicyConfig(
            action_id="test-action",
            action_type="create_ticket",
            enabled=True,
            confidence_gate={"enabled": True, "min_confidence": 0.7},
        )

    @pytest.fixture
    def epc4_client(self):
        """Create mock EPC-4 client."""
        client = MagicMock()
        client.emit_alert = MagicMock()
        return client

    @pytest.fixture
    def receipt_service(self):
        """Create mock receipt service."""
        service = AsyncMock()
        service.generate_receipt = AsyncMock(return_value={"receipt_id": "test-receipt"})
        return service

    @pytest.fixture
    def action_policy(self):
        """Create mock action policy."""
        policy = AsyncMock()
        policy.check_confidence_gate = MagicMock(return_value=True)
        policy.evaluate_action_authorization = AsyncMock(
            return_value={"authorized": True, "reason": "Allowed", "policy_version_ids": []}
        )
        return policy

    @pytest.mark.asyncio
    async def test_execute_action_confidence_gate_fails(
        self, action_policy_config, action_policy
    ):
        """Test action blocked when confidence gate fails."""
        action_policy.check_confidence_gate = MagicMock(return_value=False)
        executor = ActionExecutor(action_policy=action_policy)
        
        result = await executor.execute_action(
            action_policy=action_policy_config,
            action_type="create_ticket",
            forecast_data={"confidence": 0.5},
            context={},
        )
        
        assert result["status"] == "blocked"
        assert "confidence" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_execute_action_policy_denied(
        self, action_policy_config, action_policy
    ):
        """Test action denied when policy denies."""
        action_policy.evaluate_action_authorization = AsyncMock(
            return_value={"authorized": False, "reason": "Policy denied", "policy_version_ids": []}
        )
        executor = ActionExecutor(action_policy=action_policy)
        
        result = await executor.execute_action(
            action_policy=action_policy_config,
            action_type="create_ticket",
            forecast_data={"confidence": 0.8},
            context={},
        )
        
        assert result["status"] == "denied"
        assert "denied" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_execute_action_create_ticket(
        self, action_policy_config, epc4_client, action_policy
    ):
        """Test create_ticket action execution."""
        executor = ActionExecutor(
            epc4_client=epc4_client,
            action_policy=action_policy,
        )
        
        trace_ctx = TraceContext(trace_id="test-trace", span_id="test-span")
        result = await executor.execute_action(
            action_policy=action_policy_config,
            action_type="create_ticket",
            forecast_data={
                "confidence": 0.8,
                "time_to_breach_seconds": 3600,
                "forecast_id": "test-forecast",
                "slo_id": "SLO-A",
            },
            context={"component": "test-component"},
            trace_ctx=trace_ctx,
            tenant_id="test-tenant",
        )
        
        assert result["status"] == "executed"
        assert "ticket_created" in result.get("action_result", {})

    @pytest.mark.asyncio
    async def test_execute_action_generates_receipt(
        self, action_policy_config, receipt_service, action_policy
    ):
        """Test action generates receipt."""
        executor = ActionExecutor(
            receipt_service=receipt_service,
            action_policy=action_policy,
        )
        
        trace_ctx = TraceContext(trace_id="test-trace", span_id="test-span")
        result = await executor.execute_action(
            action_policy=action_policy_config,
            action_type="create_ticket",
            forecast_data={"confidence": 0.8},
            context={},
            trace_ctx=trace_ctx,
        )
        
        assert result["status"] == "executed"
        assert result.get("receipt_id") is not None
