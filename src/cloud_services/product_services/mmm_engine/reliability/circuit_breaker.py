"""
Thread-safe circuit breaker implementation for MMM dependencies.

Per PRD NFR-6: Prevents cascading failures by opening circuit after threshold failures.
Uses thread-safe Lock-based implementation for high concurrency scenarios.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Optional

from ..observability.metrics import set_circuit_state

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker state enumeration."""
    CLOSED = 0  # Normal operation
    OPEN = 1  # Failing, reject requests
    HALF_OPEN = 2  # Testing if service recovered


class CircuitBreaker:
    """
    Thread-safe circuit breaker for external service calls.

    Per PRD NFR-6: Prevents cascading failures by opening circuit after threshold failures.
    Uses Lock-based synchronization for thread safety in high concurrency scenarios.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        recovery_timeout: float = 60.0,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker name for logging and metrics
            failure_threshold: Number of failures before opening circuit (default: 5 per PRD)
            success_threshold: Number of successes in half-open to close circuit (default: 2)
            recovery_timeout: Timeout in seconds before transitioning from open to half-open (default: 60.0 per PRD)
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None

        self._lock = Lock()

    def call(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Optional[Callable[[], Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function with circuit breaker protection (thread-safe).

        Args:
            func: Function to execute
            *args: Positional arguments for func
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments for func

        Returns:
            Function result or fallback result

        Raises:
            RuntimeError: If circuit is open and no fallback provided
            Exception: If function fails and no fallback provided
        """
        with self._lock:
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    if fallback:
                        logger.warning(f"Circuit breaker {self.name} is OPEN, using fallback")
                        return fallback()
                    raise RuntimeError(f"Circuit {self.name} open")

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Record success
            with self._lock:
                self._record_success()

            return result
        except Exception as e:
            # Record failure
            with self._lock:
                self._record_failure()

            # If fallback provided and circuit is open, use fallback
            if self.state == CircuitState.OPEN and fallback:
                logger.warning(f"Circuit breaker {self.name} is OPEN after failure, using fallback")
                return fallback()

            raise

    async def call_async(
        self,
        func: Callable[..., Any],
        *args: Any,
        fallback: Optional[Callable[[], Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute async function with circuit breaker protection (thread-safe).

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            fallback: Optional fallback function if circuit is open
            **kwargs: Keyword arguments for func

        Returns:
            Function result or fallback result

        Raises:
            RuntimeError: If circuit is open and no fallback provided
            Exception: If function fails and no fallback provided
        """
        with self._lock:
            # Check if circuit is open
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                else:
                    if fallback:
                        logger.warning(f"Circuit breaker {self.name} is OPEN, using fallback")
                        return await fallback() if callable(fallback) else fallback()
                    raise RuntimeError(f"Circuit {self.name} open")

        try:
            # Execute async function
            result = await func(*args, **kwargs)

            # Record success
            with self._lock:
                self._record_success()

            return result
        except Exception as e:
            # Record failure
            with self._lock:
                self._record_failure()

            # If fallback provided and circuit is open, use fallback
            if self.state == CircuitState.OPEN and fallback:
                logger.warning(f"Circuit breaker {self.name} is OPEN after failure, using fallback")
                return await fallback() if callable(fallback) else fallback()

            raise

    def _record_success(self) -> None:
        """Record successful call (thread-safe)."""
        self.last_success_time = datetime.now(timezone.utc)

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(
                    f"Circuit breaker {self.name} transitioning to CLOSED after {self.success_count} successes"
                )
                set_circuit_state(self.name, self.state.value)
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _record_failure(self) -> None:
        """Record failed call (thread-safe)."""
        self.last_failure_time = datetime.now(timezone.utc)
        self.failure_count += 1

        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens circuit
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} transitioning to OPEN after failure in HALF_OPEN")
            set_circuit_state(self.name, self.state.value)
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker {self.name} transitioning to OPEN after {self.failure_count} failures"
                )
                set_circuit_state(self.name, self.state.value)

    def _should_attempt_reset(self) -> bool:
        """
        Check if circuit should attempt reset (transition from open to half-open).

        Returns:
            True if should attempt reset, False otherwise
        """
        if self.last_failure_time is None:
            return True

        time_since_failure = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
        return time_since_failure >= self.recovery_timeout

    def get_state(self) -> Dict[str, Any]:
        """
        Get circuit breaker state (thread-safe).

        Returns:
            State dictionary with current state, counts, and timestamps
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.name,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            }

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state (thread-safe)."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.last_success_time = None
            logger.info(f"Circuit breaker {self.name} manually reset to CLOSED")
            set_circuit_state(self.name, self.state.value)


