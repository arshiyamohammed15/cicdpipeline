"""
FastAPI routes for Data Governance & Privacy Module (M22).

All HTTP handlers delegate to DataGovernanceService (business logic layer).
"""

from __future__ import annotations

import logging

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .models import (
    ClassificationRequest,
    ClassificationResponse,
    ConsentCheckRequest,
    ConsentCheckResponse,
    HealthResponse,
    MetricsResponse,
    MetricsSnapshot,
    ConfigResponse,
    PrivacyEnforcementRequest,
    PrivacyEnforcementResponse,
    LineageRecord,
    LineageQueryResponse,
    RetentionEvaluationRequest,
    RetentionEvaluationResponse,
    RightsRequest,
    RightsResponse,
    ErrorResponse,
    ErrorDetail,
)
from .services import DataGovernanceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/privacy/v1", tags=["data-governance-privacy"])

_service: DataGovernanceService = DataGovernanceService()


def get_service() -> DataGovernanceService:
    """Dependency injection helper."""
    return _service


# --------------------------------------------------------------------------- #
# Utility
# --------------------------------------------------------------------------- #


def _handle_exception(exc: Exception, code: str, tenant_id: str | None = None) -> HTTPException:
    logger.exception("Privacy module error [%s]: %s", code, exc)
    detail = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=str(exc),
            details=None,
            tenant_id=tenant_id,
            retriable=False,
        )
    )
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail.model_dump())


# --------------------------------------------------------------------------- #
# Health / Metrics / Config
# --------------------------------------------------------------------------- #


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(service: DataGovernanceService = Depends(get_service)) -> MetricsResponse:
    metrics = service.service_metrics()
    snapshot = MetricsSnapshot(
        classification=metrics["classification"],
        consent_p95_ms=metrics["consent_p95_ms"],
        privacy_p95_ms=metrics["privacy_p95_ms"],
        lineage_p95_ms=metrics["lineage_p95_ms"],
    )
    return MetricsResponse(metrics=snapshot)


@router.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    return ConfigResponse(
        api_endpoints={
            "health": "/privacy/v1/health",
            "metrics": "/privacy/v1/metrics",
            "config": "/privacy/v1/config",
            "classification": "/privacy/v1/classification",
            "consent": "/privacy/v1/consent/check",
            "lineage": "/privacy/v1/lineage",
            "retention": "/privacy/v1/retention/evaluate",
            "compliance": "/privacy/v1/compliance",
            "rights": "/privacy/v1/rights/request",
        },
        performance_requirements={
            "data_classification_ms_max": 100,
            "consent_check_ms_max": 20,
            "privacy_check_ms_max": 50,
            "lineage_trace_ms_max": 200,
            "max_memory_mb": 4096,
        },
    )


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #


@router.post("/classification", response_model=ClassificationResponse)
def classify_data(
    request: ClassificationRequest,
    service: DataGovernanceService = Depends(get_service),
) -> ClassificationResponse:
    try:
        result = service.classify_data(
            tenant_id=request.tenant_id,
            data_location=request.data_location,
            data_content=request.data_content,
            context=request.context,
            hints=request.classification_hints,
        )
        return ClassificationResponse(
            classification_level=result["classification_level"],
            sensitivity_tags=result["sensitivity_tags"],
            confidence=result["classification_confidence"],
            classification_id=result["classification_id"],
            data_id=result["data_id"],
            review_required=result["review_required"],
            performance=result["performance"],
        )
    except Exception as exc:
        raise _handle_exception(exc, "CLASSIFICATION_FAILED", request.tenant_id) from exc


# --------------------------------------------------------------------------- #
# Consent
# --------------------------------------------------------------------------- #


@router.post("/consent/check", response_model=ConsentCheckResponse)
def check_consent(
    request: ConsentCheckRequest,
    service: DataGovernanceService = Depends(get_service),
) -> ConsentCheckResponse:
    try:
        result = service.check_consent(
            tenant_id=request.tenant_id,
            data_subject_id=request.data_subject_id,
            purpose=request.purpose,
            data_categories=request.data_categories,
            legal_basis=request.legal_basis,
        )
        return ConsentCheckResponse(**result)
    except Exception as exc:
        raise _handle_exception(exc, "CONSENT_CHECK_ERROR", request.tenant_id) from exc


# --------------------------------------------------------------------------- #
# Privacy Enforcement
# --------------------------------------------------------------------------- #


@router.post("/compliance", response_model=PrivacyEnforcementResponse)
def enforce_privacy(
    request: PrivacyEnforcementRequest,
    service: DataGovernanceService = Depends(get_service),
) -> PrivacyEnforcementResponse:
    try:
        consent_result = request.consent_result.model_dump() if request.consent_result else None
        result = service.enforce_privacy(
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            action=request.action,
            resource=request.resource,
            policy_id=request.policy_id,
            context=request.context,
            classification_record=request.classification_record,
            consent_result=consent_result,
            override_token=request.override_token,
        )
        return PrivacyEnforcementResponse(**result)
    except Exception as exc:
        raise _handle_exception(exc, "PRIVACY_CHECK_ERROR", request.tenant_id) from exc


# --------------------------------------------------------------------------- #
# Lineage
# --------------------------------------------------------------------------- #


@router.post("/lineage", response_model=Dict[str, Any])
def record_lineage(
    request: LineageRecord,
    service: DataGovernanceService = Depends(get_service),
) -> Dict[str, Any]:
    try:
        return service.record_lineage(**request.dict())
    except Exception as exc:
        raise _handle_exception(exc, "LINEAGE_CAPTURE_ERROR", request.tenant_id) from exc


@router.get("/lineage", response_model=LineageQueryResponse)
def query_lineage(
    tenant_id: str = Query(...),
    data_id: str = Query(...),
    service: DataGovernanceService = Depends(get_service),
) -> LineageQueryResponse:
    try:
        result = service.query_lineage(tenant_id=tenant_id, data_id=data_id)
        return LineageQueryResponse(**result)
    except Exception as exc:
        raise _handle_exception(exc, "LINEAGE_QUERY_ERROR", tenant_id) from exc


# --------------------------------------------------------------------------- #
# Retention
# --------------------------------------------------------------------------- #


@router.post("/retention/evaluate", response_model=RetentionEvaluationResponse)
def evaluate_retention(
    request: RetentionEvaluationRequest,
    service: DataGovernanceService = Depends(get_service),
) -> RetentionEvaluationResponse:
    try:
        result = service.evaluate_retention(
            tenant_id=request.tenant_id,
            data_category=request.data_category,
            last_activity_months=request.last_activity_months,
        )
        return RetentionEvaluationResponse(**result)
    except Exception as exc:
        raise _handle_exception(exc, "RETENTION_EVALUATION_ERROR", request.tenant_id) from exc


# --------------------------------------------------------------------------- #
# Rights Requests
# --------------------------------------------------------------------------- #


@router.post("/rights/request", response_model=RightsResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_rights_request(
    request: RightsRequest,
    service: DataGovernanceService = Depends(get_service),
) -> RightsResponse:
    try:
        result = service.submit_rights_request(
            tenant_id=request.tenant_id,
            data_subject_id=request.data_subject_id,
            right_type=request.right_type.value,
            verification_data=request.verification_data,
            additional_info=request.additional_info,
        )
        return RightsResponse(
            request_id=result["request_id"],
            estimated_completion=datetime.fromisoformat(result["estimated_completion"]),
            next_steps=result["next_steps"],
        )
    except Exception as exc:
        raise _handle_exception(exc, "RIGHTS_REQUEST_ERROR", request.tenant_id) from exc
