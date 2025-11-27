"""
API routes for Evidence & Receipt Indexing Service (ERIS).

What: FastAPI route handlers for receipt ingestion, query, and management
Why: Provides HTTP API endpoints for ERIS operations
Reads/Writes: Reads HTTP request bodies, writes HTTP responses
Contracts: ERIS API contract per PRD Section 9
Risks: Input validation failures, service unavailability
"""

import json
import logging
import os
import socket
import time
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status, Header, BackgroundTasks, Request
from sqlalchemy.orm import Session

from .models import (
    HealthResponse, HealthResponseDetailed, MetricsResponse, ConfigResponse,
    ErrorResponse, ErrorDetail,
    ReceiptIngestionRequest, ReceiptIngestionResponse,
    ReceiptSearchRequest, ReceiptSearchResponse,
    ReceiptAggregateRequest, ReceiptAggregateResponse,
    CourierBatchRequest, CourierBatchResponse, MerkleProofResponse,
    ExportRequest, ExportResponse, ExportStatusResponse,
    ChainTraversalRequest, ChainTraversalResponse,
    ChainQueryRequest, ChainQueryResponse
)
from .services import (
    ReceiptValidator, TenantIdResolver, ReceiptIngestionService,
    ReceiptQueryService, ReceiptAggregationService,
    IntegrityVerificationService, ChainTraversalService,
    CourierBatchService, MerkleProofService, ExportService,
    RetentionManagementService, MetaAuditService, DLQService
)
from .database.session import get_db
from .dependencies import verify_token, extract_tenant_context, check_rbac_permission
from .metrics import (
    receipts_ingested, validation_errors, queries_total, query_duration,
    ingestion_duration, dlq_entries, export_jobs
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Service metadata for structured logging
SERVICE_NAME = "evidence-receipt-indexing-service"
SERVICE_VERSION = "1.0.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()


# Dependency to get database session
def get_database_session() -> Session:
    """Get database session dependency."""
    db = next(get_db())
    return db


# Sub-feature 9.1: Health, Metrics, Config Routes

@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint per PRD Section 9.8."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/health/detailed", response_model=HealthResponseDetailed)
def health_check_detailed() -> HealthResponseDetailed:
    """Detailed health check with dependencies per PRD Section 9.8."""
    # Simplified dependency checks (would check actual services in production)
    return HealthResponseDetailed(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        dependencies={
            "storage": "healthy",
            "iam": "healthy",
            "data_governance": "healthy",
            "contracts_schema_registry": "healthy",
            "kms": "healthy"
        }
    )


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    """Prometheus metrics endpoint per PRD Section 9.8."""
    from .metrics import get_metrics_text
    metrics_text = get_metrics_text()
    return MetricsResponse(metrics=metrics_text)


@router.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    """Module configuration endpoint per PRD Section 9.8."""
    return ConfigResponse(
        version="1.0.0",
        capabilities=[
            "receipt_ingestion", "receipt_query", "receipt_aggregation",
            "courier_batch_ingestion", "export", "chain_traversal",
            "integrity_verification"
        ],
        supported_schema_versions=["1.0.0"],
        rate_limits={
            "ingestion": {"default": 1000, "burst": 2000},
            "query": {"default": 100, "burst": 200},
            "export": {"default": 10, "rate": 5}
        },
        storage_config={
            "partitioning": "by_dt",
            "retention": "configurable"
        }
    )


# Sub-feature 9.2: Ingestion Routes

