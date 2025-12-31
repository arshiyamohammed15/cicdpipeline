from __future__ import annotations

import httpx
import pytest
import time
from fastapi import HTTPException

from src.shared_libs.error_recovery import (
    ErrorClassifier,
    RetryPolicy,
    call_with_recovery,
    call_with_recovery_async,
    exponential_backoff_schedule,
)


def test_exponential_backoff_schedule_is_deterministic() -> None:
    policy = RetryPolicy(max_attempts=6, base_delay_ms=100, max_delay_ms=500)

    schedule = exponential_backoff_schedule(policy)

    assert schedule == (100, 200, 400, 500, 500)
    assert schedule == exponential_backoff_schedule(policy)


def test_error_classifier_marks_timeout_as_retryable() -> None:
    classifier = ErrorClassifier()
    request = httpx.Request("GET", "https://example.com")

    error = httpx.TimeoutException("timeout", request=request)

    assert classifier.is_timeout(error) is True
    assert classifier.is_retryable(error) is True


def test_error_classifier_marks_http_status_retryable() -> None:
    classifier = ErrorClassifier()
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(503, request=request)
    error = httpx.HTTPStatusError("server error", request=request, response=response)

    assert classifier.is_retryable(error) is True


def test_error_classifier_marks_http_status_non_retryable() -> None:
    classifier = ErrorClassifier()
    request = httpx.Request("GET", "https://example.com")
    response = httpx.Response(400, request=request)
    error = httpx.HTTPStatusError("client error", request=request, response=response)

    assert classifier.is_retryable(error) is False


def test_error_classifier_marks_http_exception_retryable() -> None:
    classifier = ErrorClassifier()
    error = HTTPException(status_code=429, detail="rate limited")

    assert classifier.is_retryable(error) is True


def test_error_classifier_marks_http_exception_non_retryable() -> None:
    classifier = ErrorClassifier()
    error = HTTPException(status_code=403, detail="forbidden")

    assert classifier.is_retryable(error) is False


def test_call_with_recovery_retries_until_success() -> None:
    attempts = []

    def flaky() -> str:
        attempts.append("try")
        if len(attempts) < 3:
            raise TimeoutError("timeout")
        return "ok"

    policy = RetryPolicy(max_attempts=3, base_delay_ms=1, max_delay_ms=1)

    result = call_with_recovery(
        flaky,
        policy=policy,
        classifier=ErrorClassifier(),
        sleep=lambda _: None,
    )

    assert result == "ok"
    assert len(attempts) == 3


def test_call_with_recovery_does_not_retry_non_retryable() -> None:
    attempts = []

    def boom() -> None:
        attempts.append("try")
        raise ValueError("nope")

    policy = RetryPolicy(max_attempts=3, base_delay_ms=1, max_delay_ms=1)

    with pytest.raises(ValueError):
        call_with_recovery(
            boom,
            policy=policy,
            classifier=ErrorClassifier(),
            sleep=lambda _: None,
        )

    assert len(attempts) == 1


def test_call_with_recovery_enforces_timeout() -> None:
    attempts = []

    def slow() -> str:
        attempts.append("try")
        time.sleep(0.2)
        return "ok"

    policy = RetryPolicy(max_attempts=2, base_delay_ms=1, max_delay_ms=1)

    with pytest.raises(TimeoutError):
        call_with_recovery(
            slow,
            policy=policy,
            classifier=ErrorClassifier(),
            timeout_ms=50,
            sleep=lambda _: None,
        )

    assert len(attempts) == 2


@pytest.mark.asyncio
async def test_call_with_recovery_async_retries_until_success() -> None:
    attempts = []

    async def flaky() -> str:
        attempts.append("try")
        if len(attempts) < 2:
            raise TimeoutError("timeout")
        return "ok"

    async def no_sleep(_: float) -> None:
        return None

    policy = RetryPolicy(max_attempts=2, base_delay_ms=1, max_delay_ms=1)

    result = await call_with_recovery_async(
        flaky,
        policy=policy,
        classifier=ErrorClassifier(),
        sleep=no_sleep,
    )

    assert result == "ok"
    assert len(attempts) == 2
