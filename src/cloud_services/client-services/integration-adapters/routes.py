"""
API routes for Integration Adapters Module.

What: FastAPI routes implementing all endpoints per PRD Section 11
Why: HTTP API layer for integration adapters
Reads/Writes: HTTP requests/responses
Contracts: PRD Section 11 (APIs & Integration Contracts)
Risks: Route errors, validation failures, authentication bypass
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .database.connection import get_db
from .dependencies import get_integration_service, get_webhook_service
from .models import (
    IntegrationProviderCreate,
    IntegrationProviderResponse,
    IntegrationConnectionCreate,
    IntegrationConnectionUpdate,
    IntegrationConnectionResponse,
    NormalisedActionCreate,
    NormalisedActionResponse,
    HealthResponse,
    ConnectionHealthResponse,
    ErrorResponse,
    WebhookPayload,
)
from .services.integration_service import IntegrationService

logger = logging.getLogger(__name__)

router = APIRouter()


# Health Check
@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.utcnow(),
    )


# Management APIs (Tenant-Facing)
@router.post(
    "/v1/integrations/connections",
    response_model=IntegrationConnectionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["connections"],
)
async def create_connection(
    connection_data: IntegrationConnectionCreate,
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
):
    """Create a new integration connection (FR-2)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID not found in request"
        )
    
    try:
        connection = service.create_connection(tenant_id, connection_data)
        return IntegrationConnectionResponse.model_validate(connection)
    except Exception as e:
        logger.error(f"Failed to create connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/v1/integrations/connections",
    response_model=List[IntegrationConnectionResponse],
    tags=["connections"],
)
async def list_connections(
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
):
    """List all connections for tenant (FR-2)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID not found in request"
        )
    
    connections = service.list_connections(tenant_id)
    return [IntegrationConnectionResponse.model_validate(c) for c in connections]


@router.post(
    "/v1/integrations/connections/{connection_id}/verify",
    response_model=IntegrationConnectionResponse,
    tags=["connections"],
)
async def verify_connection(
    connection_id: UUID,
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
):
    """Trigger connection verification (FR-2, FR-3)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID not found in request"
        )
    
    is_valid = service.verify_connection(connection_id, tenant_id)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connection verification failed"
        )
    
    connection = service.get_connection(connection_id, tenant_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    return IntegrationConnectionResponse.model_validate(connection)


@router.patch(
    "/v1/integrations/connections/{connection_id}",
    response_model=IntegrationConnectionResponse,
    tags=["connections"],
)
async def update_connection(
    connection_id: UUID,
    update_data: IntegrationConnectionUpdate,
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
):
    """Update connection (FR-2)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID not found in request"
        )
    
    connection = service.update_connection(connection_id, tenant_id, update_data)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    return IntegrationConnectionResponse.model_validate(connection)


# Webhook Endpoint
@router.post(
    "/v1/integrations/webhooks/{provider_id}/{connection_token}",
    status_code=status.HTTP_200_OK,
    tags=["webhooks"],
)
async def receive_webhook(
    provider_id: str,
    connection_token: str,
    payload: dict,
    request: Request,
    webhook_service = Depends(get_webhook_service),
):
    """Receive provider webhook (FR-4)."""
    headers = dict(request.headers)
    
    try:
        success, error = webhook_service.process_webhook(
            provider_id=provider_id,
            connection_token=connection_token,
            payload=payload,
            headers=headers,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Webhook processing failed"
            )
        
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# Internal APIs
@router.post(
    "/internal/integrations/events/normalised",
    status_code=status.HTTP_200_OK,
    tags=["internal"],
)
async def accept_normalised_event(
    event: dict,
    service: IntegrationService = Depends(get_integration_service),
):
    """Accept SignalEnvelope events from adapters (for forwarding to PM-3) (FR-6)."""
    # This endpoint would forward to PM-3
    # For now, just acknowledge
    return {"status": "accepted"}


@router.post(
    "/internal/integrations/actions/execute",
    response_model=NormalisedActionResponse,
    tags=["internal"],
)
async def execute_action(
    action_data: NormalisedActionCreate,
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
):
    """Execute NormalisedAction (FR-7)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID not found in request"
        )
    
    action_dict = action_data.model_dump()
    action = service.execute_action(tenant_id, action_dict)
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action execution failed"
        )
    
    return NormalisedActionResponse.model_validate(action)


@router.get(
    "/internal/integrations/connections/{connection_id}/health",
    response_model=ConnectionHealthResponse,
    tags=["internal"],
)
async def get_connection_health(
    connection_id: UUID,
    request: Request,
    service: IntegrationService = Depends(get_integration_service),
):
    """Get connection health status."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant ID not found in request"
        )
    
    connection = service.get_connection(connection_id, tenant_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Simplified health response
    return ConnectionHealthResponse(
        connection_id=connection_id,
        status=connection.status,
        last_successful_call=None,  # Would be tracked in practice
        error_count=0,  # Would be tracked in practice
        rate_limit_state=None,  # Would be tracked in practice
    )