@router.post("/receipts", response_model=ReceiptIngestionResponse, status_code=status.HTTP_201_CREATED)
async def ingest_receipt(
    request: ReceiptIngestionRequest,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> ReceiptIngestionResponse:
    """Ingest single receipt per PRD Section 9.1."""
    try:
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # Extract tenant context
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        
        # RBAC check per FR-6 - ingestion requires evidence:write permission
        if claims:
            # Tenant ID will be derived later, but we check write permission
            tenant_id = iam_context.get("tenant_id") if iam_context else None
            allowed, error_msg = await check_rbac_permission(claims, "evidence:write", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions for receipt ingestion",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        # Validate receipt
        validator = ReceiptValidator()
        receipt_dict = request.dict()
        is_valid, error, normalized = await validator.validate_receipt(receipt_dict)
        if not is_valid:
            # Track validation error metric
            validation_errors.inc(error_type=error or "unknown")
            
            # Store invalid receipt in DLQ per FR-2
            try:
                dlq_service = DLQService(db)
                tenant_id_from_receipt = receipt_dict.get("tenant_id") or (iam_context.get("tenant_id") if iam_context else None)
                await dlq_service.store_invalid_receipt(receipt_dict, error or "Receipt validation failed", tenant_id_from_receipt)
                dlq_entries.inc(tenant_id=tenant_id_from_receipt or "unknown")
            except Exception as dlq_exc:
                logger.error("Failed to store invalid receipt in DLQ: %s", dlq_exc)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": error or "Receipt validation failed",
                        "details": None,
                        "retryable": False
                    }
                }
            )

        # Derive tenant ID
        resolver = TenantIdResolver()
        tenant_id, error = resolver.derive_tenant_id(normalized, iam_context)
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "TENANT_ID_MISSING",
                        "message": error or "Tenant ID cannot be determined",
                        "details": None,
                        "retryable": False
                    }
                }
            )

        # Ingest receipt
        ingestion_start = time.time()
        ingestion_service = ReceiptIngestionService(db)
        success, receipt_id, error = await ingestion_service.ingest_receipt(normalized, tenant_id)
        ingestion_duration.observe(time.time() - ingestion_start, ingestion_type="single")
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": error or "Receipt ingestion failed",
                        "details": None,
                        "retryable": True
                    }
                }
            )

        # Track successful ingestion
        receipts_ingested.inc(tenant_id=tenant_id, status="success")
        
        return ReceiptIngestionResponse(
            receipt_id=receipt_id or request.receipt_id,
            status="ingested",
            signature_verification_status="verified"
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "ingest_receipt",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "details": None,
                    "retryable": False
                }
            }
        )


