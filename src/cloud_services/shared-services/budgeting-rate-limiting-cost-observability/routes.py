"""
API routes for Budgeting, Rate-Limiting & Cost Observability (EPC-13).

What: FastAPI route handlers for all EPC-13 operations per PRD v3.0.0
Why: Provides HTTP API endpoints for budget, rate limit, cost, and quota operations
Reads/Writes: Reads HTTP request bodies, writes HTTP responses
Contracts: EPC-13 API contract per PRD lines 622-2617
Risks: Input validation failures, service unavailability, error message exposure
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Request, status, Query, Header
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .models import (
    HealthResponse, ErrorResponse, PaginationMeta,
    BudgetDefinition, CheckBudgetRequest, CheckBudgetResponse,
    RateLimitPolicy, CheckRateLimitRequest, CheckRateLimitResponse,
    CostRecord, RecordCostRequest, RecordCostResponse, CostReportRequest, CostReportResponse,
    QuotaAllocation, AllocateQuotaRequest, AllocateQuotaResponse,
    RecordCostBatchRequest, RecordCostBatchResponse,
    CheckBudgetBatchRequest, CheckBudgetBatchResponse,
    AllocateQuotaBatchRequest, AllocateQuotaBatchResponse,
    EventSubscription, CreateEventSubscriptionRequest, CreateEventSubscriptionResponse
)
from .services import M35ServiceFactory
from .dependencies import (
    MockM27EvidenceLedger, MockM29DataPlane, MockM31NotificationEngine,
    MockM33KeyManagement, MockM21IAM
)
from .database.session import get_db, init_db
from .database.models import Base

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize database schema on module import
init_db()

# Global dependencies (singletons)
_evidence_ledger: Optional[MockM27EvidenceLedger] = None
_key_management: Optional[MockM33KeyManagement] = None
_notification_engine: Optional[MockM31NotificationEngine] = None
_data_plane: Optional[MockM29DataPlane] = None


def get_evidence_ledger() -> MockM27EvidenceLedger:
    """Get evidence ledger instance (singleton)."""
    global _evidence_ledger
    if _evidence_ledger is None:
        _evidence_ledger = MockM27EvidenceLedger()
    return _evidence_ledger


def get_key_management() -> MockM33KeyManagement:
    """Get key management instance (singleton)."""
    global _key_management
    if _key_management is None:
        _key_management = MockM33KeyManagement()
    return _key_management


def get_notification_engine() -> MockM31NotificationEngine:
    """Get notification engine instance (singleton)."""
    global _notification_engine
    if _notification_engine is None:
        _notification_engine = MockM31NotificationEngine()
    return _notification_engine


def get_data_plane() -> MockM29DataPlane:
    """Get data plane instance (singleton)."""
    global _data_plane
    if _data_plane is None:
        _data_plane = MockM29DataPlane()
    return _data_plane


def get_service_factory(
    db: Session = Depends(get_db),
    evidence_ledger: MockM27EvidenceLedger = Depends(get_evidence_ledger),
    key_management: MockM33KeyManagement = Depends(get_key_management),
    notification_engine: MockM31NotificationEngine = Depends(get_notification_engine),
    data_plane: MockM29DataPlane = Depends(get_data_plane)
) -> M35ServiceFactory:
    """
    Dependency to get service factory with proper dependency injection.
    
    Each request gets its own database session, but shared dependencies are singletons.
    """
    return M35ServiceFactory(
        db_session=db,
        evidence_ledger=evidence_ledger,
        key_management=key_management,
        notification_engine=notification_engine,
        data_plane=data_plane,
        redis_client=None
    )


def get_correlation_id(
    x_correlation_id: Optional[str] = Header(None, alias="X-Correlation-ID")
) -> str:
    """Extract correlation ID from header."""
    return x_correlation_id or str(uuid.uuid4())


def create_error_response(
    error_code: str,
    message: str,
    status_code: int,
    correlation_id: str,
    details: Optional[Dict[str, Any]] = None,
    retriable: bool = False,
    tenant_id: Optional[str] = None
) -> HTTPException:
    """Create error response per PRD ErrorResponse schema."""
    error_response = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        correlation_id=correlation_id,
        retriable=retriable,
        tenant_id=tenant_id
    )
    return HTTPException(status_code=status_code, detail=error_response.model_dump())


# ============================================================================
# Health & Metrics Endpoints
# ============================================================================

@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check() -> HealthResponse:
    """Health check endpoint per PRD."""
    return HealthResponse(
        status="UP",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        dependencies={
            "database": {"status": "UP", "latency_ms": 1},
            "cache": {"status": "UP", "latency_ms": 1},
            "m27_audit_ledger": {"status": "UP", "latency_ms": 1},
            "m31_notification_engine": {"status": "UP", "latency_ms": 1},
            "m33_key_management": {"status": "UP", "latency_ms": 1}
        },
        degraded_reasons=[]
    )


@router.get("/metrics", tags=["System"])
def metrics() -> Response:
    """Metrics endpoint per PRD."""
    # Would return actual metrics in production
    return Response(content="# M35 Metrics\n", media_type="text/plain")


# ============================================================================
# Budget Endpoints
# ============================================================================

@router.post("/budgets/check", response_model=CheckBudgetResponse, tags=["Budgets"])
def check_budget(
    request: CheckBudgetRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> CheckBudgetResponse:
    """Check budget availability per PRD lines 1165-1259."""
    try:
        result = factory.budget_service.check_budget(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            estimated_cost=request.estimated_cost,
            allocated_to_type=request.allocated_to_type,
            allocated_to_id=request.allocated_to_id
        )

        # Generate receipt
        factory.receipt_service.generate_budget_check_receipt(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            estimated_cost=request.estimated_cost,
            allowed=result["allowed"],
            remaining_budget=result["remaining_budget"],
            budget_id=result["budget_id"] or str(uuid.uuid4()),
            enforcement_action=result["enforcement_action"],
            utilization_ratio=result["utilization_ratio"],
            allocated_to_type=request.allocated_to_type,
            allocated_to_id=request.allocated_to_id,
            operation_context=request.operation_context
        )

        return CheckBudgetResponse(
            allowed=result["allowed"],
            remaining_budget=result["remaining_budget"],
            budget_id=result["budget_id"] or "",
            enforcement_action=result["enforcement_action"],
            utilization_ratio=result["utilization_ratio"],
             requires_approval=result["requires_approval"],
             approval_id=result["approval_id"],
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Budget check failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.post("/budgets", response_model=BudgetDefinition, status_code=status.HTTP_201_CREATED, tags=["Budgets"])
def create_budget(
    request: BudgetDefinition,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> BudgetDefinition:
    """Create budget definition per PRD lines 1261-1300."""
    try:
        budget = factory.budget_service.create_budget(
            tenant_id=request.tenant_id,
            budget_name=request.budget_name,
            budget_type=request.budget_type,
            budget_amount=request.budget_amount,
            period_type=request.period_type,
            start_date=datetime.fromisoformat(request.start_date.replace('Z', '+00:00')),
            allocated_to_type=request.allocated_to_type,
            allocated_to_id=request.allocated_to_id,
            enforcement_action=request.enforcement_action,
            currency=request.currency,
            end_date=datetime.fromisoformat(request.end_date.replace('Z', '+00:00')) if request.end_date else None,
            thresholds=request.thresholds,
            notifications=request.notifications,
            created_by=request.created_by or str(uuid.uuid4())
        )

        return BudgetDefinition(**budget.to_dict())
    except Exception as e:
        logger.error(f"Budget creation failed: {e}")
        raise create_error_response(
            error_code="VALIDATION_ERROR",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.get("/budgets", tags=["Budgets"])
def list_budgets(
    tenant_id: str = Query(..., description="Tenant identifier"),
    budget_type: Optional[str] = Query(None),
    allocated_to_type: Optional[str] = Query(None),
    allocated_to_id: Optional[str] = Query(None),
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """List budgets per PRD lines 1301-1357."""
    try:
        budgets, total_count = factory.budget_service.list_budgets(
            tenant_id=tenant_id,
            budget_type=budget_type,
            allocated_to_type=allocated_to_type,
            allocated_to_id=allocated_to_id,
            active_only=active_only,
            page=page,
            page_size=page_size
        )

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0

        return {
            "budgets": [BudgetDefinition(**b.to_dict()) for b in budgets],
            "pagination": PaginationMeta(
                page=page,
                page_size=page_size,
                total_count=total_count,
                total_pages=total_pages,
                next_page_token=str(page + 1) if page < total_pages else None,
                prev_page_token=str(page - 1) if page > 1 else None
            )
        }
    except Exception as e:
        logger.error(f"List budgets failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=tenant_id
        )


# ============================================================================
# Rate Limit Endpoints
# ============================================================================

@router.post("/rate-limits/check", response_model=CheckRateLimitResponse, tags=["Rate Limits"])
def check_rate_limit(
    request: CheckRateLimitRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> CheckRateLimitResponse:
    """Check rate limit per PRD lines 1480-1535."""
    try:
        result = factory.rate_limit_service.check_rate_limit(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            request_count=request.request_count,
            priority=request.priority,
            resource_key=request.resource_key
        )

        # Generate receipt
        factory.receipt_service.generate_rate_limit_check_receipt(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            request_count=request.request_count,
            allowed=result["allowed"],
            remaining_requests=result["remaining_requests"],
            limit_value=result["limit_value"] or 0,
            policy_id=result["policy_id"] or str(uuid.uuid4()),
            reset_time=result["reset_time"],
            priority=request.priority,
            resource_key=request.resource_key
        )

        return CheckRateLimitResponse(
            allowed=result["allowed"],
            remaining_requests=result["remaining_requests"],
            reset_time=result["reset_time"],
            limit_value=result["limit_value"],
            retry_after=result["retry_after"],
            policy_id=result["policy_id"],
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Rate limit check failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


# ============================================================================
# Cost Tracking Endpoints
# ============================================================================

@router.post("/cost-tracking/record", response_model=RecordCostResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Cost Tracking"])
def record_cost(
    request: RecordCostRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> RecordCostResponse:
    """Record cost per PRD lines 1738-1789."""
    try:
        cost_record = factory.cost_service.record_cost(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            cost_amount=request.cost_amount,
            usage_quantity=request.usage_quantity,
            attributed_to_type=request.attributed_to_type or "tenant",
            attributed_to_id=request.attributed_to_id or request.tenant_id,
            resource_id=request.resource_id,
            usage_unit=request.usage_unit,
            service_name=request.service_name,
            region=request.region,
            tags=request.tags
        )

        # Generate receipt
        factory.receipt_service.generate_cost_recording_receipt(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            cost_amount=request.cost_amount,
            record_id=str(cost_record.cost_id),
            attributed_to_type=request.attributed_to_type or "tenant",
            attributed_to_id=request.attributed_to_id or request.tenant_id,
            usage_quantity=request.usage_quantity,
            usage_unit=request.usage_unit,
            resource_id=request.resource_id,
            service_name=request.service_name,
            tags=request.tags
        )

        return RecordCostResponse(
            record_id=str(cost_record.cost_id),
            recorded_at=cost_record.timestamp.isoformat(),
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Cost recording failed: {e}")
        raise create_error_response(
            error_code="COST_CALCULATION_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


# ============================================================================
# Quota Endpoints
# ============================================================================

@router.post("/quotas/allocate", response_model=AllocateQuotaResponse, status_code=status.HTTP_201_CREATED, tags=["Quotas"])
def allocate_quota(
    request: AllocateQuotaRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> AllocateQuotaResponse:
    """Allocate quota per PRD lines 1980-2034."""
    try:
        quota = factory.quota_service.allocate_quota(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            allocated_amount=request.allocated_amount,
            period_start=datetime.fromisoformat(request.period_start.replace('Z', '+00:00')),
            period_end=datetime.fromisoformat(request.period_end.replace('Z', '+00:00')),
            allocation_type=request.allocation_type,
            max_burst_amount=request.max_burst_amount,
            auto_renew=request.auto_renew
        )

        # Generate receipt
        factory.receipt_service.generate_quota_allocation_receipt(
            tenant_id=request.tenant_id,
            resource_type=request.resource_type,
            allocated_amount=request.allocated_amount,
            quota_id=str(quota.quota_id),
            allocation_type=request.allocation_type,
            period_start=request.period_start,
            period_end=request.period_end,
            used_amount=quota.used_amount,
            remaining_amount=quota.allocated_amount - quota.used_amount,
            max_burst_amount=request.max_burst_amount,
            auto_renew=request.auto_renew
        )

        return AllocateQuotaResponse(
            quota_id=str(quota.quota_id),
            allocated_at=quota.created_at.isoformat(),
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Quota allocation failed: {e}")
        raise create_error_response(
            error_code="QUOTA_EXHAUSTED",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.get("/budgets/{budget_id}", response_model=BudgetDefinition, tags=["Budgets"])
def get_budget(
    budget_id: str,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> BudgetDefinition:
    """Get budget by ID per PRD lines 1359-1395."""
    try:
        budget = factory.budget_service.get_budget(budget_id)
        if not budget:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Budget {budget_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return BudgetDefinition(**budget.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get budget failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


@router.put("/budgets/{budget_id}", response_model=BudgetDefinition, tags=["Budgets"])
def update_budget(
    budget_id: str,
    request: BudgetDefinition,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> BudgetDefinition:
    """Update budget per PRD lines 1397-1440."""
    try:
        budget = factory.budget_service.update_budget(
            budget_id=budget_id,
            budget_name=request.budget_name,
            budget_amount=request.budget_amount,
            period_type=request.period_type,
            start_date=datetime.fromisoformat(request.start_date.replace('Z', '+00:00')),
            end_date=datetime.fromisoformat(request.end_date.replace('Z', '+00:00')) if request.end_date else None,
            enforcement_action=request.enforcement_action,
            thresholds=request.thresholds,
            notifications=request.notifications
        )
        if not budget:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Budget {budget_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return BudgetDefinition(**budget.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update budget failed: {e}")
        raise create_error_response(
            error_code="VALIDATION_ERROR",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Budgets"])
def delete_budget(
    budget_id: str,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """Delete budget per PRD lines 1442-1478."""
    try:
        deleted = factory.budget_service.delete_budget(budget_id)
        if not deleted:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Budget {budget_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return Response(status_code=204)
    except HTTPException:
        raise
    except ValueError as e:
        raise create_error_response(
            error_code="CONFLICT",
            message=str(e),
            status_code=409,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Delete budget failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


@router.post("/budgets/check/batch", response_model=CheckBudgetBatchResponse, tags=["Budgets"])
def check_budget_batch(
    request: CheckBudgetBatchRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> CheckBudgetBatchResponse:
    """Batch budget check per PRD lines 3129-3133."""
    try:
        results = []
        for check in request.checks:
            try:
                result = factory.budget_service.check_budget(
                    tenant_id=check.tenant_id,
                    resource_type=check.resource_type,
                    estimated_cost=check.estimated_cost,
                    allocated_to_type=check.allocated_to_type,
                    allocated_to_id=check.allocated_to_id
                )
                results.append({
                    "tenant_id": check.tenant_id,
                    "resource_type": check.resource_type,
                    "allowed": result["allowed"],
                    "remaining_budget": float(result["remaining_budget"]),
                    "budget_id": result["budget_id"]
                })
            except Exception as exc:
                results.append({
                    "tenant_id": check.tenant_id,
                    "resource_type": check.resource_type,
                    "error": str(exc)
                })
        return CheckBudgetBatchResponse(
            batch_id=str(uuid.uuid4()),
            results=results,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Batch budget check failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


# Rate Limit CRUD endpoints
@router.post("/rate-limits", response_model=RateLimitPolicy, status_code=status.HTTP_201_CREATED, tags=["Rate Limits"])
def create_rate_limit_policy(
    request: RateLimitPolicy,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> RateLimitPolicy:
    """Create rate limit policy per PRD."""
    try:
        policy = factory.rate_limit_service.create_rate_limit_policy(
            tenant_id=request.tenant_id,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            resource_type=request.resource_type,
            limit_value=request.limit_value,
            time_window_seconds=request.time_window_seconds,
            algorithm=request.algorithm,
            burst_capacity=request.burst_capacity,
            overrides=request.overrides
        )
        return RateLimitPolicy(**policy.to_dict())
    except Exception as e:
        logger.error(f"Create rate limit policy failed: {e}")
        raise create_error_response(
            error_code="VALIDATION_ERROR",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.get("/rate-limits", tags=["Rate Limits"])
def list_rate_limit_policies(
    tenant_id: str = Query(..., description="Tenant identifier"),
    scope_type: Optional[str] = Query(None),
    scope_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """List rate limit policies per PRD."""
    try:
        policies, total_count = factory.rate_limit_service.list_rate_limit_policies(
            tenant_id=tenant_id,
            scope_type=scope_type,
            scope_id=scope_id,
            resource_type=resource_type,
            page=page,
            page_size=page_size
        )
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        return {
            "policies": [RateLimitPolicy(**p.to_dict()) for p in policies],
            "pagination": PaginationMeta(
                page=page,
                page_size=page_size,
                total_count=total_count,
                total_pages=total_pages,
                next_page_token=str(page + 1) if page < total_pages else None,
                prev_page_token=str(page - 1) if page > 1 else None
            )
        }
    except Exception as e:
        logger.error(f"List rate limit policies failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=tenant_id
        )


@router.get("/rate-limits/{policy_id}", response_model=RateLimitPolicy, tags=["Rate Limits"])
def get_rate_limit_policy(
    policy_id: str,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> RateLimitPolicy:
    """Get rate limit policy by ID."""
    try:
        policy = factory.rate_limit_service.get_rate_limit_policy(policy_id)
        if not policy:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Rate limit policy {policy_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return RateLimitPolicy(**policy.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get rate limit policy failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


@router.put("/rate-limits/{policy_id}", response_model=RateLimitPolicy, tags=["Rate Limits"])
def update_rate_limit_policy(
    policy_id: str,
    request: RateLimitPolicy,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> RateLimitPolicy:
    """Update rate limit policy."""
    try:
        policy = factory.rate_limit_service.update_rate_limit_policy(
            policy_id=policy_id,
            limit_value=request.limit_value,
            time_window_seconds=request.time_window_seconds,
            algorithm=request.algorithm,
            burst_capacity=request.burst_capacity,
            overrides=request.overrides
        )
        if not policy:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Rate limit policy {policy_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return RateLimitPolicy(**policy.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update rate limit policy failed: {e}")
        raise create_error_response(
            error_code="VALIDATION_ERROR",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.delete("/rate-limits/{policy_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Rate Limits"])
def delete_rate_limit_policy(
    policy_id: str,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """Delete rate limit policy."""
    try:
        deleted = factory.rate_limit_service.delete_rate_limit_policy(policy_id)
        if not deleted:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Rate limit policy {policy_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete rate limit policy failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


# Cost Tracking additional endpoints
@router.get("/cost-tracking/records", tags=["Cost Tracking"])
def query_cost_records(
    tenant_id: str = Query(..., description="Tenant identifier"),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    attributed_to_type: Optional[str] = Query(None),
    attributed_to_id: Optional[str] = Query(None),
    service_name: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """Query cost records per PRD."""
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00')) if start_time else None
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else None
        records, total_count, aggregated = factory.cost_service.query_cost_records(
            tenant_id=tenant_id,
            start_time=start_dt,
            end_time=end_dt,
            resource_type=resource_type,
            attributed_to_type=attributed_to_type,
            attributed_to_id=attributed_to_id,
            service_name=service_name,
            page=page,
            page_size=page_size
        )
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        return {
            "records": [CostRecord(**r.to_dict()) for r in records],
            "aggregated": aggregated,
            "pagination": PaginationMeta(
                page=page,
                page_size=page_size,
                total_count=total_count,
                total_pages=total_pages,
                next_page_token=str(page + 1) if page < total_pages else None,
                prev_page_token=str(page - 1) if page > 1 else None
            )
        }
    except Exception as e:
        logger.error(f"Query cost records failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=tenant_id
        )


@router.post("/cost-tracking/reports", response_model=CostReportResponse, tags=["Cost Tracking"])
def generate_cost_report(
    request: CostReportRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> CostReportResponse:
    """Generate cost report per PRD lines 1908-1977."""
    try:
        start_dt = datetime.fromisoformat(request.start_time.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(request.end_time.replace('Z', '+00:00'))
        report = factory.cost_service.generate_cost_report(
            tenant_id=request.tenant_id,
            report_type=request.report_type,
            start_time=start_dt,
            end_time=end_dt,
            group_by=request.group_by
        )
        return CostReportResponse(
            report_id=report["report_id"],
            report_type=report["report_type"],
            period=report["period"],
            total_cost=report["total_cost"],
            currency=report["currency"],
            breakdown=report["breakdown"],
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Generate cost report failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.post("/cost-tracking/record/batch", response_model=RecordCostBatchResponse, status_code=status.HTTP_202_ACCEPTED, tags=["Cost Tracking"])
def record_cost_batch(
    request: RecordCostBatchRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> RecordCostBatchResponse:
    """Batch cost recording per PRD lines 3123-3128."""
    try:
        records = [r.model_dump() for r in request.records]
        processed, failed, failures = factory.cost_service.record_cost_batch(records)
        return RecordCostBatchResponse(
            batch_id=str(uuid.uuid4()),
            processed_count=processed,
            failed_count=failed,
            failures=failures,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Batch cost recording failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


# Quota additional endpoints
@router.get("/quotas", tags=["Quotas"])
def list_quotas(
    tenant_id: str = Query(..., description="Tenant identifier"),
    resource_type: Optional[str] = Query(None),
    allocation_type: Optional[str] = Query(None),
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """List quotas per PRD."""
    try:
        quotas, total_count = factory.quota_service.list_quotas(
            tenant_id=tenant_id,
            resource_type=resource_type,
            allocation_type=allocation_type,
            active_only=active_only,
            page=page,
            page_size=page_size
        )
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        return {
            "quotas": [QuotaAllocation(**q.to_dict()) for q in quotas],
            "pagination": PaginationMeta(
                page=page,
                page_size=page_size,
                total_count=total_count,
                total_pages=total_pages,
                next_page_token=str(page + 1) if page < total_pages else None,
                prev_page_token=str(page - 1) if page > 1 else None
            )
        }
    except Exception as e:
        logger.error(f"List quotas failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=tenant_id
        )


@router.get("/quotas/{quota_id}", response_model=QuotaAllocation, tags=["Quotas"])
def get_quota(
    quota_id: str,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> QuotaAllocation:
    """Get quota by ID."""
    try:
        quota = factory.quota_service.get_quota(quota_id)
        if not quota:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Quota {quota_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return QuotaAllocation(**quota.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get quota failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


@router.put("/quotas/{quota_id}", response_model=QuotaAllocation, tags=["Quotas"])
def update_quota(
    quota_id: str,
    request: QuotaAllocation,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> QuotaAllocation:
    """Update quota."""
    try:
        quota = factory.quota_service.update_quota(
            quota_id=quota_id,
            allocated_amount=request.allocated_amount,
            max_burst_amount=request.max_burst_amount,
            auto_renew=request.auto_renew
        )
        if not quota:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Quota {quota_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return QuotaAllocation(**quota.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update quota failed: {e}")
        raise create_error_response(
            error_code="VALIDATION_ERROR",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.delete("/quotas/{quota_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Quotas"])
def delete_quota(
    quota_id: str,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """Delete quota."""
    try:
        deleted = factory.quota_service.delete_quota(quota_id)
        if not deleted:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Quota {quota_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return Response(status_code=204)
    except HTTPException:
        raise
    except ValueError as e:
        raise create_error_response(
            error_code="CONFLICT",
            message=str(e),
            status_code=409,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Delete quota failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


@router.post("/quotas/allocate/batch", response_model=AllocateQuotaBatchResponse, status_code=status.HTTP_201_CREATED, tags=["Quotas"])
def allocate_quota_batch(
    request: AllocateQuotaBatchRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> AllocateQuotaBatchResponse:
    """Batch quota allocation per PRD lines 3134-3138."""
    try:
        successful = 0
        failed = 0
        quotas = []
        failures = []
        for allocation in request.allocations:
            try:
                quota = factory.quota_service.allocate_quota(
                    tenant_id=allocation.tenant_id,
                    resource_type=allocation.resource_type,
                    allocated_amount=allocation.allocated_amount,
                    period_start=datetime.fromisoformat(allocation.period_start.replace('Z', '+00:00')),
                    period_end=datetime.fromisoformat(allocation.period_end.replace('Z', '+00:00')),
                    allocation_type=allocation.allocation_type,
                    max_burst_amount=allocation.max_burst_amount,
                    auto_renew=allocation.auto_renew
                )
                quotas.append(QuotaAllocation(**quota.to_dict()).model_dump())
                successful += 1
            except Exception as exc:
                failed += 1
                failures.append({
                    "tenant_id": allocation.tenant_id,
                    "resource_type": allocation.resource_type,
                    "error": str(exc)
                })
        return AllocateQuotaBatchResponse(
            batch_id=str(uuid.uuid4()),
            successful_count=successful,
            failed_count=failed,
            quotas=quotas if quotas else None,
            failures=failures if failures else None,
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Batch quota allocation failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )


# Alerts endpoint
@router.get("/alerts", tags=["Alerts"])
def list_alerts(
    tenant_id: str = Query(..., description="Tenant identifier"),
    alert_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """List alerts per PRD."""
    try:
        # Mock implementation - would query from alert store in production
        return {
            "alerts": [],
            "pagination": PaginationMeta(
                page=page,
                page_size=page_size,
                total_count=0,
                total_pages=0,
                next_page_token=None,
                prev_page_token=None
            )
        }
    except Exception as e:
        logger.error(f"List alerts failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=tenant_id
        )


# Event Subscriptions endpoints
@router.post("/event-subscriptions", response_model=CreateEventSubscriptionResponse, status_code=status.HTTP_201_CREATED, tags=["Event Subscriptions"])
def create_event_subscription(
    request: CreateEventSubscriptionRequest,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
) -> CreateEventSubscriptionResponse:
    """Create event subscription per PRD lines 1949-1973."""
    try:
        subscription = factory.event_subscription_service.create_subscription(
            tenant_id=request.tenant_id,
            event_types=request.event_types,
            webhook_url=request.webhook_url,
            filters=request.filters,
            enabled=request.enabled
        )
        return CreateEventSubscriptionResponse(
            subscription_id=subscription["subscription_id"],
            created_at=subscription["created_at"],
            correlation_id=correlation_id
        )
    except Exception as e:
        logger.error(f"Create event subscription failed: {e}")
        raise create_error_response(
            error_code="VALIDATION_ERROR",
            message=str(e),
            status_code=400,
            correlation_id=correlation_id,
            tenant_id=request.tenant_id
        )


@router.get("/event-subscriptions", tags=["Event Subscriptions"])
def list_event_subscriptions(
    tenant_id: str = Query(..., description="Tenant identifier"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """List event subscriptions."""
    try:
        subscriptions, total_count = factory.event_subscription_service.list_subscriptions(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size
        )
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        return {
            "subscriptions": subscriptions,
            "pagination": PaginationMeta(
                page=page,
                page_size=page_size,
                total_count=total_count,
                total_pages=total_pages,
                next_page_token=str(page + 1) if page < total_pages else None,
                prev_page_token=str(page - 1) if page > 1 else None
            )
        }
    except Exception as e:
        logger.error(f"List event subscriptions failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id,
            tenant_id=tenant_id
        )


@router.delete("/event-subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Event Subscriptions"])
def delete_event_subscription(
    subscription_id: str,
    correlation_id: str = Depends(get_correlation_id),
    factory: M35ServiceFactory = Depends(get_service_factory)
):
    """Delete event subscription."""
    try:
        deleted = factory.event_subscription_service.delete_subscription(subscription_id)
        if not deleted:
            raise create_error_response(
                error_code="NOT_FOUND",
                message=f"Event subscription {subscription_id} not found",
                status_code=404,
                correlation_id=correlation_id
            )
        return Response(status_code=204)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete event subscription failed: {e}")
        raise create_error_response(
            error_code="INTERNAL_ERROR",
            message=str(e),
            status_code=500,
            correlation_id=correlation_id
        )

