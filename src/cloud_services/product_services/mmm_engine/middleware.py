"""
IAM authentication middleware for MMM Engine.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .service_registry import get_iam

logger = logging.getLogger(__name__)


PUBLIC_PATHS = {"/health", "/ready", "/v1/mmm/health", "/v1/mmm/ready", "/v1/mmm/metrics"}


async def verify_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    iam = get_iam()
    return iam.verify_token(token)


class IAMAuthMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware enforcing IAM authentication."""

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        authorization = request.headers.get("Authorization")
        if not authorization:
            return self._unauthorized("Missing authorization token")

        token = authorization[7:] if authorization.startswith("Bearer ") else authorization
        is_valid, claims, error = await verify_token(token)
        if not is_valid or not claims:
            return self._unauthorized(error or "Invalid token")

        request.state.claims = claims
        request.state.tenant_id = claims.get("tenant_id")
        request.state.roles = claims.get("roles", [])
        return await call_next(request)

    @staticmethod
    def _unauthorized(message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": message,
                    "retryable": False,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
        )


