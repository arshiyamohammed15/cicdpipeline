"""
Middleware for Key Management Service (KMS).

What: FastAPI middleware for request logging, rate limiting, and mTLS validation per KMS spec
Why: Enables observability, prevents abuse, ensures mTLS authentication per Rule 173, Rule 4083
Reads/Writes: Reads request headers and client certificates, writes structured logs (JSON format per Rule 4083)
Contracts: FastAPI middleware contract, W3C trace context propagation (Rule 1685), mTLS validation per KMS spec
Risks: Logging overhead, potential PII exposure if certificates logged without redaction, rate limit bypass
"""

import json
import logging
import os
import socket
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Callable, Dict, Any, Optional, Tuple

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Service metadata per Rule 62
SERVICE_NAME = "key-management-service"
SERVICE_VERSION = "0.1.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Rate limiting per KMS spec: conservative limits for cryptographic operations
RATE_LIMIT_RPS = 100
RATE_LIMIT_BURST = 500
RATE_LIMIT_BURST_WINDOW = 10


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
    Rate limiting middleware per KMS spec.

    Default: 100 RPS/client, burst 500 for 10s.
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
        Apply rate limiting per KMS spec.

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
                        "details": None,
                        "retryable": True
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
                        "details": None,
                        "retryable": True
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


class mTLSValidationMiddleware(BaseHTTPMiddleware):
    """
    mTLS validation middleware per KMS spec.

    Extracts tenant_id, environment, plane from client certificate.
    Validates certificate against internal CA via M32.
    """

    def __init__(self, app: ASGIApp, trust_plane=None):
        """
        Initialize mTLS validation middleware.

        Args:
            app: ASGI application
            trust_plane: MockM32TrustPlane instance for certificate validation
        """
        super().__init__(app)
        self.trust_plane = trust_plane

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate mTLS certificate and extract identity information.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object or 401 if mTLS validation fails
        """
        # Extract client certificate from request
        # In production, this would come from TLS connection
        client_cert = request.headers.get("X-Client-Certificate")

        # For development/testing, allow bypass if no certificate
        if not client_cert and SERVICE_ENV == "development":
            # Set default identity for development
            request.state.tenant_id = "dev-tenant"
            request.state.environment = "dev"
            request.state.plane = "laptop"
            request.state.module_id = "M21"  # Code identifier for EPC-1 (Identity & Access Management)
            return await call_next(request)

        if not client_cert:
            response = Response(
                content=json.dumps({
                    "error": {
                        "code": "UNAUTHENTICATED",
                        "message": "mTLS certificate required",
                        "details": None,
                        "retryable": False
                    }
                }),
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )
            return response

        # Validate certificate via M32
        if self.trust_plane:
            try:
                cert_bytes = client_cert.encode() if isinstance(client_cert, str) else client_cert
                is_valid, error, identity_info = self.trust_plane.validate_certificate(cert_bytes)

                if not is_valid:
                    response = Response(
                        content=json.dumps({
                            "error": {
                                "code": "UNAUTHENTICATED",
                                "message": f"Certificate validation failed: {error}",
                                "details": None,
                                "retryable": False
                            }
                        }),
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        media_type="application/json"
                    )
                    return response

                # Extract identity information
                request.state.tenant_id = identity_info.get("tenant_id")
                request.state.environment = identity_info.get("environment")
                request.state.plane = identity_info.get("plane")
                request.state.module_id = identity_info.get("module_id")
            except Exception as exc:
                logger.error(f"Certificate validation error: {exc}")
                response = Response(
                    content=json.dumps({
                        "error": {
                            "code": "UNAUTHENTICATED",
                            "message": f"Certificate validation error: {str(exc)}",
                            "details": None,
                            "retryable": False
                        }
                    }),
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    media_type="application/json"
                )
                return response
        else:
            # No trust plane available - set defaults for development
            request.state.tenant_id = "dev-tenant"
            request.state.environment = "dev"
            request.state.plane = "laptop"
            request.state.module_id = "M21"  # Code identifier for EPC-1 (Identity & Access Management)

        return await call_next(request)


class JWTValidationMiddleware(BaseHTTPMiddleware):
    """
    JWT validation middleware per KMS spec (optional but recommended).

    Validates JWT tokens from Authorization header, ensures consistency with mTLS identity.
    """

    def __init__(self, app: ASGIApp, iam=None):
        """
        Initialize JWT validation middleware.

        Args:
            app: ASGI application
            iam: MockM21IAM instance (EPC-1) for JWT verification
        """
        super().__init__(app)
        self.iam = iam

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Validate JWT token if present and ensure consistency with mTLS identity.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response object or 401 if JWT validation fails
        """
        # Extract JWT from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix

            # Validate JWT if IAM is available
            if self.iam:
                try:
                    is_valid, claims, error = self.iam.verify_jwt(token)

                    if not is_valid:
                        response = Response(
                            content=json.dumps({
                                "error": {
                                    "code": "UNAUTHENTICATED",
                                    "message": f"JWT validation failed: {error}",
                                    "details": None,
                                    "retryable": False
                                }
                            }),
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            media_type="application/json"
                        )
                        return response

                    # Check required claims
                    required_claims = ["sub", "module_id", "tenant_id", "environment"]
                    missing_claims = [claim for claim in required_claims if claim not in claims]
                    if missing_claims:
                        response = Response(
                            content=json.dumps({
                                "error": {
                                    "code": "UNAUTHENTICATED",
                                    "message": f"JWT missing required claims: {', '.join(missing_claims)}",
                                    "details": None,
                                    "retryable": False
                                }
                            }),
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            media_type="application/json"
                        )
                        return response

                    # Ensure consistency with mTLS identity
                    jwt_tenant_id = claims.get("tenant_id")
                    jwt_environment = claims.get("environment")
                    mtls_tenant_id = getattr(request.state, "tenant_id", None)
                    mtls_environment = getattr(request.state, "environment", None)

                    if jwt_tenant_id and mtls_tenant_id and jwt_tenant_id != mtls_tenant_id:
                        response = Response(
                            content=json.dumps({
                                "error": {
                                    "code": "UNAUTHENTICATED",
                                    "message": "JWT tenant_id does not match mTLS tenant_id",
                                    "details": None,
                                    "retryable": False
                                }
                            }),
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            media_type="application/json"
                        )
                        return response

                    if jwt_environment and mtls_environment and jwt_environment != mtls_environment:
                        response = Response(
                            content=json.dumps({
                                "error": {
                                    "code": "UNAUTHENTICATED",
                                    "message": "JWT environment does not match mTLS environment",
                                    "details": None,
                                    "retryable": False
                                }
                            }),
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            media_type="application/json"
                        )
                        return response

                    # Store validated claims in request state
                    request.state.jwt_claims = claims

                except Exception as exc:
                    logger.error(f"JWT validation error: {exc}")
                    response = Response(
                        content=json.dumps({
                            "error": {
                                "code": "UNAUTHENTICATED",
                                "message": f"JWT validation error: {str(exc)}",
                                "details": None,
                                "retryable": False
                            }
                        }),
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        media_type="application/json"
                    )
                    return response
            # If no IAM available, JWT is optional (development mode)

        return await call_next(request)
