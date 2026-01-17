"""
Trace context utilities for ZeroUI Observability Layer.

W3C Trace Context (traceparent, tracestate) implementation for Python.
"""

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Optional

try:
    from ...cccs.observability.service import ObservabilityService, TraceContext as CCCSTraceContext
    CCCS_AVAILABLE = True
except ImportError:
    CCCS_AVAILABLE = False
    ObservabilityService = None  # type: ignore
    CCCSTraceContext = None  # type: ignore

logger = logging.getLogger(__name__)

# W3C Trace Context format
# traceparent: 00-{trace-id}-{parent-id}-{trace-flags}
TRACEPARENT_PATTERN = re.compile(
    r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$",
    re.IGNORECASE
)


@dataclass
class TraceContext:
    """
    Trace context for distributed tracing.

    Per W3C Trace Context standard.
    """

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: str = "01"  # Default: sampled
    tracestate: Optional[str] = None

    def to_traceparent(self) -> str:
        """
        Generate traceparent header value.

        Returns:
            traceparent header string
        """
        parent_id = self.parent_span_id or "0" * 16
        return f"00-{self.trace_id}-{parent_id}-{self.trace_flags}"

    @classmethod
    def from_traceparent(cls, traceparent: str) -> Optional["TraceContext"]:
        """
        Parse traceparent header value.

        Args:
            traceparent: traceparent header string

        Returns:
            TraceContext or None if invalid
        """
        match = TRACEPARENT_PATTERN.match(traceparent.strip())
        if not match:
            logger.warning(f"Invalid traceparent format: {traceparent}")
            return None

        version, trace_id, parent_id, trace_flags = match.groups()

        # Validate version (currently only 00 is supported)
        if version != "00":
            logger.warning(f"Unsupported traceparent version: {version}")
            return None

        # Normalize to lowercase
        trace_id = trace_id.lower()
        parent_id = parent_id.lower()
        trace_flags = trace_flags.lower()

        return cls(
            trace_id=trace_id,
            span_id=parent_id,  # Current span uses parent_id as span_id
            parent_span_id=parent_id if parent_id != "0" * 16 else None,
            trace_flags=trace_flags,
        )

    def create_child(self) -> "TraceContext":
        """
        Create child trace context.

        Returns:
            New TraceContext with new span_id, current span as parent
        """
        new_span_id = generate_span_id()
        return TraceContext(
            trace_id=self.trace_id,
            span_id=new_span_id,
            parent_span_id=self.span_id,
            trace_flags=self.trace_flags,
            tracestate=self.tracestate,
        )


def generate_trace_id() -> str:
    """
    Generate new trace ID (32 hex characters).

    Returns:
        32-character hex string
    """
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """
    Generate new span ID (16 hex characters).

    Returns:
        16-character hex string
    """
    return uuid.uuid4().hex[:16]


def parse_traceparent(traceparent: Optional[str]) -> Optional[TraceContext]:
    """
    Parse traceparent header value.

    Args:
        traceparent: traceparent header string or None

    Returns:
        TraceContext or None if invalid/missing
    """
    if not traceparent:
        return None
    return TraceContext.from_traceparent(traceparent)


def get_or_create_trace_context(traceparent: Optional[str] = None) -> TraceContext:
    """
    Get or create trace context from traceparent header or generate new.

    Args:
        traceparent: Optional traceparent header string

    Returns:
        TraceContext (parsed from traceparent or newly generated)
    """
    if traceparent:
        ctx = TraceContext.from_traceparent(traceparent)
        if ctx:
            return ctx

    # Generate new trace context
    return TraceContext(
        trace_id=generate_trace_id(),
        span_id=generate_span_id(),
    )


def generate_traceparent(
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    trace_flags: str = "01",
) -> str:
    """
    Generate traceparent header value.

    Args:
        trace_id: Trace ID (32 hex chars) or None to generate new
        parent_span_id: Parent span ID (16 hex chars) or None
        trace_flags: Trace flags (2 hex chars), default "01" (sampled)

    Returns:
        traceparent header string
    """
    if not trace_id:
        trace_id = generate_trace_id()
    if not parent_span_id:
        parent_span_id = "0" * 16

    # Normalize
    trace_id = trace_id.lower()
    parent_span_id = parent_span_id.lower()
    trace_flags = trace_flags.lower()

    return f"00-{trace_id}-{parent_span_id}-{trace_flags}"


def get_or_create_trace_context(
    traceparent: Optional[str] = None,
    cccs_service: Optional[ObservabilityService] = None,
) -> TraceContext:
    """
    Get trace context from traceparent or create new.

    Args:
        traceparent: Optional traceparent header
        cccs_service: Optional CCCS ObservabilityService for integration

    Returns:
        TraceContext (from header or newly created)
    """
    # Try to parse traceparent
    if traceparent:
        ctx = parse_traceparent(traceparent)
        if ctx:
            return ctx

    # Create new trace context
    trace_id = generate_trace_id()
    span_id = generate_span_id()

    # If CCCS available, use it for trace ID generation
    if cccs_service and CCCS_AVAILABLE:
        # CCCS generates trace IDs, but we'll use our own for consistency
        pass

    return TraceContext(
        trace_id=trace_id,
        span_id=span_id,
        trace_flags="01",  # Sampled
    )
