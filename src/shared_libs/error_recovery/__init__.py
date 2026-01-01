"""
Deterministic retry and error classification primitives.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
import inspect
import time
from typing import Awaitable, Callable, FrozenSet, Optional, TypeVar, overload

import httpx
from fastapi import HTTPException

try:  # pragma: no cover - optional dependency
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None


_DEFAULT_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})
T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """Retry policy parameters for deterministic backoff."""

    max_attempts: int
    base_delay_ms: int
    max_delay_ms: int
    jitter: bool = False

    def backoff_delay_ms(self, attempt: int) -> int:
        """Return the backoff delay for a 1-based retry attempt."""
        return exponential_backoff_delay_ms(attempt, self)

    def schedule(self) -> tuple[int, ...]:
        """
        Return the backoff schedule for retry attempts.

        The schedule length is max_attempts - 1 because delays occur between
        attempts.
        """
        return exponential_backoff_schedule(self)


def exponential_backoff_delay_ms(attempt: int, policy: RetryPolicy) -> int:
    """
    Calculate deterministic exponential backoff delay.

    Jitter is intentionally ignored to keep the schedule deterministic.
    """
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    delay = policy.base_delay_ms * (2 ** (attempt - 1))
    return min(delay, policy.max_delay_ms)


def exponential_backoff_schedule(policy: RetryPolicy) -> tuple[int, ...]:
    """Build a deterministic backoff schedule for the policy."""
    return tuple(
        exponential_backoff_delay_ms(attempt, policy)
        for attempt in range(1, policy.max_attempts)
    )


@dataclass(frozen=True)
class ErrorClassifier:
    """Classify errors for retry and timeout handling."""

    retryable_status_codes: FrozenSet[int] = _DEFAULT_RETRYABLE_STATUS_CODES

    def is_retryable(self, error: BaseException) -> bool:
        """Return True if the error is considered retryable."""
        status_code = self._extract_status_code(error)
        if status_code is not None:
            return status_code in self.retryable_status_codes

        if self.is_timeout(error):
            return True

        if isinstance(error, httpx.RequestError):
            return True

        if requests is not None:
            if isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
                return True

        return False

    def is_timeout(self, error: BaseException) -> bool:
        """Return True if the error represents a timeout."""
        return isinstance(
            error,
            (
                httpx.TimeoutException,
                TimeoutError,
            ),
        )

    def _extract_status_code(self, error: BaseException) -> Optional[int]:
        if isinstance(error, httpx.HTTPStatusError):
            return error.response.status_code
        if isinstance(error, HTTPException):
            return error.status_code
        return None


@dataclass
class RecoveryReport:
    """Capture deterministic recovery metadata for receipts or logs."""

    attempts_made: int = 0
    final_outcome: str = "unknown"
    last_error_code: Optional[str] = None
    timeout_applied_ms: Optional[int] = None

    def to_receipt_fields(self) -> dict[str, Optional[object]]:
        return {
            "recovery_applied": self.attempts_made > 1,
            "attempts_made": self.attempts_made,
            "final_outcome": self.final_outcome,
            "last_error_code": self.last_error_code,
            "timeout_applied_ms": self.timeout_applied_ms,
        }


def _is_async_callable(func: object) -> bool:
    if func is None:
        return False
    if inspect.iscoroutinefunction(func):
        return True
    call_attr = getattr(func, "__call__", None)
    if call_attr is not None and inspect.iscoroutinefunction(call_attr):
        return True
    underlying = getattr(func, "func", None)
    if underlying is not None and inspect.iscoroutinefunction(underlying):
        return True
    return False


def _call_with_recovery_sync(
    func: Callable[[], T],
    *,
    policy: RetryPolicy,
    classifier: ErrorClassifier,
    timeout_ms: Optional[int] = None,
    report: Optional[RecoveryReport] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Sync implementation for call_with_recovery."""
    if policy.max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if timeout_ms is not None and timeout_ms <= 0:
        raise ValueError("timeout_ms must be > 0 when provided")

    if report is not None:
        report.timeout_applied_ms = timeout_ms
        report.attempts_made = 0
        report.final_outcome = "unknown"
        report.last_error_code = None

    attempt = 1
    while True:
        if report is not None:
            report.attempts_made = attempt
        try:
            result = _call_with_timeout(func, timeout_ms)
            if report is not None:
                report.final_outcome = "success"
            return result
        except Exception as exc:
            if report is not None:
                report.last_error_code = _sanitize_error_code(exc)
            if attempt >= policy.max_attempts or not classifier.is_retryable(exc):
                if report is not None:
                    report.final_outcome = "failure"
                raise
            delay_ms = policy.backoff_delay_ms(attempt)
            if delay_ms > 0:
                sleep(delay_ms / 1000)
            attempt += 1


