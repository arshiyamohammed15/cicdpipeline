"""
Circuit breaker implementation for Integration Adapters Module.

What: Per-connection circuit breakers to prevent cascading failures per FR-8
Why: Protect system from repeated provider failures
Reads/Writes: Circuit breaker state in memory
Contracts: PRD FR-8 (Error Handling, Retries & Circuit Breaking)
Risks: Circuit breaker state management, false positives
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Optional
from uuid import UUID


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker per connection.
    
    Opens after failure threshold, allows test requests in half-open state,
    closes after success threshold.
    """

    def __init__(
        self,
        connection_id: UUID,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            connection_id: Connection ID
            failure_threshold: Number of failures before opening
            success_threshold: Number of successes in half-open to close
            timeout: Time in seconds before attempting half-open
        """
        self.connection_id = connection_id
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.opened_at: Optional[float] = None

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: If function execution fails
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.opened_at and (time.time() - self.opened_at) >= self.timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is open for connection {self.connection_id}"
                )
        
        # Execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.opened_at = None
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Failure in half-open, go back to open
            self.state = CircuitState.OPEN
            self.opened_at = time.time()
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            # Check if threshold reached
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.opened_at = time.time()

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreakerManager:
    """Manager for multiple circuit breakers (one per connection)."""

    def __init__(self):
        """Initialize circuit breaker manager."""
        self._breakers: dict[UUID, CircuitBreaker] = {}

    def get_breaker(
        self,
        connection_id: UUID,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker for connection.
        
        Args:
            connection_id: Connection ID
            failure_threshold: Failure threshold
            success_threshold: Success threshold
            timeout: Timeout in seconds
            
        Returns:
            Circuit breaker instance
        """
        if connection_id not in self._breakers:
            self._breakers[connection_id] = CircuitBreaker(
                connection_id, failure_threshold, success_threshold, timeout
            )
        return self._breakers[connection_id]

    def remove_breaker(self, connection_id: UUID) -> bool:
        """
        Remove circuit breaker for connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            True if removed, False if not found
        """
        if connection_id in self._breakers:
            del self._breakers[connection_id]
            return True
        return False

    def reset_breaker(self, connection_id: UUID) -> bool:
        """
        Reset circuit breaker for connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            True if reset, False if not found
        """
        if connection_id in self._breakers:
            self._breakers[connection_id].reset()
            return True
        return False


# Global circuit breaker manager
_circuit_breaker_manager = CircuitBreakerManager()


def get_circuit_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager instance."""
    return _circuit_breaker_manager

