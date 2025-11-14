"""
Middleware for Configuration & Policy Management (M23).

What: FastAPI middleware for request logging, rate limiting per PRD v1.1.0
Why: Enables observability, prevents abuse per Rule 173, Rule 4083
Reads/Writes: Reads request headers, writes structured logs (JSON format per Rule 4083), rate limit tracking
Contracts: FastAPI middleware contract, W3C trace context propagation (Rule 1685), rate limiting per PRD
Risks: Logging overhead, potential PII exposure, rate limit bypass
"""

import json
import logging
import os
import socket
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Optional

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Service metadata per Rule 62
SERVICE_NAME = "configuration-policy-management"
SERVICE_VERSION = "1.1.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Rate limiting per PRD (lines 1095-1104)
RATE_LIMIT_POLICY_EVAL = 10000  # 10,000 RPS
RATE_LIMIT_CONFIG_RETRIEVAL = 20000  # 20,000 RPS
RATE_LIMIT_COMPLIANCE_CHECK = 5000  # 5,000 RPS
RATE_LIMIT_BURST = 1000  # Burst limit
RATE_LIMIT_BURST_WINDOW = 10  # 10 seconds


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request.start and request.end per Rule 173."""

    def __init__(self, app: ASGIApp):
        """
        Initialize request logging middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log start/end events per Rule 173 and Rule 4083.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object
        """
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

        route = str(request.url.path)
        method = request.method

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
            "cause": None,
            "log_schema_version": "1.0"
        }
        logger.info(json.dumps(log_data_start))

        try:
            response = await call_next(request)
            status_code = response.status_code

            end_time = time.perf_counter_ns()
            duration_ms = (end_time - start_time) / 1_000_000

            log_data_end = {
                "timestamp": time.time(),
                "level": "INFO",
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
                "duration": duration_ms,
                "attempt": 1,
                "retryable": False,
                "severity": "INFO" if status_code < 400 else "ERROR",
                "cause": None,
                "statusCode": status_code,
                "log_schema_version": "1.0"
            }
            logger.info(json.dumps(log_data_end))

            return response

        except Exception as exc:
            end_time = time.perf_counter_ns()
            duration_ms = (end_time - start_time) / 1_000_000

            log_data_error = {
                "timestamp": time.time(),
                "level": "ERROR",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "env": SERVICE_ENV,
                "host": SERVICE_HOST,
                "operation": "request.error",
                "traceId": trace_id,
                "spanId": span_id,
                "parentSpanId": parent_span_id,
                "requestId": request_id,
                "route": route,
                "method": method,
                "duration": duration_ms,
                "attempt": 1,
                "retryable": False,
                "severity": "ERROR",
                "cause": str(exc),
                "log_schema_version": "1.0"
            }
            logger.error(json.dumps(log_data_error))

            raise


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting per PRD."""

    def __init__(self, app: ASGIApp):
        """
        Initialize rate limiting middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.request_counts: Dict[str, list] = defaultdict(list)
        self.burst_counts: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with rate limiting.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object

        Raises:
            HTTPException: If rate limit exceeded
        """
        client_id = request.headers.get("X-Client-Id", request.client.host if request.client else "unknown")
        route = str(request.url.path)

        # Determine rate limit based on route
        if "/policies/" in route and "/evaluate" in route:
            rate_limit = RATE_LIMIT_POLICY_EVAL
        elif "/configurations" in route:
            rate_limit = RATE_LIMIT_CONFIG_RETRIEVAL
        elif "/compliance/check" in route:
            rate_limit = RATE_LIMIT_COMPLIANCE_CHECK
        else:
            rate_limit = 1000  # Default rate limit

        now = time.time()

        # Clean old entries
        self.request_counts[client_id] = [
            ts for ts in self.request_counts[client_id]
            if now - ts < 1.0  # 1 second window
        ]

        # Check rate limit
        if len(self.request_counts[client_id]) >= rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "error_code": "RATE_LIMITED",
                        "message": f"Rate limit exceeded: {rate_limit} requests/second",
                        "details": None,
                        "correlation_id": str(uuid.uuid4()),
                        "retriable": True,
                        "tenant_id": None
                    }
                }
            )

        # Add current request
        self.request_counts[client_id].append(now)

        # Check burst limit
        self.burst_counts[client_id] = [
            ts for ts in self.burst_counts[client_id]
            if now - ts < RATE_LIMIT_BURST_WINDOW
        ]

        if len(self.burst_counts[client_id]) >= RATE_LIMIT_BURST:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "error_code": "RATE_LIMITED",
                        "message": f"Burst limit exceeded: {RATE_LIMIT_BURST} requests/{RATE_LIMIT_BURST_WINDOW}s",
                        "details": None,
                        "correlation_id": str(uuid.uuid4()),
                        "retriable": True,
                        "tenant_id": None
                    }
                }
            )

        self.burst_counts[client_id].append(now)

        return await call_next(request)
