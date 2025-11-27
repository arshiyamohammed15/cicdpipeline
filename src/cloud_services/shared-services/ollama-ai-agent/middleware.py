"""
Logging middleware for Ollama AI Agent service.

What: FastAPI middleware for request/response logging with traceId, requestId, latency tracking
Why: Enables observability per Rule 173 - log request.start and request.end with correlation IDs
Reads/Writes: Reads request headers, writes structured logs (JSON format per Rule 4083)
Contracts: FastAPI middleware contract, W3C trace context propagation (Rule 1685)
Risks: Logging overhead, potential PII exposure if prompts logged without redaction
"""

import json
import logging
import os
import socket
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Service metadata per Rule 62
SERVICE_NAME = "ollama-ai-agent"
SERVICE_VERSION = "2.0.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request.start and request.end per Rule 173."""

    def __init__(self, app: ASGIApp):
        """
        Initialize request logging middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    # Note: ASGI middleware requires async/await (Rule 332 exception - framework requirement)
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log start/end events per Rule 173 and Rule 4083.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object
        """
        # Generate or extract W3C trace context per Rule 1685
        traceparent = request.headers.get("traceparent", "")
        if traceparent:
            parts = traceparent.split("-")
            trace_id = parts[1] if len(parts) > 1 else str(uuid.uuid4())
            span_id = parts[2] if len(parts) > 2 else str(uuid.uuid4())[:16]
            parent_span_id = parts[3] if len(parts) > 3 else None
        else:
            trace_id = str(uuid.uuid4())
            span_id = str(uuid.uuid4())[:16]
            parent_span_id = None

        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))

        # Extract route and method
        route = str(request.url.path)
        method = request.method

        # Log request.start per Rule 173, Rule 4083, Rule 62, Rule 1641
        start_time = time.perf_counter_ns()
        log_data_start = {
            "timestamp": time.time(),
            "level": "INFO",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "request.start",
            "traceId": trace_id,
            "spanId": span_id,
            "parentSpanId": parent_span_id,
            "requestId": request_id,
            "route": route,
            "method": method,
            "duration": None,
            "attempt": 1,
            "retryable": False,
            "severity": "INFO",
            "cause": None
        }
        logger.info(json.dumps(log_data_start))

        # Process request
        status_code = 500
        response = None
        error_code = None
        error_message = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            status_code = 500
            error_code = "INTERNAL_ERROR"
            error_message = str(exc)
            raise
        finally:
            # Calculate latency in milliseconds per Rule 1531
            end_time = time.perf_counter_ns()
            latency_ns = end_time - start_time
            latency_ms = round(latency_ns / 1_000_000, 2)

            # Log request.end per Rule 173, Rule 4083, Rule 62, Rule 1641
            log_data_end = {
                "timestamp": time.time(),
                "level": "INFO" if status_code < 400 else "ERROR",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "env": SERVICE_ENV,
                "host": SERVICE_HOST,
                "operation": "request.end",
                "traceId": trace_id,
                "spanId": span_id,
                "parentSpanId": parent_span_id,
                "requestId": request_id,
                "route": route,
                "method": method,
                "status": status_code,
                "duration": latency_ms,
                "attempt": 1,
                "retryable": False,
                "severity": "INFO" if status_code < 400 else "ERROR",
                "error.code": error_code,
                "cause": error_message
            }
            logger.info(json.dumps(log_data_end))

        # Add trace headers to response per Rule 1685
        if response:
            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Request-Id"] = request_id
            response.headers["X-Span-Id"] = span_id

        return response