@router.post("/receipts/bulk", status_code=status.HTTP_201_CREATED)
async def ingest_receipts_bulk(
    requests: list[ReceiptIngestionRequest],
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Bulk receipt ingestion per PRD Section 9.1."""
    # Get claims from request state
    claims = getattr(http_request.state, "claims", None)
    
    # RBAC check per FR-6 - bulk ingestion requires evidence:write permission
    if claims:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = iam_context.get("tenant_id") if iam_context else None
        allowed, error_msg = await check_rbac_permission(claims, "evidence:write", tenant_id, False)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": error_msg or "Insufficient permissions for bulk receipt ingestion",
                        "details": None,
                        "retryable": False
                    }
                }
            )
    
    results = []
    dlq_service = DLQService(db)
    headers = {"Authorization": authorization or ""}
    iam_context = extract_tenant_context(headers)
    
    for request in requests:
        try:
            response = await ingest_receipt(request, http_request, authorization, db)
            results.append({"receipt_id": response.receipt_id, "status": "success"})
        except HTTPException as http_exc:
            # If validation error, it's already in DLQ from ingest_receipt
            # For other HTTP errors, add to DLQ if it's a validation-related error
            error_detail = http_exc.detail.get("error", {}) if isinstance(http_exc.detail, dict) else {}
            if error_detail.get("code") == "VALIDATION_ERROR":
                # Already in DLQ, just record result
                pass
            results.append({"receipt_id": request.receipt_id, "status": "error", "error": str(http_exc.detail)})
        except Exception as exc:
            # For unexpected errors, try to store in DLQ
            try:
                receipt_dict = request.dict()
                tenant_id_from_receipt = receipt_dict.get("tenant_id") or (iam_context.get("tenant_id") if iam_context else None)
                await dlq_service.store_invalid_receipt(receipt_dict, f"Bulk ingestion error: {str(exc)}", tenant_id_from_receipt)
            except Exception:
                pass  # Don't fail bulk operation if DLQ write fails
            results.append({"receipt_id": request.receipt_id, "status": "error", "error": str(exc)})
    return {"results": results}


# Sub-feature 9.3: Query Routes

@router.post("/search", response_model=ReceiptSearchResponse)
async def search_receipts(
    request: ReceiptSearchRequest,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> ReceiptSearchResponse:
    """Search receipts per PRD Section 9.2."""
    try:
        # Extract tenant context
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = request.tenant_id or (iam_context.get("tenant_id") if iam_context else None)
        
        # Get claims from request state (set by IAMAuthMiddleware)
        claims = getattr(http_request.state, "claims", None)
        
        # Check if this is a system-wide query (no tenant_id specified)
        is_system_wide = not tenant_id
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:read", tenant_id, is_system_wide)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "TENANT_ID_MISSING",
                        "message": "Tenant ID required",
                        "details": None,
                        "retryable": False
                    }
                }
            )

        query_start = time.time()
        query_service = ReceiptQueryService(db)
        filters = request.dict(exclude={"tenant_id", "cursor", "limit"})
        receipts, next_cursor = query_service.search_receipts(filters, tenant_id, request.cursor, request.limit)
        query_duration.observe(time.time() - query_start, query_type="search")
        queries_total.inc(query_type="search", tenant_id=tenant_id)

        # Create meta-receipt for access audit
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": "search",
            "decision": "success",
            "receipt_count": len(receipts)
        })

        return ReceiptSearchResponse(
            receipts=receipts,
            next_cursor=next_cursor,
            total_count=len(receipts)
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Receipt search error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "details": None,
                    "retryable": False
                }
            }
        )


@router.post("/aggregate", response_model=ReceiptAggregateResponse)
async def aggregate_receipts(
    request: ReceiptAggregateRequest,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> ReceiptAggregateResponse:
    """Aggregate receipts per PRD Section 9.2."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = request.tenant_id or (iam_context.get("tenant_id") if iam_context else None)
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # Check if this is a system-wide query
        is_system_wide = not tenant_id
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:read", tenant_id, is_system_wide)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "TENANT_ID_MISSING", "message": "Tenant ID required"}}
            )

        query_start = time.time()
        aggregation_service = ReceiptAggregationService(db)
        result = aggregation_service.aggregate_receipts(
            request.filters or {},
            request.group_by,
            tenant_id,
            request.time_bucket
        )
        query_duration.observe(time.time() - query_start, query_type="aggregate")
        queries_total.inc(query_type="aggregate", tenant_id=tenant_id)

        # Create meta-receipt for access audit
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": "aggregate",
            "decision": "success",
            "receipt_count": result.get("total_count", 0)
        })

        return ReceiptAggregateResponse(
            aggregations=result.get("aggregations", {}),
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "aggregate_receipts",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/receipts/{receipt_id}")
async def get_receipt(
    receipt_id: str,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get receipt by ID per PRD Section 9.2."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = iam_context.get("tenant_id") if iam_context else None
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:read", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID required")

        query_service = ReceiptQueryService(db)
        receipts, _ = query_service.search_receipts({"receipt_id": receipt_id}, tenant_id, None, 1)

        if not receipts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Receipt not found"}}
            )

        # Create meta-receipt for access audit
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": f"get_receipt:{receipt_id}",
            "decision": "success",
            "receipt_count": 1
        })

        return receipts[0]
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "get_receipt",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# Sub-feature 9.4: Integrity Routes

