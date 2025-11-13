"""
Middleware for Identity & Access Management (IAM) service.

What: FastAPI middleware for request logging, rate limiting, and idempotency per IAM spec v1.1.0
Why: Enables observability, prevents abuse, ensures idempotent operations per Rule 173, Rule 4083
Reads/Writes: Reads request headers, writes structured logs (JSON format per Rule 4083), rate limit tracking
Contracts: FastAPI middleware contract, W3C trace context propagation (Rule 1685), rate limiting per IAM spec
Risks: Logging overhead, potential PII exposure if tokens logged without redaction, rate limit bypass
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
SERVICE_NAME = "identity-access-management"
SERVICE_VERSION = "1.1.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Rate limiting per IAM spec section 6: 50 RPS/client, burst 200/10s
RATE_LIMIT_RPS = 50
RATE_LIMIT_BURST = 200
RATE_LIMIT_BURST_WINDOW = 10

# Idempotency window per IAM spec section 6: 24h
IDEMPOTENCY_WINDOW_HOURS = 24


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
    Rate limiting middleware per IAM spec section 6.
    
    Default: 50 RPS/client, burst 200 for 10s.
    429 with Retry-After header.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize rate limiting middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.client_requests: Dict[str, list] = defaultdict(list)
        self.client_bursts: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Apply rate limiting per IAM spec section 6.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object or 429 if rate limited
        """
        client_id = request.headers.get("X-Client-Id", request.client.host if request.client else "unknown")
        now = time.time()

        requests = self.client_requests[client_id]
        requests = [r for r in requests if now - r < 1.0]
        
        if len(requests) >= RATE_LIMIT_RPS:
            retry_after = 1
            response = Response(
                content=json.dumps({
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Rate limit exceeded: {RATE_LIMIT_RPS} RPS",
                        "details": None
                    }
                }),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        bursts = self.client_bursts[client_id]
        bursts = [b for b in bursts if now - b < RATE_LIMIT_BURST_WINDOW]
        
        if len(bursts) >= RATE_LIMIT_BURST:
            retry_after = RATE_LIMIT_BURST_WINDOW
            response = Response(
                content=json.dumps({
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": f"Burst limit exceeded: {RATE_LIMIT_BURST} requests in {RATE_LIMIT_BURST_WINDOW}s",
                        "details": None
                    }
                }),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json"
            )
            response.headers["Retry-After"] = str(retry_after)
            return response

        requests.append(now)
        bursts.append(now)
        self.client_requests[client_id] = requests
        self.client_bursts[client_id] = bursts

        return await call_next(request)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Idempotency middleware per IAM spec section 6.
    
    Required for /policies endpoint via X-Idempotency-Key.
    Server ensures single application per key within 24h window.
    """

    def __init__(self, app: ASGIApp):
        """
        Initialize idempotency middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.idempotency_keys: Dict[str, Dict[str, Any]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Handle idempotency per IAM spec section 6.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object
        """
        if request.method != "PUT" or "/policies" not in str(request.url.path):
            return await call_next(request)

        idempotency_key = request.headers.get("X-Idempotency-Key")
        if not idempotency_key:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "BAD_REQUEST",
                        "message": "X-Idempotency-Key header required for /policies endpoint",
                        "details": None
                    }
                }
            )

        now = datetime.utcnow()
        key_data = self.idempotency_keys.get(idempotency_key)
        
        if key_data:
            key_time = datetime.fromisoformat(key_data["timestamp"])
            if (now - key_time).total_seconds() < IDEMPOTENCY_WINDOW_HOURS * 3600:
                if "response" in key_data:
                    return Response(
                        content=json.dumps(key_data["response"]),
                        status_code=key_data.get("status_code", 202),
                        media_type="application/json"
                    )

        response = await call_next(request)
        
        if response.status_code < 400:
            response_body = None
            try:
                response_body = json.loads(response.body.decode())
            except Exception:
                pass
            
            self.idempotency_keys[idempotency_key] = {
                "timestamp": now.isoformat(),
                "response": response_body,
                "status_code": response.status_code
            }
            
            cleanup_time = now - timedelta(hours=IDEMPOTENCY_WINDOW_HOURS)
            self.idempotency_keys = {
                k: v for k, v in self.idempotency_keys.items()
                if datetime.fromisoformat(v["timestamp"]) > cleanup_time
            }

        return response

