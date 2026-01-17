"""
Trace context propagation for ZeroUI Observability Layer.

W3C Trace Context implementation for end-to-end correlation.
"""

from .trace_context import TraceContext, parse_traceparent, generate_traceparent

__all__ = ["TraceContext", "parse_traceparent", "generate_traceparent"]
