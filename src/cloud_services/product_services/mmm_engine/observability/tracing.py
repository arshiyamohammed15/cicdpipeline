"""
OpenTelemetry distributed tracing for MMM Engine.

Per PRD Section FR-15, implements distributed tracing with span creation
for decision flow and trace export to observability backend.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import OpenTelemetry, but make it optional
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning("OpenTelemetry not available, tracing disabled")


class TracingService:
    """OpenTelemetry tracing service for MMM Engine."""

    def __init__(self):
        if not OPENTELEMETRY_AVAILABLE:
            self.tracer = None
            return

        # Initialize tracer provider
        resource = Resource.create({"service.name": "mmm-engine"})
        provider = TracerProvider(resource=resource)

        # Configure exporter from environment
        otlp_endpoint = os.getenv("OTLP_EXPORTER_ENDPOINT")
        if otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)
        self.tracer = trace.get_tracer("mmm-engine")

    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        parent_span: Optional[Any] = None,
    ):
        """
        Create a span context manager.

        Args:
            name: Span name
            attributes: Span attributes (tenant_id, actor_id, etc.)
            parent_span: Optional parent span context
        """
        if not self.tracer:
            yield None
            return

        if parent_span:
            ctx = trace.set_span_in_context(parent_span)
        else:
            ctx = None

        with self.tracer.start_as_current_span(name, context=ctx) as span:
            if attributes and span:
                for key, value in attributes.items():
                    if value is not None:
                        span.set_attribute(key, str(value))
            yield span

    def get_current_span(self) -> Optional[Any]:
        """Get current active span."""
        if not self.tracer:
            return None
        return trace.get_current_span()

    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID for logging."""
        span = self.get_current_span()
        if span and hasattr(span, "get_span_context"):
            ctx = span.get_span_context()
            if ctx and ctx.is_valid:
                return format(ctx.trace_id, "032x")
        return None


# Global tracing service instance
_tracing_service: Optional[TracingService] = None


def get_tracing_service() -> TracingService:
    """Get global tracing service instance."""
    global _tracing_service
    if _tracing_service is None:
        _tracing_service = TracingService()
    return _tracing_service

