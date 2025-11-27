"""
Circuit Breaker for UBI Module (EPC-9).

What: Circuit breaker pattern for external service calls
Why: Prevent cascading failures and enable graceful degradation per PRD NFR-6
Reads/Writes: Circuit breaker state management
Contracts: Circuit breaker pattern (Open/Closed/Half-Open states)
Risks: Circuit breaker misconfiguration, false positives
"""

import logging
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker state enumeration."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Per PRD NFR-6: Prevents cascading failures by opening circuit after threshold failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes in half-open to close circuit
            timeout_seconds: Timeout before transitioning from open to half-open
            name: Circuit breaker name for logging
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.name = name
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        
        self._lock = Lock()

    def call(
        self,
        func: Callable[[], Any],
        fallback: Optional[Callable[[], Any]] = None
    ) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            fallback: Optional fallback function if circuit is open

        Returns:
            Function result or fallback result

        Raises:
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
                    raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            # Execute function
            result = func()
            
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
        func: Callable[[], Any],
        fallback: Optional[Callable[[], Any]] = None
    ) -> Any:
        """
        Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            fallback: Optional fallback function if circuit is open

        Returns:
            Function result or fallback result

        Raises:
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
                    raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            # Execute async function
            result = await func()
            
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
        """Record successful call."""
        self.last_success_time = datetime.utcnow()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker {self.name} transitioning to CLOSED after {self.success_count} successes")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def _record_failure(self) -> None:
        """Record failed call."""
        self.last_failure_time = datetime.utcnow()
        self.failure_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open immediately opens circuit
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} transitioning to OPEN after failure in HALF_OPEN")
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} transitioning to OPEN after {self.failure_count} failures")

    def _should_attempt_reset(self) -> bool:
        """
        Check if circuit should attempt reset (transition from open to half-open).

        Returns:
            True if should attempt reset, False otherwise
        """
        if self.last_failure_time is None:
            return True
        
        time_since_failure = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.timeout_seconds

    def get_state(self) -> Dict[str, Any]:
        """
        Get circuit breaker state.

        Returns:
            State dictionary
        """
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None
            }

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            self.last_success_time = None
            logger.info(f"Circuit breaker {self.name} manually reset to CLOSED")


class CircuitBreakerManager:
    """
    Manager for multiple circuit breakers.

    Provides centralized management and monitoring of circuit breakers.
    """

    def __init__(self):
        """Initialize circuit breaker manager."""
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 60.0
    ) -> CircuitBreaker:
        """
        Get or create circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            success_threshold: Number of successes to close
            timeout_seconds: Timeout before half-open

        Returns:
            CircuitBreaker instance
        """
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout_seconds=timeout_seconds,
                name=name
            )
        return self.breakers[name]

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """
        Get states of all circuit breakers.

        Returns:
            Dictionary of breaker states
        """
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}