async def _call_with_recovery_async(
    func: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    classifier: ErrorClassifier,
    timeout_ms: Optional[int] = None,
    report: Optional[RecoveryReport] = None,
    sleep: Optional[Callable[[float], Awaitable[None]]] = None,
) -> T:
    """Async implementation for call_with_recovery using anyio for timeouts and backoff."""
    if policy.max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    if timeout_ms is not None and timeout_ms <= 0:
        raise ValueError("timeout_ms must be > 0 when provided")

    import anyio

    sleep_func = sleep or anyio.sleep
    attempt = 1
    if report is not None:
        report.timeout_applied_ms = timeout_ms
        report.attempts_made = 0
        report.final_outcome = "unknown"
        report.last_error_code = None

    while True:
        if report is not None:
            report.attempts_made = attempt
        try:
            if timeout_ms is None:
                result = await func()
            else:
                with anyio.fail_after(timeout_ms / 1000):
                    result = await func()
            if report is not None:
                report.final_outcome = "success"
            return result
        except Exception as exc:
            if report is not None:
                report.last_error_code = _sanitize_error_code(exc)
            if attempt >= policy.max_attempts or not classifier.is_retryable(exc):
                if report is not None:
                    report.final_outcome = "failure"
                raise
            delay_ms = policy.backoff_delay_ms(attempt)
            if delay_ms > 0:
                await sleep_func(delay_ms / 1000)
            attempt += 1


@overload
def call_with_recovery(
    func: Callable[[], T],
    *,
    policy: RetryPolicy,
    classifier: ErrorClassifier,
    timeout_ms: Optional[int] = None,
    report: Optional[RecoveryReport] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    ...


@overload
def call_with_recovery(
    func: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    classifier: ErrorClassifier,
    timeout_ms: Optional[int] = None,
    report: Optional[RecoveryReport] = None,
    sleep: Optional[Callable[[float], Awaitable[None]]] = None,
) -> Awaitable[T]:
    ...


def call_with_recovery(
    func: Callable[[], T] | Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    classifier: ErrorClassifier,
    timeout_ms: Optional[int] = None,
    report: Optional[RecoveryReport] = None,
    sleep: Optional[Callable[[float], object]] = time.sleep,
) -> T | Awaitable[T]:
    """
    Call a sync or async function with deterministic retries and optional timeout enforcement.
    """
    if _is_async_callable(func):
        async_sleep = sleep if _is_async_callable(sleep) else None
        return _call_with_recovery_async(
            func,  # type: ignore[arg-type]
            policy=policy,
            classifier=classifier,
            timeout_ms=timeout_ms,
            report=report,
            sleep=async_sleep,  # type: ignore[arg-type]
        )
    return _call_with_recovery_sync(
        func,  # type: ignore[arg-type]
        policy=policy,
        classifier=classifier,
        timeout_ms=timeout_ms,
        report=report,
        sleep=sleep or time.sleep,
    )


async def call_with_recovery_async(
    func: Callable[[], Awaitable[T]],
    *,
    policy: RetryPolicy,
    classifier: ErrorClassifier,
    timeout_ms: Optional[int] = None,
    report: Optional[RecoveryReport] = None,
    sleep: Optional[Callable[[float], Awaitable[None]]] = None,
) -> T:
    """
    Compatibility wrapper for async call sites. Prefer call_with_recovery.
    """
    result = call_with_recovery(
        func,
        policy=policy,
        classifier=classifier,
        timeout_ms=timeout_ms,
        report=report,
        sleep=sleep,
    )
    if inspect.isawaitable(result):
        return await result
    return result


def _call_with_timeout(func: Callable[[], T], timeout_ms: Optional[int]) -> T:
    """Execute a callable with an optional timeout enforced via a worker thread."""
    if timeout_ms is None:
        return func()

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_ms / 1000)
        except FutureTimeoutError as exc:
            future.cancel()
            raise TimeoutError(f"Operation exceeded {timeout_ms} ms") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _sanitize_error_code(error: BaseException) -> str:
    if isinstance(error, httpx.HTTPStatusError):
        return f"HTTP_{error.response.status_code}"
    if isinstance(error, HTTPException):
        return f"HTTP_{error.status_code}"
    return type(error).__name__


__all__ = [
    "ErrorClassifier",
    "RetryPolicy",
    "RecoveryReport",
    "call_with_recovery",
    "call_with_recovery_async",
    "exponential_backoff_delay_ms",
    "exponential_backoff_schedule",
]