@router.get("/receipts/{receipt_id}/verify")
async def verify_receipt(
    receipt_id: str,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Verify receipt integrity per PRD Section 9.3."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = iam_context.get("tenant_id") if iam_context else None
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:read", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID required")

        # Track integrity check metrics
        from .metrics import integrity_checks_total, integrity_check_duration
        integrity_start = time.time()
        
        integrity_service = IntegrityVerificationService(db)
        result = integrity_service.verify_receipt(receipt_id, tenant_id)
        
        # Record metrics
        integrity_duration = time.time() - integrity_start
        integrity_check_duration.observe(integrity_duration, check_type="verify_receipt")
        check_result = "success" if result.get("hash_valid") else "failure"
        integrity_checks_total.inc(check_type="verify_receipt", tenant_id=tenant_id, result=check_result)

        if "error" in result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result)

        # Create meta-receipt for access audit
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": f"verify_receipt:{receipt_id}",
            "decision": "success" if result.get("hash_valid") else "partial",
            "receipt_count": 1
        })

        return result
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "verify_receipt",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/verify_range")
async def verify_range(
    request: Dict[str, Any],
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """Verify receipt range integrity per PRD Section 9.3."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = request.get("tenant_id") or (iam_context.get("tenant_id") if iam_context else None)
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:read", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID required")

        # Track integrity check metrics
        from .metrics import integrity_checks_total, integrity_check_duration
        integrity_start = time.time()
        
        integrity_service = IntegrityVerificationService(db)
        result = integrity_service.verify_range(
            tenant_id,
            request.get("chain_id"),
            datetime.fromisoformat(request.get("from_timestamp")),
            datetime.fromisoformat(request.get("to_timestamp"))
        )
        
        # Record metrics
        integrity_duration = time.time() - integrity_start
        integrity_check_duration.observe(integrity_duration, check_type="verify_range")
        check_result = "success" if result.get("valid") else "failure"
        integrity_checks_total.inc(check_type="verify_range", tenant_id=tenant_id, result=check_result)

        # Create meta-receipt for access audit
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": f"verify_range:chain_id={request.get('chain_id')}",
            "decision": "success" if result.get("valid") else "partial",
            "receipt_count": result.get("receipt_count", 0)
        })

        return result
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "verify_range",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# Sub-feature 9.5: Courier Batch Routes

@router.post("/receipts/courier-batch", response_model=CourierBatchResponse, status_code=status.HTTP_201_CREATED)
async def ingest_courier_batch(
    request: CourierBatchRequest,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> CourierBatchResponse:
    """Ingest courier batch per PRD Section 9.4."""
    try:
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6 - courier batch ingestion requires evidence:write permission
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:write", request.tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions for courier batch ingestion",
                            "details": None,
                            "retryable": False
                        }
                    }
                )
        
        batch_service = CourierBatchService(db)
        success, batch_id, error = await batch_service.ingest_batch(request.dict(), request.tenant_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "VALIDATION_ERROR", "message": error}}
            )

        return CourierBatchResponse(
            batch_id=batch_id or request.batch_id,
            status="completed",
            receipt_count=len(request.receipts),
            timestamp=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "ingest_courier_batch",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/courier-batches/{batch_id}/merkle-proof", response_model=MerkleProofResponse)
def get_merkle_proof(
    batch_id: str,
    db: Session = Depends(get_database_session)
) -> MerkleProofResponse:
    """Get Merkle proof for batch per PRD Section 9.4."""
    try:
        proof_service = MerkleProofService(db)
        proof = proof_service.get_merkle_proof(batch_id)

        if not proof:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Batch not found"}}
            )

        return MerkleProofResponse(**proof)
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "get_merkle_proof",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# Sub-feature 9.6: Export Routes

@router.post("/export", response_model=ExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    request: ExportRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> ExportResponse:
    """Create export job per PRD Section 9.5."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = request.tenant_id or (iam_context.get("tenant_id") if iam_context else None)
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6 - export requires evidence:export permission
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:export", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions for export",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID required")

        # Check concurrent export limit per PRD NFR-3: 10 concurrent exports per tenant
        from .database.models import ExportJob
        active_exports = db.query(ExportJob).filter(
            ExportJob.tenant_id == tenant_id,
            ExportJob.status.in_(["pending", "processing"])
        ).count()
        
        if active_exports >= 10:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "code": "CONCURRENT_EXPORT_LIMIT_EXCEEDED",
                        "message": f"Maximum concurrent exports (10) reached for tenant. Active exports: {active_exports}",
                        "retryable": True,
                        "details": {
                            "active_exports": active_exports,
                            "max_concurrent": 10
                        }
                    }
                }
            )
        
        export_service = ExportService(db)
        export_id = export_service.create_export_job(request.dict(), tenant_id)
        
        # Track export job creation
        export_format = request.export_format.value if hasattr(request.export_format, 'value') else str(request.export_format)
        export_jobs.inc(tenant_id=tenant_id, format=export_format)
        
        # Get the export job to trigger background generation
        export_job = db.query(ExportJob).filter(ExportJob.export_id == UUID(export_id)).first()
        if export_job:
            # Trigger background file generation
            background_tasks.add_task(export_service._generate_export_file, export_job)

        # Create meta-receipt for access audit per FR-9
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": f"export:format={request.export_format.value if hasattr(request.export_format, 'value') else request.export_format}",
            "decision": "success",
            "receipt_count": None  # Will be known after export completes
        })

        return ExportResponse(
            export_id=export_id,
            status="pending",
            download_url=None,
            export_metadata=None
        )
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "create_export",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/export/{export_id}", response_model=ExportStatusResponse)
async def get_export_status(
    export_id: str,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> ExportStatusResponse:
    """Get export job status per PRD Section 9.5."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = iam_context.get("tenant_id") if iam_context else None
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:export", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID required")

        export_service = ExportService(db)
        status_data = export_service.get_export_status(export_id, tenant_id)

        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "RESOURCE_NOT_FOUND", "message": "Export not found"}}
            )

        return ExportStatusResponse(**status_data)
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "get_export_status",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# Sub-feature 9.7: Chain Traversal Routes

@router.get("/receipts/{receipt_id}/chain", response_model=ChainTraversalResponse)
async def get_receipt_chain(
    receipt_id: str,
    http_request: Request,
    direction: str = "both",
    max_depth: int = 10,
    include_metadata: bool = True,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> ChainTraversalResponse:
    """Traverse receipt chain per PRD Section 9.6."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = iam_context.get("tenant_id") if iam_context else None
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:read", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID required")

        chain_service = ChainTraversalService(db)
        result = chain_service.traverse_chain(receipt_id, tenant_id, direction, max_depth)

        # Create meta-receipt for access audit
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": f"chain_traversal:receipt_id={receipt_id},direction={direction}",
            "decision": "success",
            "receipt_count": result.get("traversal_depth", 0)
        })

        return ChainTraversalResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "traverse_chain",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/receipts/chain-query", response_model=ChainQueryResponse)
