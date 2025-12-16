"""Dependency injection helpers."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import List, Optional
import os

from fastapi import HTTPException, Request, status
from sqlmodel.ext.asyncio.session import AsyncSession
import jwt

from .config import get_settings
from .database.session import engine, init_db

settings = get_settings()


def get_engine():
    return engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session


async def on_startup() -> None:
    await init_db()


async def on_shutdown() -> None:
    pass


@dataclass
class RequestContext:
    tenant_id: str
    actor_id: str
    roles: List[str]
    allowed_tenants: List[str]
    token_sub: Optional[str] = None

    def is_global(self) -> bool:
        return "*" in self.allowed_tenants or "global_admin" in self.roles

    def can_access(self, target_tenant: str) -> bool:
        if target_tenant == self.tenant_id:
            return True
        if self.is_global():
            return True
        return target_tenant in self.allowed_tenants


def _decode_bearer_token(token: str) -> dict:
    """
    Validate and decode a bearer JWT using HS256 and shared secret.
    Fail closed if secret is not configured or verification fails.
    """
    secret = os.getenv("ALERTING_JWT_SECRET")
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
        )
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"], options={"require": ["sub", "tenant_id"]})
    except Exception as exc:  # pragma: no cover - explicit failure path
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc
    return claims


async def get_request_context(request: Request) -> RequestContext:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    claims = _decode_bearer_token(auth_header.replace("Bearer ", "", 1))

    tenant_id = request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Tenant-ID header",
        )
    if claims.get("tenant_id") != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch",
        )

    actor_id = request.headers.get("X-Actor-ID", "system")
    roles = [role.strip() for role in request.headers.get("X-Roles", "").split(",") if role.strip()]
    allowed_tenants = [
        tenant.strip() for tenant in request.headers.get("X-Allow-Tenants", "").split(",") if tenant.strip()
    ]
    return RequestContext(
        tenant_id=tenant_id,
        actor_id=actor_id,
        roles=roles,
        allowed_tenants=allowed_tenants,
        token_sub=claims.get("sub"),
    )
