"""
Middleware for Evidence & Receipt Indexing Service (ERIS).

What: Request logging, rate limiting, IAM authentication middleware
Why: Cross-cutting concerns for all ERIS API requests
Reads/Writes: Reads request headers, writes logs, rate limit tracking
Contracts: Middleware contracts per PRD NFR-3, NFR-4
Risks: Performance impact, security vulnerabilities if misconfigured
"""

import json
import logging
import time
from datetime import datetime
from typing import Callable, Dict, Any, Optional
from collections import defaultdict

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .dependencies import verify_token, extract_tenant_context

logger = logging.getLogger(__name__)


# Sub-feature 10.1: Rate Limiting Middleware

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware per PRD NFR-3.

    Per-tenant rate limits per endpoint with burst support.
    """

    def __init__(self, app):
        """Initialize rate limiting middleware."""
        super().__init__(app)
        self.rate_limits = {
            "/v1/evidence/receipts": {"default": 1000, "burst": 2000, "window": 10},
            "/v1/evidence/receipts/bulk": {"default": 1000, "burst": 2000, "window": 10},
            "/v1/evidence/receipts/courier-batch": {"default": 1000, "burst": 2000, "window": 10},
            "/v1/evidence/search": {"default": 100, "burst": 200, "window": 10},
            "/v1/evidence/aggregate": {"default": 100, "burst": 200, "window": 10},
            "/v1/evidence/export": {"default": 5, "burst": 5, "window": 60},  # PRD: 5 per minute per tenant
            "/v1/evidence/receipts/{receipt_id}/verify": {"default": 500, "burst": 500, "window": 10},
            "/v1/evidence/verify_range": {"default": 500, "burst": 500, "window": 10},  # PRD: 500 req/s for integrity endpoints
        }
        self.request_counts: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "window_start": time.time()})

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        path = request.url.path
        tenant_id = self._extract_tenant_id(request)

        # Get rate limit for path
        rate_limit = self._get_rate_limit(path)
        if not rate_limit:
            return await call_next(request)

        # Check rate limit
        key = f"{tenant_id}:{path}"
        current_time = time.time()
        request_data = self.request_counts[key]

        # Reset window if expired
        if current_time - request_data["window_start"] > rate_limit["window"]:
            request_data["count"] = 0
            request_data["window_start"] = current_time

        # Check limit
        if request_data["count"] >= rate_limit["default"]:
            # Track rate limit exceeded metric per NFR-5
            try:
                from .metrics import rate_limit_exceeded
                rate_limit_exceeded.inc(
                    tenant_id=tenant_id,
                    endpoint=path
                )
            except (ImportError, AttributeError):
                # Metrics may not be available, continue anyway
                pass
            
            retry_after = int(rate_limit["window"] - (current_time - request_data["window_start"]))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded",
                        "retryable": True,
                        "request_id": str(request.headers.get("X-Request-ID", "")),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rate_limit["default"]),
                    "X-RateLimit-Remaining": str(max(0, rate_limit["default"] - request_data["count"])),
                    "X-RateLimit-Reset": str(int(request_data["window_start"] + rate_limit["window"]))
                }
            )

        request_data["count"] += 1

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limit["default"])
        response.headers["X-RateLimit-Remaining"] = str(max(0, rate_limit["default"] - request_data["count"]))
        response.headers["X-RateLimit-Reset"] = str(int(request_data["window_start"] + rate_limit["window"]))

        return response

    def _extract_tenant_id(self, request: Request) -> str:
        """Extract tenant ID from request."""
        headers = dict(request.headers)
        context = extract_tenant_context(headers)
        return context.get("tenant_id", "unknown") if context else "unknown"

    def _get_rate_limit(self, path: str) -> Optional[Dict[str, Any]]:
        """Get rate limit configuration for path."""
        for pattern, limit in self.rate_limits.items():
            if pattern in path or path.startswith(pattern.replace("{receipt_id}", "")):
                return limit
        return None


# Sub-feature 10.2: Request Logging Middleware

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware per Rule 173.

    Structured JSON logging for all requests.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        start_time = time.time()
        request_id = request.headers.get("X-Request-ID", "")

        # Log request
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "service": "evidence-receipt-indexing-service",
            "version": "1.0.0",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown"
        }
        logger.info(json.dumps(log_data))

        # Process request
        response = await call_next(request)

        # Log response
        duration_ms = (time.time() - start_time) * 1000
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "service": "evidence-receipt-indexing-service",
            "version": "1.0.0",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms
        }
        logger.info(json.dumps(log_data))

        return response


# Sub-feature 10.3: IAM Authentication Middleware

class IAMAuthMiddleware(BaseHTTPMiddleware):
    """
    IAM authentication middleware per FR-6.

    Token verification and tenant context extraction.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with IAM authentication."""
        # Skip auth for health/metrics/config endpoints
        if request.url.path in ["/v1/evidence/health", "/v1/evidence/metrics", "/v1/evidence/config"]:
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Missing authorization token",
                        "retryable": False,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )

        # Extract token
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization

        # Verify token
        is_valid, claims, error = await verify_token(token)
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": error or "Invalid token",
                        "retryable": False,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )

        # Add claims to request state
        request.state.claims = claims
        # Extract tenant_id from claims (derived from IAM VerifyResponse.sub in dependencies.py)
        request.state.tenant_id = claims.get("tenant_id") if claims else None
        
        # Log tenant context extraction for debugging
        if claims and request.state.tenant_id:
            logger.debug("Tenant context extracted: tenant_id=%s, sub=%s", 
                        request.state.tenant_id, claims.get("sub"))

        return await call_next(request)
