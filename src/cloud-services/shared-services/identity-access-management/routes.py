"""
API routes for Identity & Access Management (IAM) service.

What: FastAPI route handlers for token verification, access decisions, policy management per IAM spec v1.1.0
Why: Provides HTTP API endpoints for IAM operations, delegates to service layer
Reads/Writes: Reads HTTP request bodies, writes HTTP responses (no file I/O)
Contracts: IAM API contract (verify, decision, policies endpoints), IPC protocol error envelope (Rule 4171)
Risks: Input validation failures, service unavailability, error message exposure
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, status
from .models import (
    VerifyRequest, VerifyResponse,
    DecisionRequest, DecisionResponse,
    PolicyBundle, BreakGlassRequest,
    HealthResponse, MetricsResponse, ConfigResponse,
    ErrorResponse, ErrorDetail
)
from .services import IAMService

logger = logging.getLogger(__name__)

router = APIRouter()


# Singleton service instance to maintain policy state across requests
_iam_service_instance: Optional[IAMService] = None

def get_service() -> IAMService:
    """
    Dependency to get IAMService instance (singleton for test compatibility).

    Returns:
        IAMService instance
    """
    global _iam_service_instance
    if _iam_service_instance is None:
        _iam_service_instance = IAMService()
    return _iam_service_instance


@router.post("/verify", response_model=VerifyResponse)
def verify_identity(
    request: VerifyRequest,
    service: IAMService = Depends(get_service)
) -> VerifyResponse:
    """
    Verify identity/token per IAM spec section 4.

    Args:
        request: Verify request with token
        service: IAM service instance

    Returns:
        Verify response with sub, scope, valid_until

    Raises:
        HTTPException: If token verification fails (with error envelope per Rule 4171)
    """
    try:
        result = service.verify_token(request)
        return result
    except ValueError as exc:
        error_code = "AUTH_FAILED"
        error_message = str(exc)

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "verify_identity",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )
    except Exception as exc:
        error_code = "SERVER_ERROR"
        error_message = f"Token verification failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "verify_identity",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )


@router.post("/decision", response_model=DecisionResponse)
def access_decision(
    request: DecisionRequest,
    service: IAMService = Depends(get_service)
) -> DecisionResponse:
    """
    Evaluate an access decision or JIT elevation per IAM spec section 3.

    Args:
        request: Decision request with subject, action, resource, context, elevation
        service: IAM service instance

    Returns:
        Decision response with decision, reason, expires_at, receipt_id

    Raises:
        HTTPException: If decision evaluation fails (with error envelope per Rule 4171)
    """
    try:
        result = service.evaluate_decision(request)
        return result
    except ValueError as exc:
        error_code = "BAD_REQUEST"
        error_message = str(exc)

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "access_decision",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )
    except Exception as exc:
        error_code = "SERVER_ERROR"
        error_message = f"Decision evaluation failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "access_decision",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )


@router.post("/break-glass", response_model=DecisionResponse)
def trigger_break_glass(
    request: BreakGlassRequest,
    service: IAMService = Depends(get_service)
) -> DecisionResponse:
    """
    Trigger break-glass access per IAM spec section 3.3.

    Args:
        request: Break-glass request with subject, incident_id, justification, approver_identity
        service: IAM service instance

    Returns:
        Decision response with BREAK_GLASS_GRANTED decision

    Raises:
        HTTPException: If break-glass fails (with error envelope per Rule 4171)
    """
    try:
        result = service.trigger_break_glass(request)
        return result
    except ValueError as exc:
        error_code = "FORBIDDEN"
        error_message = str(exc)

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "trigger_break_glass",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )
    except Exception as exc:
        error_code = "SERVER_ERROR"
        error_message = f"Break-glass failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "trigger_break_glass",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )


@router.put("/policies", status_code=status.HTTP_202_ACCEPTED)
def upsert_policies(
    bundle: PolicyBundle,
    service: IAMService = Depends(get_service)
) -> Dict[str, Any]:
    """
    Upsert policy bundle (versioned) per IAM spec section 8.

    Args:
        bundle: Policy bundle to upsert
        service: IAM service instance

    Returns:
        Response with snapshot_id

    Raises:
        HTTPException: If policy upsert fails (with error envelope per Rule 4171)
    """
    try:
        snapshot_id = service.upsert_policies(bundle)
        return {
            "bundle_id": bundle.bundle_id,
            "version": bundle.version,
            "snapshot_id": f"sha256:{snapshot_id}",
            "status": "accepted"
        }
    except ValueError as exc:
        error_code = "BAD_REQUEST"
        error_message = str(exc)

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "upsert_policies",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )
    except Exception as exc:
        error_code = "SERVER_ERROR"
        error_message = f"Policy upsert failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "identity-access-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "upsert_policies",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )


@router.get("/health", response_model=HealthResponse)
def health_check(
    service: IAMService = Depends(get_service)
) -> HealthResponse:
    """
    Health check endpoint.

    Args:
        service: IAM service instance

    Returns:
        Health response with status and timestamp
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    service: IAMService = Depends(get_service)
) -> MetricsResponse:
    """
    Metrics endpoint.

    Args:
        service: IAM service instance

    Returns:
        Metrics response with counts and latencies
    """
    metrics = service.get_metrics()
    return MetricsResponse(
        authentication_count=metrics["authentication_count"],
        decision_count=metrics["decision_count"],
        policy_count=metrics["policy_count"],
        average_auth_latency_ms=metrics["average_auth_latency_ms"],
        average_decision_latency_ms=metrics["average_decision_latency_ms"],
        average_policy_latency_ms=metrics["average_policy_latency_ms"],
        timestamp=datetime.utcnow()
    )


@router.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    """
    Configuration endpoint per IAM spec section 1.

    Returns:
        Config response with module identity and performance requirements
    """
    return ConfigResponse(
        module_id="M21",
        version="1.1.0",
        api_endpoints={
            "health": "/iam/v1/health",
            "metrics": "/iam/v1/metrics",
            "config": "/iam/v1/config",
            "verify": "/iam/v1/verify",
            "decision": "/iam/v1/decision",
            "policies": "/iam/v1/policies"
        },
        performance_requirements={
            "authentication_response_ms_max": 200,
            "policy_evaluation_ms_max": 50,
            "access_decision_ms_max": 100,
            "token_validation_ms_max": 10,
            "max_memory_mb": 512
        },
        timestamp=datetime.utcnow()
    )
