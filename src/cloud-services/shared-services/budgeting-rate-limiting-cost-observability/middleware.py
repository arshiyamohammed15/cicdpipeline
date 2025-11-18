"""
Middleware for Budgeting, Rate-Limiting & Cost Observability (M35).

What: Request logging, rate limiting, authentication middleware
Why: Provides cross-cutting concerns per PRD
Reads/Writes: Reads request data, writes logs
Contracts: Middleware contracts per ZeroUI standards
Risks: Middleware failures, performance degradation
"""

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware per ZeroUI standards."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response."""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"Request-ID: {request_id}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {response.status_code} "
            f"Request-ID: {request_id} "
            f"Process-Time: {process_time:.3f}s"
        )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for M35's own APIs per PRD lines 3100-3118."""

    def __init__(self, app: ASGIApp):
        """Initialize rate limiting middleware."""
        super().__init__(app)
        self.rate_limits = {}  # Would use Redis in production

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting to requests."""
        # Skip rate limiting for health and metrics endpoints
        if request.url.path in ["/budget/v1/health", "/budget/v1/metrics"]:
            return await call_next(request)

        # Extract tenant/user identifier (would come from JWT in production)
        tenant_id = request.headers.get("X-Tenant-ID", "default")
        user_id = request.headers.get("X-User-ID", "default")

        # Check rate limit (simplified - would use Redis in production)
        key = f"{tenant_id}:{request.url.path}"
        current_time = time.time()
        window_start = int(current_time // 60) * 60  # 1-minute windows

        if key not in self.rate_limits:
            self.rate_limits[key] = {"window": window_start, "count": 0}

        if self.rate_limits[key]["window"] != window_start:
            self.rate_limits[key] = {"window": window_start, "count": 0}

        # Default limit: 1000 requests per minute per tenant
        limit = 1000
        if self.rate_limits[key]["count"] >= limit:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail={
                    "error_code": "RATE_LIMIT_VIOLATED",
                    "message": "Rate limit exceeded",
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window_start + 60),
                    "Retry-After": "60"
                }
            )

        self.rate_limits[key]["count"] += 1

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(limit - self.rate_limits[key]["count"])
        response.headers["X-RateLimit-Reset"] = str(window_start + 60)

        return response


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """JWT validation middleware using M21 IAM."""

    def __init__(self, app: ASGIApp, iam):
        """Initialize JWT validation middleware."""
        super().__init__(app)
        self.iam = iam

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate JWT token."""
        # Skip validation for health endpoint
        if request.url.path == "/budget/v1/health":
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "UNAUTHORIZED",
                    "message": "Missing or invalid authorization token",
                    "correlation_id": str(uuid.uuid4())
                }
            )

        token = auth_header.replace("Bearer ", "")
        is_valid, claims, error = self.iam.verify_jwt(token)

        if not is_valid:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=401,
                detail={
                    "error_code": "UNAUTHORIZED",
                    "message": error or "Invalid token",
                    "correlation_id": str(uuid.uuid4())
                }
            )

        # Set tenant context in request state
        request.state.tenant_id = claims.get("tenant_id", "default")
        request.state.user_id = claims.get("sub", "default")

        return await call_next(request)

