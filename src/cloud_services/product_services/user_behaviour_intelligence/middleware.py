"""
IAM Authentication Middleware for UBI Module (EPC-9).

What: IAM token verification and tenant context extraction middleware
Why: Enforce authentication and authorization per PRD Section 11
Reads/Writes: HTTP request/response handling
Contracts: IAM API contract (POST /iam/v1/verify)
Risks: Authentication failures, token validation errors
"""

import logging
from datetime import datetime
from typing import Callable, Optional, Dict, Any, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .dependencies import MockM21IAM
from .service_registry import get_iam_instance

logger = logging.getLogger(__name__)


async def verify_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Verify JWT token via IAM.

    Args:
        token: JWT token string

    Returns:
        Tuple of (is_valid, claims_dict, error_message)
    """
    iam = get_iam_instance()
    return iam.verify_token(token)


class IAMAuthMiddleware(BaseHTTPMiddleware):
    """
    IAM authentication middleware per UBI PRD Section 11.

    Token verification and tenant context extraction.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process request with IAM authentication."""
        # Skip auth for health/ready endpoints
        if request.url.path in ["/health", "/ready", "/v1/ubi/health", "/v1/ubi/ready"]:
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
        # Extract tenant_id from claims
        request.state.tenant_id = claims.get("tenant_id") if claims else None
        
        # Extract roles for authorization
        request.state.roles = claims.get("roles", []) if claims else []
        
        # Log tenant context extraction for debugging
        if claims and request.state.tenant_id:
            logger.debug("Tenant context extracted: tenant_id=%s, sub=%s, roles=%s", 
                        request.state.tenant_id, claims.get("sub"), request.state.roles)

        return await call_next(request)

