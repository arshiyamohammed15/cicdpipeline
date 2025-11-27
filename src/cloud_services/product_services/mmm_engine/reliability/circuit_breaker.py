"""
Simple circuit breaker implementation for MMM dependencies.
"""

from __future__ import annotations

import time
from enum import Enum
from typing import Callable, Any

from ..observability.metrics import set_circuit_state


class CircuitState(Enum):
    CLOSED = 0
    OPEN = 1
    HALF_OPEN = 2


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_ts = 0.0

    def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        self._ensure_can_call()
        try:
            result = func(*args, **kwargs)
            self._reset()
            return result
        except Exception:
            self._record_failure()
            raise

    async def call_async(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        self._ensure_can_call()
        try:
            result = await func(*args, **kwargs)
            self._reset()
            return result
        except Exception:
            self._record_failure()
            raise

    def _ensure_can_call(self) -> None:
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_ts < self.recovery_timeout:
                raise RuntimeError(f"Circuit {self.name} open")
            self.state = CircuitState.HALF_OPEN

    def _reset(self) -> None:
        self.failures = 0
        self.state = CircuitState.CLOSED
        set_circuit_state(self.name, self.state.value)

    def _record_failure(self) -> None:
        self.failures += 1
        self.last_failure_ts = time.time()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
        set_circuit_state(self.name, self.state.value)


