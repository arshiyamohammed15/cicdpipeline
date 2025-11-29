"""
Middleware for Integration Adapters Module.

What: IAM token validation, request logging, error handling
Why: Cross-cutting concerns for API requests
Reads/Writes: HTTP requests/responses
Contracts: PRD Section 11 (Authentication requirements)
Risks: Authentication bypass, error handling failures
"""

from __future__ import annotations

import logging
from typing import Callable

from datetime import datetime
from typing import Callable

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from .integrations.iam_client import IAMClient
from .models import ErrorResponse

logger = logging.getLogger(__name__)


async def iam_auth_middleware(request: Request, call_next: Callable):
    """
    IAM authentication middleware.
    
    Validates IAM token for all requests except health checks.
    """
    # Skip auth for health checks and webhook endpoints
    if request.url.path in ["/health", "/metrics"] or request.url.path.startswith("/v1/integrations/webhooks/"):
        return await call_next(request)
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                error={
                    "code": "UNAUTHORIZED",
                    "message": "Missing or invalid Authorization header",
                    "details": {},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ).model_dump()
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Verify token
    iam_client = IAMClient()
    claims = iam_client.verify_token(token)
    if not claims:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                error={
                    "code": "UNAUTHORIZED",
                    "message": "Invalid or expired token",
                    "details": {},
                    "timestamp": datetime.utcnow().isoformat(),
                }
            ).model_dump()
        )
    
    # Add tenant_id to request state
    request.state.tenant_id = claims.get("tenant_id")
    request.state.user_id = claims.get("user_id")
    
    return await call_next(request)

