"""Observability & Trace (OTCS) implementation."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Iterator, Optional

from ..types import TraceContext

logger = logging.getLogger("cccs.observability")


@dataclass
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None


class ObservabilityService:
    """Generates trace/span IDs and structured logs."""

    def __init__(self, time_fn: Callable[[], float] = time.time):
        self._time_fn = time_fn
        self._spans: Dict[str, SpanRecord] = {}

    def _new_trace_id(self) -> str:
        return uuid.uuid4().hex

    def _new_span_id(self) -> str:
        return uuid.uuid4().hex[:16]

    @contextmanager
    def start_span(self, name: str, parent: Optional[TraceContext] = None) -> Iterator[TraceContext]:
        trace_id = parent.trace_id if parent else self._new_trace_id()
        span_id = self._new_span_id()
        ctx = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent.span_id if parent else None,
            name=name,
            start_time=datetime.fromtimestamp(self._time_fn(), tz=timezone.utc),
        )
        self._spans[span_id] = SpanRecord(**ctx.__dict__)
        self.log_info(f"start_span:{name}", ctx)
        try:
            yield ctx
        finally:
            record = self._spans[span_id]
            record.end_time = datetime.fromtimestamp(self._time_fn(), tz=timezone.utc)
            self.log_info(f"end_span:{name}", ctx)

    def log_info(self, message: str, trace: Optional[TraceContext] = None, **extra) -> None:
        self._log(logging.INFO, message, trace, **extra)

    def log_error(self, message: str, trace: Optional[TraceContext] = None, **extra) -> None:
        self._log(logging.ERROR, message, trace, **extra)

    def _log(self, level: int, message: str, trace: Optional[TraceContext], **extra) -> None:
        payload = {
            "message": message,
            "trace_id": trace.trace_id if trace else None,
            "span_id": trace.span_id if trace else None,
            **extra,
        }
        logger.log(level, payload)


