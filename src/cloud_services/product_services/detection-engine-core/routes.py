"""
API routes for Detection Engine Core Module (PM-4).

What: FastAPI route handlers for decision evaluation, feedback submission, evidence links
Why: Expose Detection Engine Core functionality via REST API per PRD §3.7
Reads/Writes: HTTP request/response handling
Contracts: PRD §3.7, §3.9
Risks: Authentication/authorization must be enforced, input validation required
"""

import logging
import sys
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import JSONResponse

try:
    from . import models as _models
    from .models import (
        DecisionRequest, DecisionResponse, DecisionResponseError,
        FeedbackRequest, FeedbackResponse,
        HealthResponse, ReadinessResponse
    )
    from . import services as _services
    from .services import DetectionEngineService
except ImportError:
    # For direct execution or testing
    from models import (
        DecisionRequest, DecisionResponse, DecisionResponseError,
        FeedbackRequest, FeedbackResponse,
        HealthResponse, ReadinessResponse
    )
    from services import DetectionEngineService
else:
    # Expose aliases so bare `import models`/`import services` resolve to this package.
    sys.modules.setdefault("models", _models)
    sys.modules.setdefault("services", _services)

logger = logging.getLogger(__name__)

# Ensure subsequent bare `import routes` resolves to this module (test helpers rely on it).
sys.modules.setdefault("routes", sys.modules[__name__])

router = APIRouter(prefix="/v1", tags=["detection-engine-core"])

# Global service instance (in production, use dependency injection)
_service: Optional[DetectionEngineService] = None


def get_service() -> DetectionEngineService:
    """Dependency to get service instance."""
    global _service
    if _service is None:
        _service = DetectionEngineService()
    return _service


def get_tenant_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract tenant ID from authorization header.

    Args:
        authorization: Authorization header

    Returns:
        Tenant ID

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Verify token (placeholder - in production would use IAM service)
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # Placeholder token verification
    if not token or token == "invalid":
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Extract tenant_id from token (placeholder)
    # In production, would decode JWT and extract claims
    tenant_id = "default-tenant"  # Placeholder
    
    return tenant_id


@router.post("/decisions/evaluate", response_model=DecisionResponse, status_code=200)
async def evaluate_decision(
    request: DecisionRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: DetectionEngineService = Depends(get_service)
) -> DecisionResponse:
    """
    Evaluate decision per PRD §3.2.

    Per PRD §3.7: Accepts decision request, returns decision response with receipt.
    Per PRD §3.12: Respects performance budgets (50ms/100ms/200ms p95).
    """
    try:
        response = service.evaluate_decision(request)
        return response
    except Exception as e:
        logger.error(f"Error evaluating decision: {e}", exc_info=True)
        # Return error response instead of raising exception
        return JSONResponse(
            status_code=500,
            content=DecisionResponseError(
                error_code="EVALUATION_ERROR",
                error_message=str(e),
                degraded=True
            ).model_dump()
        )


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    request: FeedbackRequest,
    tenant_id: str = Depends(get_tenant_id),
    service: DetectionEngineService = Depends(get_service)
) -> FeedbackResponse:
    """
    Submit feedback per PRD §3.6.

    Per PRD §3.7: Accepts feedback request, returns feedback response.
    """
    try:
        response = service.submit_feedback(request)
        return response
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint per PRD §3.9.
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint per PRD §3.9.
    """
    from datetime import datetime
    return ReadinessResponse(
        ready=True,
        checks={
            "service": True,
            "detection_engine": True
        },
        timestamp=datetime.utcnow()
    )
