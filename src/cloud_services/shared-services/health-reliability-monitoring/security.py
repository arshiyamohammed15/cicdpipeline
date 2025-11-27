"""
Security helpers for the Health & Reliability Monitoring module.

Provides reusable FastAPI dependencies for authN/Z and tenant isolation.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import Depends, Header, HTTPException, status

from .dependencies import IAMClient
from .service_container import get_iam_client


def _iam() -> IAMClient:
    return get_iam_client()


async def require_scope(
    authorization: str = Header(..., alias="Authorization"),
    iam: IAMClient = Depends(_iam),
) -> Dict[str, Any]:
    """Verify bearer token and return claims."""
    token = authorization.replace("Bearer ", "")
    claims = await iam.verify(token)
    if not claims or not iam.authorize(claims, "health_reliability_monitoring.read"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return claims


def ensure_scope(claims: Dict[str, Any], scope: str) -> None:
    """Ensure claims include the required scope."""
    if scope not in claims.get("scope", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def ensure_tenant_access(claims: Dict[str, Any], tenant_id: str | None) -> None:
    """Restrict tenant-granular views to the caller's tenant unless privileged."""
    if not tenant_id:
        return
    scopes = claims.get("scope", [])
    if (
        "health_reliability_monitoring.cross_tenant" in scopes
        or "health_reliability_monitoring.admin" in scopes
    ):
        return
    claim_tenant = claims.get("tenant_id")
    if claim_tenant not in {tenant_id, "all-tenants"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant access denied",
        )


def ensure_cross_plane_access(claims: Dict[str, Any]) -> None:
    """Allow plane-level aggregation only for privileged callers."""
    scopes = claims.get("scope", [])
    if (
        "health_reliability_monitoring.cross_tenant" in scopes
        or "health_reliability_monitoring.admin" in scopes
    ):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Plane access denied")


