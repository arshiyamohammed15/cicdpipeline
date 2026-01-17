"""
Unit tests for PreventFirstService.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from ..prevent_first_service import PreventFirstService
from ..action_executor import ActionExecutor
from ..action_policy import ActionPolicy, ActionPolicyConfig


class TestPreventFirstService:
    """Test prevent-first service."""

    @pytest.fixture
    def action_executor(self):
        """Create mock action executor."""
        executor = AsyncMock()
        executor.execute_action = AsyncMock(
            return_value={"action_id": "test-action", "status": "executed", "receipt_id": "test-receipt"}
        )
        return executor

    @pytest.fixture
    def action_policy(self):
        """Create mock action policy."""
        policy = MagicMock()
        policy.check_confidence_gate = MagicMock(return_value=True)
        return policy

    @pytest.mark.asyncio
    async def test_evaluate_and_trigger_action_not_found(self, action_executor, action_policy):
        """Test evaluation when action policy not found."""
        service = PreventFirstService(
            action_executor=action_executor,
            action_policy=action_policy,
        )
        
        result = await service.evaluate_and_trigger(
            forecast_data={"confidence": 0.8, "slo_id": "SLO-A"},
            action_id="nonexistent-action",
        )
        
        assert result["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_evaluate_and_trigger_action_disabled(self, action_executor, action_policy):
        """Test evaluation when action is disabled."""
        service = PreventFirstService(
            action_executor=action_executor,
            action_policy=action_policy,
        )
        
        # Manually add a disabled policy
        disabled_policy = ActionPolicyConfig(
            action_id="disabled-action",
            action_type="create_ticket",
            enabled=False,
            confidence_gate={"enabled": True, "min_confidence": 0.7},
        )
        service._action_policies["disabled-action"] = disabled_policy
        
        result = await service.evaluate_and_trigger(
            forecast_data={"confidence": 0.8},
            action_id="disabled-action",
        )
        
        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_evaluate_and_trigger_confidence_gate_fails(self, action_executor, action_policy):
        """Test evaluation when confidence gate fails."""
        action_policy.check_confidence_gate = MagicMock(return_value=False)
        service = PreventFirstService(
            action_executor=action_executor,
            action_policy=action_policy,
        )
        
        enabled_policy = ActionPolicyConfig(
            action_id="enabled-action",
            action_type="create_ticket",
            enabled=True,
            confidence_gate={"enabled": True, "min_confidence": 0.7},
        )
        service._action_policies["enabled-action"] = enabled_policy
        
        result = await service.evaluate_and_trigger(
            forecast_data={"confidence": 0.5},  # Below threshold
            action_id="enabled-action",
        )
        
        assert result["status"] == "blocked"
        assert "confidence" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_evaluate_and_trigger_success(self, action_executor, action_policy):
        """Test successful action execution."""
        service = PreventFirstService(
            action_executor=action_executor,
            action_policy=action_policy,
        )
        
        enabled_policy = ActionPolicyConfig(
            action_id="enabled-action",
            action_type="create_ticket",
            enabled=True,
            confidence_gate={"enabled": True, "min_confidence": 0.7},
        )
        service._action_policies["enabled-action"] = enabled_policy
        
        result = await service.evaluate_and_trigger(
            forecast_data={"confidence": 0.8, "slo_id": "SLO-A"},
            action_id="enabled-action",
        )
        
        assert result["status"] == "executed"
        action_executor.execute_action.assert_called_once()

    @pytest.mark.asyncio
    async def test_evaluate_forecasts_and_trigger(self, action_executor, action_policy):
        """Test evaluating multiple forecasts."""
        service = PreventFirstService(
            action_executor=action_executor,
            action_policy=action_policy,
        )
        
        enabled_policy = ActionPolicyConfig(
            action_id="enabled-action",
            action_type="create_ticket",
            enabled=True,
            confidence_gate={"enabled": True, "min_confidence": 0.7},
        )
        service._action_policies["enabled-action"] = enabled_policy
        
        forecasts = [
            {"confidence": 0.8, "slo_id": "SLO-A"},
            {"confidence": 0.9, "slo_id": "SLO-B"},
        ]
        
        results = await service.evaluate_forecasts_and_trigger(
            forecasts=forecasts,
            action_mappings={"SLO-A": "enabled-action", "SLO-B": "enabled-action"},
        )
        
        assert len(results) == 2
        assert all(r["status"] in ["executed", "blocked", "denied", "disabled"] for r in results)
