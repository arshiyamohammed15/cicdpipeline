from __future__ import annotations

from typing import AsyncIterator

import pytest

from src.shared_libs.sse_guard import (
    SSEGuard,
    SSE_MAX_BYTES,
    SSE_MAX_DURATION,
    SSE_MAX_EVENTS,
)


async def _collect(events: AsyncIterator[str]) -> list[str]:
    return [event async for event in events]


async def _fake_events(items: list[str]) -> AsyncIterator[str]:
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_sse_guard_stops_at_max_events() -> None:
    guard = SSEGuard(max_events=2)

    result = await _collect(guard.wrap(_fake_events(["a", "b", "c"])))

    assert result == ["a", "b"]
    assert guard.last_termination is not None
    assert guard.last_termination.reason_code == SSE_MAX_EVENTS
    assert guard.last_termination.observed_events == 2


@pytest.mark.asyncio
async def test_sse_guard_stops_at_max_bytes() -> None:
    guard = SSEGuard(max_bytes=4)

    result = await _collect(guard.wrap(_fake_events(["aa", "bb", "cc"])))

    assert result == ["aa", "bb"]
    assert guard.last_termination is not None
    assert guard.last_termination.reason_code == SSE_MAX_BYTES
    assert guard.last_termination.observed_events == 2
    assert guard.last_termination.observed_bytes == 4


@pytest.mark.asyncio
async def test_sse_guard_stops_at_max_duration() -> None:
    clock_state = {"now": 0.0}

    def clock() -> float:
        return clock_state["now"]

    async def events() -> AsyncIterator[str]:
        for item in ["a", "b", "c"]:
            clock_state["now"] += 0.04
            yield item

    guard = SSEGuard(max_duration_ms=100, clock=clock)

    result = await _collect(guard.wrap(events()))

    assert result == ["a", "b"]
    assert guard.last_termination is not None
    assert guard.last_termination.reason_code == SSE_MAX_DURATION
    assert guard.last_termination.observed_events == 2
    assert guard.last_termination.observed_duration_ms == 120
