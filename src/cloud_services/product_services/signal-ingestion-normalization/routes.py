"""
API routes for Signal Ingestion & Normalization (SIN) Module.

What: FastAPI route handlers for signal ingestion, DLQ inspection, producer registration
Why: Expose SIN functionality via REST API per PRD §5
Reads/Writes: HTTP request/response handling
Contracts: PRD §5 Data & API Contracts
Risks: Authentication/authorization must be enforced, input validation required
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Header, Body
from fastapi.responses import JSONResponse

from .models import (
    IngestRequest, IngestResponse, SignalIngestResult, DLQInspectionRequest, DLQInspectionResponse,
    ProducerRegistrationRequest, ProducerRegistrationResponse,
    HealthResponse, ReadinessResponse
)
from .services import SignalIngestionService
from .dlq import DLQHandler
from .producer_registry import ProducerRegistry, ProducerRegistryError
from .observability import HealthChecker
from .dependencies import MockM21IAM

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["signal-ingestion"])


def get_ingestion_service() -> SignalIngestionService:
    """Proxy to global ingestion service (needed for tests/mocking)."""
    from .main import get_ingestion_service as _get_ingestion_service
    return _get_ingestion_service()


def get_iam() -> MockM21IAM:
    """Dependency to get IAM instance."""
    from .main import get_iam_instance
    return get_iam_instance()


def get_tenant_id(authorization: Optional[str] = Header(None), iam: MockM21IAM = Depends(get_iam)) -> str:
    """
    Extract tenant ID from authorization header.

    Args:
        authorization: Authorization header
        iam: IAM dependency

    Returns:
        Tenant ID

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    # Verify token
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    claims = iam.verify_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    tenant_id = claims.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Token missing tenant_id claim")

    return tenant_id


@router.post("/signals/ingest", response_model=IngestResponse, status_code=200)
async def ingest_signals(
    request: IngestRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> IngestResponse:
    """
    Ingest signals per F3.2.

    Per PRD §5.3: Accepts batch of signals, returns per-signal results.
    """
    # Get service instance (in production, this would be dependency injection)
    from .main import get_ingestion_service
    service = get_ingestion_service()

    signals = request.signals or []
    results = []
    for signal in signals:
        try:
            result = service.ingest_signal(signal, tenant_id=tenant_id)
        except Exception as e:
            logger.error(f"Error ingesting signal: {e}")
            result = SignalIngestResult(
                signal_id=getattr(signal, "signal_id", "unknown"),
                status="rejected",
                error_code=None,
                error_message=str(e),
                dlq_id=None,
                warnings=[],
            )
        results.append(result)
    # Normalize all result objects into SignalIngestResult instances to satisfy response_model
    normalized_results = [
        result if isinstance(result, SignalIngestResult) else SignalIngestResult.model_validate(result)
        for result in results
    ]
    summary = {
        "total": len(normalized_results),
        "accepted": sum(1 for r in normalized_results if r.status == "accepted"),
        "rejected": sum(1 for r in normalized_results if r.status == "rejected"),
        "dlq": sum(1 for r in normalized_results if r.status == "dlq"),
    }
    return IngestResponse(results=normalized_results, summary=summary)


@router.get("/signals/dlq", response_model=DLQInspectionResponse)
async def inspect_dlq(
    tenant_id: Optional[str] = None,
    producer_id: Optional[str] = None,
    signal_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    auth_tenant_id: str = Depends(get_tenant_id)
) -> DLQInspectionResponse:
    """
    Inspect DLQ entries per F8.

    Per PRD §5.4: Returns DLQ entries with optional filters.
    """
    # Enforce tenant isolation
    if tenant_id and tenant_id != auth_tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant's DLQ entries")

    # Use authenticated tenant_id if not provided
    filter_tenant_id = tenant_id or auth_tenant_id

    # Get DLQ handler (in production, this would be dependency injection)
    from .main import get_dlq_handler
    dlq_handler = get_dlq_handler()

    entries = dlq_handler.list_dlq_entries(
        tenant_id=filter_tenant_id,
        producer_id=producer_id,
        signal_type=signal_type,
        limit=limit,
        offset=offset
    )

    # Get total count (simplified - in production would be efficient query)
    all_entries = dlq_handler.list_dlq_entries(
        tenant_id=filter_tenant_id,
        producer_id=producer_id,
        signal_type=signal_type,
        limit=10000,
        offset=0
    )
    total = len(all_entries)

    return DLQInspectionResponse(entries=entries, total=total)


@router.post("/producers/register", response_model=ProducerRegistrationResponse, status_code=201)
async def register_producer(
    request: ProducerRegistrationRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> ProducerRegistrationResponse:
    """
    Register producer per F2.1.

    Per PRD §5.5: Register producer with allowed signal types and contracts.
    """
    # Get producer registry (in production, this would be dependency injection)
    from .main import get_producer_registry
    registry = get_producer_registry()

    try:
        registry.register_producer(request.producer)
        return ProducerRegistrationResponse(
            producer_id=request.producer.producer_id,
            status="registered",
            message="Producer registered successfully"
        )
    except ProducerRegistryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error registering producer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/producers/{producer_id}", response_model=ProducerRegistrationRequest)
async def get_producer(
    producer_id: str,
    tenant_id: str = Depends(get_tenant_id)
) -> ProducerRegistrationRequest:
    """
    Get producer registration per F2.1.
    """
    from .main import get_producer_registry
    registry = get_producer_registry()

    producer = registry.get_producer(producer_id)
    if not producer:
        raise HTTPException(status_code=404, detail=f"Producer {producer_id} not found")

    return ProducerRegistrationRequest(producer=producer)


@router.put("/producers/{producer_id}", response_model=ProducerRegistrationResponse)
async def update_producer(
    producer_id: str,
    request: ProducerRegistrationRequest,
    tenant_id: str = Depends(get_tenant_id)
) -> ProducerRegistrationResponse:
    """
    Update producer registration per F2.1.
    """
    from .main import get_producer_registry
    registry = get_producer_registry()

    if producer_id != request.producer.producer_id:
        raise HTTPException(status_code=400, detail="Producer ID mismatch")

    try:
        registry.update_producer(producer_id, request.producer)
        return ProducerRegistrationResponse(
            producer_id=producer_id,
            status="updated",
            message="Producer updated successfully"
        )
    except ProducerRegistryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating producer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint per F9.
    """
    return HealthResponse(status="healthy")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint per F9.
    """
    from .main import get_health_checker
    from datetime import datetime
    health_checker = get_health_checker()

    health_status = health_checker.get_health_status()
    return ReadinessResponse(
        ready=health_checker.is_ready(),
        checks=health_status.get('checks', {}),
        timestamp=datetime.utcnow()
    )

