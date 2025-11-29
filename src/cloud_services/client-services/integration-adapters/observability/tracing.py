"""
OpenTelemetry tracing for Integration Adapters Module.

What: Distributed tracing per FR-12
Why: Request tracing and correlation
Reads/Writes: OpenTelemetry spans
Contracts: PRD FR-12 (Observability & Diagnostics)
Risks: Tracing overhead, span propagation errors
"""

from __future__ import annotations

from typing import Optional
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.trace import Span, Tracer
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Fallback: Mock tracing
    class Span:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def set_attribute(self, *args, **kwargs):
            pass
    
    class Tracer:
        def start_span(self, *args, **kwargs):
            return Span()
    
    trace = None


class TracingService:
    """OpenTelemetry tracing service."""

    def __init__(self):
        """Initialize tracing service."""
        if OPENTELEMETRY_AVAILABLE:
            self.tracer = trace.get_tracer(__name__)
        else:
            self.tracer = Tracer()

    @contextmanager
    def trace_http_call(
        self,
        method: str,
        url: str,
        provider_id: Optional[str] = None,
        connection_id: Optional[str] = None,
    ):
        """
        Create span for HTTP call.
        
        Args:
            method: HTTP method
            url: Request URL
            provider_id: Optional provider ID
            connection_id: Optional connection ID
        """
        with self.tracer.start_span(f"http.{method}") as span:
            if isinstance(span, Span):
                span.set_attribute("http.method", method)
                span.set_attribute("http.url", url)
                if provider_id:
                    span.set_attribute("integration.provider_id", provider_id)
                if connection_id:
                    span.set_attribute("integration.connection_id", connection_id)
            yield span

    @contextmanager
    def trace_normalization(
        self,
        provider_id: str,
        event_type: str,
    ):
        """
        Create span for event normalization.
        
        Args:
            provider_id: Provider identifier
            event_type: Event type
        """
        with self.tracer.start_span("event.normalize") as span:
            if isinstance(span, Span):
                span.set_attribute("integration.provider_id", provider_id)
                span.set_attribute("event.type", event_type)
            yield span

    @contextmanager
    def trace_webhook_processing(
        self,
        provider_id: str,
        connection_id: str,
        event_type: str,
    ):
        """
        Create span for webhook processing.
        
        Args:
            provider_id: Provider identifier
            connection_id: Connection ID
            event_type: Event type
        """
        with self.tracer.start_span("webhook.process") as span:
            if isinstance(span, Span):
                span.set_attribute("integration.provider_id", provider_id)
                span.set_attribute("integration.connection_id", connection_id)
                span.set_attribute("event.type", event_type)
            yield span


# Global tracing service
_tracing_service = TracingService()


def get_tracing_service() -> TracingService:
    """Get global tracing service instance."""
    return _tracing_service

