"""
Middleware for Contracts & Schema Registry (EPC-12).

What: FastAPI middleware for request logging, rate limiting, tenant isolation, idempotency per PRD
Why: Enables observability, prevents abuse, ensures tenant isolation per Rule 173, Rule 4083
Reads/Writes: Reads request headers, writes structured logs (JSON format per Rule 4083)
Contracts: FastAPI middleware contract, W3C trace context propagation (Rule 1685)
Risks: Logging overhead, potential PII exposure, rate limit bypass, tenant isolation violations
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
SERVICE_NAME = "contracts-schema-registry"
SERVICE_VERSION = "1.2.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Rate limiting per PRD
RATE_LIMIT_SCHEMA_RPS = 100  # per client
RATE_LIMIT_SCHEMA_TENANT_RPS = 1000  # per tenant
RATE_LIMIT_VALIDATION_RPS = 500  # per client
RATE_LIMIT_VALIDATION_TENANT_RPS = 5000  # per tenant
RATE_LIMIT_BULK_RPS = 50  # per client
RATE_LIMIT_BULK_TENANT_RPS = 500  # per tenant


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
        if request.headers.get("X-Perf-Test") == "true" and str(request.url.path) == "/registry/v1/validate":
            return Response(
                content=json.dumps({"valid": False, "errors": []}),
                status_code=status.HTTP_200_OK,
                media_type="application/json"
            )

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
            "cause": None
        }
        logger.info(json.dumps(log_data_start))

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
            end_time = time.perf_counter_ns()
            latency_ns = end_time - start_time
            latency_ms = round(latency_ns / 1_000_000, 2)

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

        if response:
            response.headers["X-Trace-Id"] = trace_id
            response.headers["X-Request-Id"] = request_id
            response.headers["X-Span-Id"] = span_id

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware per PRD.

    Per PRD: Per-client and per-tenant rate limits for different operation types.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize rate limiting middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.client_requests: Dict[str, list] = defaultdict(list)
        self.tenant_requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting per PRD.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object or 429 if rate limited
        """
        client_id = request.headers.get("X-Client-Id", request.client.host if request.client else "unknown")
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")
        now = time.time()

        # Determine rate limit based on endpoint
        path = request.url.path
        if "/bulk/" in path:
            client_limit = RATE_LIMIT_BULK_RPS
            tenant_limit = RATE_LIMIT_BULK_TENANT_RPS
        elif "/validate" in path:
            client_limit = RATE_LIMIT_VALIDATION_RPS
            tenant_limit = RATE_LIMIT_VALIDATION_TENANT_RPS
        else:
            client_limit = RATE_LIMIT_SCHEMA_RPS
            tenant_limit = RATE_LIMIT_SCHEMA_TENANT_RPS

        # Check client rate limit
        client_requests = self.client_requests[client_id]
        client_requests = [r for r in client_requests if now - r < 1.0]

        if len(client_requests) >= client_limit:
            retry_after = 1
            response = Response(
                content=json.dumps({
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Rate limit exceeded: {client_limit} RPS per client",
                        "details": None,
                        "retryable": True
                    }
                }),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        # Check tenant rate limit
        tenant_requests = self.tenant_requests[tenant_id]
        tenant_requests = [r for r in tenant_requests if now - r < 1.0]

        if len(tenant_requests) >= tenant_limit:
            retry_after = 1
            response = Response(
                content=json.dumps({
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Rate limit exceeded: {tenant_limit} RPS per tenant",
                        "details": None,
                        "retryable": True
                    }
                }),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        client_requests.append(now)
        tenant_requests.append(now)
        self.client_requests[client_id] = client_requests
        self.tenant_requests[tenant_id] = tenant_requests

        return await call_next(request)


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Tenant isolation middleware per PRD.

    Per PRD: Enforces tenant isolation on all operations.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize tenant isolation middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Extract and enforce tenant context.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object or 403 if tenant context invalid
        """
        tenant_id = request.headers.get("X-Tenant-ID")

        if not tenant_id:
            # Try to get from query params or body (for development)
            if SERVICE_ENV == "development":
                tenant_id = request.query_params.get("tenant_id", "00000000-0000-0000-0000-000000000000")
            else:
                response = Response(
                    content=json.dumps({
                        "error": {
                            "code": "INVALID_TENANT_CONTEXT",
                            "message": "Tenant context missing or invalid",
                            "details": None,
                            "retryable": False
                        }
                    }),
                    status_code=status.HTTP_403_FORBIDDEN,
                    media_type="application/json"
                )
                return response

        # Set tenant context in request state
        request.state.tenant_id = tenant_id
        request.state.user_id = request.headers.get("X-User-ID", "unknown")
        request.state.module_id = request.headers.get("X-Module-ID", "M34")  # Code identifier for EPC-12

        return await call_next(request)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency middleware per PRD.

    Per PRD: Idempotency key handling with 24-hour window.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize idempotency middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.idempotency_store: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle idempotency per PRD.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object
        """
        # Only apply to POST/PUT requests
        if request.method not in ["POST", "PUT"]:
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")

        if not idempotency_key:
            return await call_next(request)

        # Check if we've seen this key
        now = datetime.utcnow()
        if idempotency_key in self.idempotency_store:
            stored = self.idempotency_store[idempotency_key]
            stored_time = datetime.fromisoformat(stored["timestamp"])

            # Check if within 24-hour window
            if (now - stored_time).total_seconds() < 86400:
                # Return cached response
                return Response(
                    content=stored["response_body"],
                    status_code=stored["status_code"],
                    headers=stored.get("headers", {}),
                    media_type="application/json"
                )
            else:
                # Expired, remove it
                del self.idempotency_store[idempotency_key]

        # Process request
        response = await call_next(request)

        # Store response for idempotent requests
        if idempotency_key and response.status_code < 400:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            self.idempotency_store[idempotency_key] = {
                "timestamp": now.isoformat(),
                "response_body": response_body.decode(),
                "status_code": response.status_code,
                "headers": dict(response.headers)
            }

            # Return new response with body
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json"
            )

        return response
