"""
Tests for Rate Limiter & Budget Guard (RLBGS) with EPC-13 adapter.

Covers PRD section 10.1: Rate limiting behavior, deny-by-default when EPC-13 unavailable.
"""

import pytest

from src.shared_libs.cccs.ratelimit import RateLimiterConfig, RateLimiterService
from src.shared_libs.cccs.exceptions import BudgetExceededError
from tests.cccs.mocks import MockEPC13Adapter
from unittest.mock import patch


def test_rate_limiter_allows_when_budget_available():
    """Test rate limiter allows when budget is available."""
    config = RateLimiterConfig(
        epc13_base_url="http://localhost:8013",
        epc13_timeout_seconds=5.0,
        epc13_api_version="v1",
        default_deny_on_unavailable=True,
    )
    
    with patch('src.shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter', MockEPC13Adapter):
        limiter = RateLimiterService(config)
        decision = limiter.check_budget("action", 2, use_cache=False)
        assert decision.allowed
        assert decision.remaining == 98.0  # Default capacity is 100


def test_rate_limiter_denies_when_budget_exceeded():
    """Test rate limiter denies when budget is exceeded."""
    config = RateLimiterConfig(
        epc13_base_url="http://localhost:8013",
        epc13_timeout_seconds=5.0,
        epc13_api_version="v1",
        default_deny_on_unavailable=True,
    )
    
    with patch('src.shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter', MockEPC13Adapter):
        limiter = RateLimiterService(config)
        limiter._adapter._default_capacity = 100.0
        # Use up budget - first call succeeds
        decision1 = limiter.check_budget("action", 60.0, use_cache=False)
        assert decision1.allowed is True
        assert decision1.remaining == 40.0
        
        # Second call that exceeds remaining budget should fail
        with pytest.raises(BudgetExceededError):
            limiter.check_budget("action", 50.0)  # 50 > 40 remaining


def test_rate_limiter_deny_by_default_when_epc13_unavailable():
    """Test rate limiter denies by default when EPC-13 unavailable."""
    config = RateLimiterConfig(
        epc13_base_url="http://localhost:8013",
        epc13_timeout_seconds=5.0,
        epc13_api_version="v1",
        default_deny_on_unavailable=True,
    )
    
    with patch('src.shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter', MockEPC13Adapter):
        limiter = RateLimiterService(config)
        limiter._adapter._fail_check = True
        
        with pytest.raises(BudgetExceededError, match="EPC-13 unavailable, denying by default"):
            limiter.check_budget("action", 1.0, use_cache=False)


def test_rate_limiter_budget_snapshot_persistence():
    """Test rate limiter persists budget snapshots."""
    config = RateLimiterConfig(
        epc13_base_url="http://localhost:8013",
        epc13_timeout_seconds=5.0,
        epc13_api_version="v1",
        default_deny_on_unavailable=True,
    )
    
    with patch('src.shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter', MockEPC13Adapter):
        limiter = RateLimiterService(config)
        
        import asyncio
        budget_data = {"action_id": "action1", "remaining": 50.0}
        snapshot_id = asyncio.run(limiter.persist_budget_snapshot(budget_data))
        assert snapshot_id.startswith("snapshot-")


def test_rate_limiter_callback_on_budget_exceeded():
    """Test rate limiter calls callback on budget exceeded."""
    config = RateLimiterConfig(
        epc13_base_url="http://localhost:8013",
        epc13_timeout_seconds=5.0,
        epc13_api_version="v1",
        default_deny_on_unavailable=True,
    )
    
    callback_called = []
    
    def on_exceeded(action_id, cost):
        callback_called.append((action_id, cost))
    
    config.on_budget_exceeded = on_exceeded
    
    with patch('src.shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter', MockEPC13Adapter):
        limiter = RateLimiterService(config)
        limiter._adapter._default_capacity = 10.0  # Lower capacity for test
        
        with pytest.raises(BudgetExceededError):
            limiter.check_budget("action", 20.0, use_cache=False)  # Exceeds capacity
        
        assert len(callback_called) == 1
        assert callback_called[0] == ("action", 20.0)

