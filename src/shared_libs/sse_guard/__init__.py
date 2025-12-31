"""
Deterministic guard for SSE-style async event streams.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import AsyncIterator, Callable, Optional, Union

SSEEvent = Union[str, bytes]

SSE_MAX_EVENTS = "SSE_MAX_EVENTS"
SSE_MAX_BYTES = "SSE_MAX_BYTES"
SSE_MAX_DURATION = "SSE_MAX_DURATION"


@dataclass(frozen=True)
class SSEGuardTermination:
    reason_code: str
    max_events: Optional[int]
    max_bytes: Optional[int]
    max_duration_ms: Optional[int]
    observed_events: int
    observed_bytes: int
    observed_duration_ms: int


class SSEGuard:
    """Enforce deterministic limits on an async iterator of SSE events."""

    def __init__(
        self,
        *,
        max_duration_ms: Optional[int] = None,
        max_events: Optional[int] = None,
        max_bytes: Optional[int] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_duration_ms is not None and max_duration_ms <= 0:
            raise ValueError("max_duration_ms must be > 0 when provided")
        if max_events is not None and max_events <= 0:
            raise ValueError("max_events must be > 0 when provided")
        if max_bytes is not None and max_bytes <= 0:
            raise ValueError("max_bytes must be > 0 when provided")
        self._max_duration_ms = max_duration_ms
        self._max_events = max_events
        self._max_bytes = max_bytes
        self._clock = clock
        self._last_termination: Optional[SSEGuardTermination] = None

    @property
    def last_termination(self) -> Optional[SSEGuardTermination]:
        return self._last_termination

    async def wrap(self, events: AsyncIterator[SSEEvent]) -> AsyncIterator[SSEEvent]:
        """Yield events until a limit is reached, then terminate cleanly."""
        start = self._clock()
        event_count = 0
        byte_count = 0
        self._last_termination = None

        async for event in events:
            if self._max_events is not None and event_count >= self._max_events:
                self._last_termination = SSEGuardTermination(
                    reason_code=SSE_MAX_EVENTS,
                    max_events=self._max_events,
                    max_bytes=self._max_bytes,
                    max_duration_ms=self._max_duration_ms,
                    observed_events=event_count,
                    observed_bytes=byte_count,
                    observed_duration_ms=int((self._clock() - start) * 1000),
                )
                break
            if self._max_duration_ms is not None:
                elapsed_ms = (self._clock() - start) * 1000
                if elapsed_ms >= self._max_duration_ms:
                    self._last_termination = SSEGuardTermination(
                        reason_code=SSE_MAX_DURATION,
                        max_events=self._max_events,
                        max_bytes=self._max_bytes,
                        max_duration_ms=self._max_duration_ms,
                        observed_events=event_count,
                        observed_bytes=byte_count,
                        observed_duration_ms=int(elapsed_ms),
                    )
                    break

            event_size = _event_size_bytes(event)
            if self._max_bytes is not None and byte_count + event_size > self._max_bytes:
                self._last_termination = SSEGuardTermination(
                    reason_code=SSE_MAX_BYTES,
                    max_events=self._max_events,
                    max_bytes=self._max_bytes,
                    max_duration_ms=self._max_duration_ms,
                    observed_events=event_count,
                    observed_bytes=byte_count,
                    observed_duration_ms=int((self._clock() - start) * 1000),
                )
                break

            yield event
            event_count += 1
            byte_count += event_size


def _event_size_bytes(event: SSEEvent) -> int:
    if isinstance(event, str):
        return len(event.encode("utf-8"))
    if isinstance(event, bytes):
        return len(event)
    raise TypeError(f"Unsupported event type: {type(event)!r}")


__all__ = [
    "SSEGuard",
    "SSEGuardTermination",
    "SSE_MAX_BYTES",
    "SSE_MAX_DURATION",
    "SSE_MAX_EVENTS",
]
