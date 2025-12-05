from __future__ import annotations
"""
Unit tests for circuit breaker.

What: Test circuit breaker state transitions, failure counting, recovery
Why: Ensure circuit breaker protects against cascading failures
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
import time
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.reliability.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    CircuitBreakerManager,
)

class TestCircuitBreaker:
    """Test CircuitBreaker."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        connection_id = uuid4()
        breaker = CircuitBreaker(connection_id)

        assert breaker.connection_id == connection_id
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0

    def test_circuit_breaker_success(self):
        """Test successful call keeps circuit closed."""
        import uuid
        breaker = CircuitBreaker(uuid.uuid4())

        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    def test_circuit_breaker_failure_counting(self):
        """Test failure counting."""
        import uuid
        breaker = CircuitBreaker(uuid.uuid4(), failure_threshold=3)

        def fail_func():
            raise Exception("Failure")

        # First failure
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.failure_count == 1
        assert breaker.state == CircuitState.CLOSED

        # Second failure
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.failure_count == 2
        assert breaker.state == CircuitState.CLOSED

        # Third failure - should open
        with pytest.raises(Exception):
            breaker.call(fail_func)
        assert breaker.failure_count == 3
        assert breaker.state == CircuitState.OPEN

    def test_circuit_breaker_opens_on_threshold(self):
        """Test circuit opens when failure threshold reached."""
        breaker = CircuitBreaker(uuid4(), failure_threshold=2)

        def fail_func():
            raise Exception("Failure")

        # First failure
        with pytest.raises(Exception):
            breaker.call(fail_func)

        # Second failure - should open
        with pytest.raises(Exception):
            breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.opened_at is not None

    def test_circuit_breaker_rejects_when_open(self):
        """Test circuit rejects calls when open."""
        breaker = CircuitBreaker(uuid4(), failure_threshold=1, timeout=60.0)

        def fail_func():
            raise Exception("Failure")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Should reject new calls
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(lambda: "should not execute")

    def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit goes to half-open after timeout."""
        breaker = CircuitBreaker(uuid4(), failure_threshold=1, timeout=0.1)

        def fail_func():
            raise Exception("Failure")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.2)

        # Next call should transition to half-open
        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        # Should still be half-open (needs success_threshold successes)
        assert breaker.state == CircuitState.HALF_OPEN

    def test_circuit_breaker_closes_after_success_threshold(self):
        """Test circuit closes after success threshold in half-open."""
        breaker = CircuitBreaker(
            uuid4(),
            failure_threshold=1,
            success_threshold=2,
            timeout=0.1
        )

        def fail_func():
            raise Exception("Failure")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)

        time.sleep(0.2)

        # First success in half-open
        breaker.call(lambda: "success")
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker.success_count == 1

        # Second success - should close
        breaker.call(lambda: "success")
        assert breaker.state == CircuitState.CLOSED
        assert breaker.success_count == 0
        assert breaker.failure_count == 0

    def test_circuit_breaker_failure_in_half_open(self):
        """Test failure in half-open returns to open."""
        breaker = CircuitBreaker(uuid4(), failure_threshold=1, timeout=0.1)

        def fail_func():
            raise Exception("Failure")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)

        time.sleep(0.2)

        # Failure in half-open should return to open
        with pytest.raises(Exception):
            breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.success_count == 0

    def test_circuit_breaker_reset(self):
        """Test circuit breaker reset."""
        import uuid
        breaker = CircuitBreaker(uuid.uuid4(), failure_threshold=1)

        def fail_func():
            raise Exception("Failure")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(fail_func)

        assert breaker.state == CircuitState.OPEN

        # Reset
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0
        assert breaker.success_count == 0
        assert breaker.opened_at is None

class TestCircuitBreakerManager:
    """Test CircuitBreakerManager."""

    def test_get_breaker_creates_new(self):
        """Test getting breaker creates new instance."""
        manager = CircuitBreakerManager()
        connection_id = uuid4()

        breaker = manager.get_breaker(connection_id)
        assert breaker.connection_id == connection_id
        assert breaker.state == CircuitState.CLOSED

    def test_get_breaker_returns_existing(self):
        """Test getting breaker returns existing instance."""
        import uuid
        manager = CircuitBreakerManager()
        connection_id = uuid.uuid4()

        breaker1 = manager.get_breaker(connection_id)
        breaker2 = manager.get_breaker(connection_id)

        assert breaker1 is breaker2

    def test_remove_breaker(self):
        """Test removing breaker."""
        import uuid
        manager = CircuitBreakerManager()
        connection_id = uuid.uuid4()

        manager.get_breaker(connection_id)
        removed = manager.remove_breaker(connection_id)
        assert removed is True

        removed_again = manager.remove_breaker(connection_id)
        assert removed_again is False

    def test_reset_breaker(self):
        """Test resetting breaker."""
        from reliability.circuit_breaker import CircuitBreaker, CircuitBreakerManager, CircuitState

        manager = CircuitBreakerManager()
        connection_id = uuid4()

        # Create breaker with low failure threshold to open quickly
        breaker = CircuitBreaker(connection_id, failure_threshold=1)
        manager._breakers[connection_id] = breaker

        def fail_func():
            raise Exception("Failure")

        # Open the circuit (need to trigger failure_threshold failures)
        with pytest.raises(Exception):
            breaker.call(fail_func)

        # After one failure with threshold=1, circuit should be OPEN
        assert breaker.state == CircuitState.OPEN

        # Reset
        reset = manager.reset_breaker(connection_id)
        assert reset is True
        assert breaker.state == CircuitState.CLOSED