async def query_receipt_chain(
    request: ChainQueryRequest,
    http_request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_database_session)
) -> ChainQueryResponse:
    """Query receipt chains per PRD Section 9.6."""
    try:
        headers = {"Authorization": authorization or ""}
        iam_context = extract_tenant_context(headers)
        tenant_id = iam_context.get("tenant_id") if iam_context else None
        
        # Get claims from request state
        claims = getattr(http_request.state, "claims", None)
        
        # RBAC check per FR-6
        if claims:
            allowed, error_msg = await check_rbac_permission(claims, "evidence:read", tenant_id, False)
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": {
                            "code": "FORBIDDEN",
                            "message": error_msg or "Insufficient permissions",
                            "details": None,
                            "retryable": False
                        }
                    }
                )

        if not tenant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID required")

        chain_service = ChainTraversalService(db)
        if request.root_receipt_id:
            result = chain_service.traverse_chain(request.root_receipt_id, tenant_id, "both", 100)
            chain_count = len(result.get("receipts", []))
            
            # Create meta-receipt for access audit
            meta_service = MetaAuditService(db)
            meta_service.create_meta_receipt({
                "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
                "actor_type": "service",
                "tenant_ids": [tenant_id],
                "timestamp": datetime.utcnow(),
                "query_scope": f"chain_query:root_receipt_id={request.root_receipt_id}",
                "decision": "success",
                "receipt_count": chain_count
            })
            
            return ChainQueryResponse(
                receipts=result.get("receipts", []),
                chain_count=chain_count
            )

        # Create meta-receipt even for empty result
        meta_service = MetaAuditService(db)
        meta_service.create_meta_receipt({
            "requester_actor_id": iam_context.get("user_id") if iam_context else "unknown",
            "actor_type": "service",
            "tenant_ids": [tenant_id],
            "timestamp": datetime.utcnow(),
            "query_scope": "chain_query:no_root_receipt_id",
            "decision": "success",
            "receipt_count": 0
        })

        return ChainQueryResponse(receipts=[], chain_count=0)
    except HTTPException:
        raise
    except Exception as exc:
        # Structured logging per Rule 173
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "env": SERVICE_ENV,
            "host": SERVICE_HOST,
            "operation": "query_chain",
            "error.code": "INTERNAL_ERROR",
            "severity": "ERROR",
            "cause": str(exc)
        }
        logger.error(json.dumps(log_data_error))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
