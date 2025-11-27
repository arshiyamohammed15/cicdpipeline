"""
API routes for User Behaviour Intelligence (UBI) Module (EPC-9).

What: FastAPI route handlers for actor profiles, signal queries, configuration management
Why: Expose UBI functionality via REST API per PRD Section 11
Reads/Writes: HTTP request/response handling
Contracts: PRD Section 11 APIs & Integration Contracts
Risks: Authentication/authorization must be enforced, input validation required
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from datetime import datetime

from .models import (
    ActorProfileResponse, QuerySignalsRequest, QuerySignalsResponse,
    TenantConfigRequest, TenantConfigResponse, TenantConfigUpdateResponse,
    HealthResponse, ReadinessResponse, ErrorResponse
)
from .services import UBIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/ubi", tags=["user-behaviour-intelligence"])

# Global service instance (in production, use dependency injection)
_service: Optional[UBIService] = None


def get_service() -> UBIService:
    """Dependency to get service instance."""
    global _service
    if _service is None:
        _service = UBIService()
    return _service


def get_tenant_id(request: Request) -> str:
    """
    Extract tenant ID from request state (set by middleware).

    Args:
        request: FastAPI request object

    Returns:
        Tenant ID

    Raises:
        HTTPException: If tenant ID not found
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID not found in token")
    return tenant_id


def check_permission(request: Request, required_role: str) -> None:
    """
    Check if user has required role.

    Args:
        request: FastAPI request object
        required_role: Required IAM role (e.g., "ubi:read:actor")

    Raises:
        HTTPException: If permission denied
    """
    roles = getattr(request.state, "roles", [])
    
    # Check for privileged roles
    if "product_ops" in roles or "admin" in roles:
        return
    
    # Check for specific role
    if required_role not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions. Required role: {required_role}"
        )


@router.get("/actors/{actor_id}/profile", response_model=ActorProfileResponse)
async def get_actor_profile(
    actor_id: str,
    tenant_id: str,
    request: Request,
    window: Optional[str] = None,
    service: UBIService = Depends(get_service)
) -> ActorProfileResponse:
    """
    Get actor behaviour profile per PRD Section 11.1.

    Per PRD Section 11.1: Returns actor metadata, recent signals, features, and baselines.
    """
    # Extract tenant_id from request state
    auth_tenant_id = get_tenant_id(request)
    
    # Enforce tenant isolation
    if tenant_id != auth_tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant's data")
    
    # Check authorization
    check_permission(request, "ubi:read:actor")
    
    try:
        response = service.get_actor_profile(actor_id, tenant_id, window)
        return response
    except Exception as e:
        logger.error(f"Error getting actor profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/signals", response_model=QuerySignalsResponse)
async def query_signals(
    request_body: QuerySignalsRequest,
    request: Request,
    service: UBIService = Depends(get_service)
) -> QuerySignalsResponse:
    """
    Query signals per PRD Section 11.2.

    Per PRD Section 11.2: Returns signals matching query criteria.
    """
    # Extract tenant_id from request state
    auth_tenant_id = get_tenant_id(request)
    
    # Enforce tenant isolation
    if request_body.tenant_id != auth_tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant's data")
    
    # Check authorization based on scope
    if request_body.scope == "actor":
        check_permission(request, "ubi:read:actor")
    elif request_body.scope == "team":
        check_permission(request, "ubi:read:team")
    elif request_body.scope == "tenant":
        check_permission(request, "ubi:read:tenant")
    
    try:
        response = service.query_signals(request_body)
        return response
    except Exception as e:
        logger.error(f"Error querying signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/{tenant_id}", response_model=TenantConfigResponse)
async def get_tenant_config(
    tenant_id: str,
    request: Request,
    service: UBIService = Depends(get_service)
) -> TenantConfigResponse:
    """
    Get tenant configuration per PRD Section 11.4.

    Per PRD Section 11.4: Returns current configuration for tenant.
    """
    # Extract tenant_id from request state
    auth_tenant_id = get_tenant_id(request)
    
    # Enforce tenant isolation
    if tenant_id != auth_tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant's configuration")
    
    # Check authorization
    check_permission(request, "ubi:read:tenant")
    
    try:
        response = service.get_tenant_config(tenant_id)
        return response
    except Exception as e:
        logger.error(f"Error getting tenant config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/{tenant_id}", response_model=TenantConfigUpdateResponse)
async def update_tenant_config(
    tenant_id: str,
    request_body: TenantConfigRequest,
    request: Request,
    service: UBIService = Depends(get_service)
) -> TenantConfigUpdateResponse:
    """
    Update tenant configuration per PRD Section 11.4.

    Per PRD Section 11.4: Updates configuration and emits receipt to ERIS.
    """
    # Extract tenant_id from request state
    auth_tenant_id = get_tenant_id(request)
    
    # Enforce tenant isolation
    if tenant_id != auth_tenant_id:
        raise HTTPException(status_code=403, detail="Cannot update other tenant's configuration")
    
    # Check authorization
    check_permission(request, "ubi:write:config")
    
    # Extract actor ID from claims for audit trail
    claims = getattr(request.state, "claims", {})
    created_by = claims.get("sub", "unknown")
    
    try:
        response = service.update_tenant_config(tenant_id, request_body, created_by)
        return response
    except ValueError as e:
        logger.error(f"Invalid configuration: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating tenant config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint per PRD Section 11.
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint per PRD Section 11.
    """
    from ..database.connection import health_check
    
    db_health = health_check()
    
    return ReadinessResponse(
        ready=db_health.get("status") == "healthy",
        checks={
            "service": True,
            "database": db_health.get("status") == "healthy",
            "pm3": True,
            "eris": True
        },
        timestamp=datetime.utcnow()
    )


@router.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint per PRD NFR-5.
    """
    from fastapi.responses import Response
    from prometheus_client import CONTENT_TYPE_LATEST
    from ..observability.metrics import get_metrics_text
    
    metrics_text = get_metrics_text()
    return Response(content=metrics_text, media_type=CONTENT_TYPE_LATEST)

