from __future__ import annotations
"""
Resilience test: Provider Outage (RF-IA-01).

What: Test provider outage handling with retries, circuit breaker, incidents
Why: Ensure system degrades gracefully
Coverage Target: Outage scenarios
"""

# Imports handled by conftest.py

import pytest
from unittest.mock import Mock, patch
import uuid

# Module setup handled by root conftest.py

from integration_adapters.reliability.circuit_breaker import CircuitBreaker, CircuitState

class TestProviderOutage:
    """Test provider outage handling."""

    def test_circuit_breaker_opens_on_repeated_failures(self):
        """Test circuit breaker opens after repeated failures."""
        breaker = CircuitBreaker(uuid.uuid4(), failure_threshold=3)

        def fail_func():
            raise Exception("Provider outage")

        # First failure
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.CLOSED

        # Second failure
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.CLOSED

        # Third failure - should open
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.state == CircuitState.OPEN

    def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects calls when open."""
        breaker = CircuitBreaker(uuid.uuid4(), failure_threshold=1)

        def fail_func():
            raise Exception("Provider outage")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Should reject new calls
        from integration_adapters.reliability.circuit_breaker import CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "should not execute")

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovers after timeout."""
        breaker = CircuitBreaker(uuid.uuid4(), failure_threshold=1, timeout=0.1)

        def fail_func():
            raise Exception("Provider outage")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        import time
        time.sleep(0.2)

        # Should transition to half-open
        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

