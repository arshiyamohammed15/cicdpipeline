"""
Unit tests for ActionPolicy.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ..action_policy import ActionPolicy, ActionPolicyConfig


class TestActionPolicy:
    """Test action policy."""

    @pytest.fixture
    def action_policy_config(self):
        """Create test action policy config."""
        return ActionPolicyConfig(
            action_id="test-action",
            action_type="create_ticket",
            enabled=True,
            confidence_gate={"enabled": True, "min_confidence": 0.7},
            permissions={"require_policy_approval": False},
        )

    @pytest.fixture
    def epc3_adapter(self):
        """Create mock EPC-3 adapter."""
        adapter = AsyncMock()
        adapter.evaluate_policy = AsyncMock()
        return adapter

    @pytest.mark.asyncio
    async def test_check_confidence_gate_passes(self, action_policy_config):
        """Test confidence gate passes when confidence is above threshold."""
        policy = ActionPolicy()
        
        result = policy.check_confidence_gate(
            action_policy=action_policy_config,
            forecast_confidence=0.8,
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_check_confidence_gate_fails(self, action_policy_config):
        """Test confidence gate fails when confidence is below threshold."""
        policy = ActionPolicy()
        
        result = policy.check_confidence_gate(
            action_policy=action_policy_config,
            forecast_confidence=0.5,
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_check_confidence_gate_disabled(self, action_policy_config):
        """Test confidence gate passes when disabled."""
        action_policy_config.confidence_gate = {"enabled": False}
        policy = ActionPolicy()
        
        result = policy.check_confidence_gate(
            action_policy=action_policy_config,
            forecast_confidence=0.0,  # Even with 0 confidence
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_evaluate_action_authorization_disabled(self, action_policy_config):
        """Test authorization denied when action is disabled."""
        action_policy_config.enabled = False
        policy = ActionPolicy()
        
        result = await policy.evaluate_action_authorization(
            action_policy=action_policy_config,
            context={},
        )
        
        assert result["authorized"] is False
        assert "disabled" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_evaluate_action_authorization_tenant_filter(self, action_policy_config):
        """Test authorization denied when tenant not in allowed list."""
        action_policy_config.permissions = {"tenant_ids": ["tenant-1", "tenant-2"]}
        policy = ActionPolicy()
        
        result = await policy.evaluate_action_authorization(
            action_policy=action_policy_config,
            context={},
            tenant_id="tenant-3",
        )
        
        assert result["authorized"] is False
        assert "tenant" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_evaluate_action_authorization_no_policy_approval(self, action_policy_config):
        """Test authorization passes when no policy approval required."""
        action_policy_config.permissions = {"require_policy_approval": False}
        policy = ActionPolicy()
        
        result = await policy.evaluate_action_authorization(
            action_policy=action_policy_config,
            context={},
        )
        
        assert result["authorized"] is True
