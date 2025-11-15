"""
API routes for Configuration & Policy Management (M23).

What: FastAPI route handlers for all endpoints per PRD v1.1.0
Why: Provides HTTP API endpoints for policy, configuration, compliance operations
Reads/Writes: Reads HTTP request bodies, writes HTTP responses (no file I/O)
Contracts: Policy API contract (8 endpoints), error envelope per PRD
Risks: Input validation failures, service unavailability, error message exposure
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, status, Query, Path
from .models import (
    CreatePolicyRequest, PolicyResponse, EvaluatePolicyRequest, EvaluatePolicyResponse,
    CreateConfigurationRequest, ConfigurationResponse,
    ComplianceCheckRequest, ComplianceCheckResponse,
    ListGoldStandardsResponse, AuditSummaryResponse,
    TriggerRemediationRequest, RemediationResponse,
    HealthResponse, MetricsResponse, ConfigResponse,
    ErrorResponse, ErrorDetail
)
from .services import (
    PolicyEvaluationEngine, PolicyService, ConfigurationService,
    ComplianceChecker, GoldStandardService, ReceiptGenerator
)
from .dependencies import (
    MockM21IAM, MockM27EvidenceLedger, MockM29DataPlane,
    MockM33KeyManagement, MockM34SchemaRegistry, MockM32TrustPlane
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service instances
_policy_evaluation_engine: Optional[PolicyEvaluationEngine] = None
_policy_service: Optional[PolicyService] = None
_configuration_service: Optional[ConfigurationService] = None
_compliance_checker: Optional[ComplianceChecker] = None
_gold_standard_service: Optional[GoldStandardService] = None
_receipt_generator: Optional[ReceiptGenerator] = None

# Initialize dependencies
_evidence_ledger = MockM27EvidenceLedger()
_key_management = MockM33KeyManagement()
_data_plane = MockM29DataPlane()
_schema_registry = MockM34SchemaRegistry()
_iam = MockM21IAM()
_trust_plane = MockM32TrustPlane()


def get_policy_evaluation_engine() -> PolicyEvaluationEngine:
    """Dependency to get PolicyEvaluationEngine instance."""
    global _policy_evaluation_engine
    if _policy_evaluation_engine is None:
        _policy_evaluation_engine = PolicyEvaluationEngine(_data_plane, _evidence_ledger, _key_management)
    return _policy_evaluation_engine


def get_policy_service() -> PolicyService:
    """Dependency to get PolicyService instance."""
    global _policy_service
    if _policy_service is None:
        _policy_service = PolicyService(_evidence_ledger, _key_management, _schema_registry)
    return _policy_service


def get_configuration_service() -> ConfigurationService:
    """Dependency to get ConfigurationService instance."""
    global _configuration_service
    if _configuration_service is None:
        from .services import ConfigurationDriftDetector
        drift_detector = ConfigurationDriftDetector(_evidence_ledger, _key_management)
        _configuration_service = ConfigurationService(_evidence_ledger, _key_management, _schema_registry, drift_detector)
    return _configuration_service


def get_compliance_checker() -> ComplianceChecker:
    """Dependency to get ComplianceChecker instance."""
    global _compliance_checker
    if _compliance_checker is None:
        _compliance_checker = ComplianceChecker(_evidence_ledger, _key_management, _data_plane)
    return _compliance_checker


def get_gold_standard_service() -> GoldStandardService:
    """Dependency to get GoldStandardService instance."""
    global _gold_standard_service
    if _gold_standard_service is None:
        _gold_standard_service = GoldStandardService()
    return _gold_standard_service


def get_receipt_generator() -> ReceiptGenerator:
    """Dependency to get ReceiptGenerator instance."""
    global _receipt_generator
    if _receipt_generator is None:
        _receipt_generator = ReceiptGenerator(_evidence_ledger, _key_management)
    return _receipt_generator


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Health check endpoint per PRD.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        version="1.1.0",
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    """
    Get runtime metrics snapshot per PRD.

    Returns:
        MetricsResponse with metrics array
    """
    return MetricsResponse(metrics=[])


@router.get("/config", response_model=ConfigResponse)
def get_module_config() -> ConfigResponse:
    """
    Get effective configuration for the module per PRD.

    Returns:
        ConfigResponse with module configuration
    """
    return ConfigResponse(
        config={},
        timestamp=datetime.utcnow().isoformat()
    )


@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(
    request: CreatePolicyRequest,
    tenant_id: str = Query(..., description="Tenant identifier"),
    http_request: Request = None,
    service: PolicyService = Depends(get_policy_service)
) -> PolicyResponse:
    """
    Create a new policy per PRD (lines 337-366).

    Args:
        request: Create policy request
        tenant_id: Tenant identifier
        service: Policy service instance

    Returns:
        PolicyResponse with policy_id, version, status

    Raises:
        HTTPException: If policy creation fails
    """
    try:
        # Extract user_id from JWT token in Authorization header
        created_by = "system"  # Default fallback
        if http_request:
            auth_header = http_request.headers.get("Authorization", "")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix
                try:
                    # Decode JWT token to extract user_id (sub claim)
                    import jwt
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    created_by = decoded.get("sub", "system")
                except Exception:
                    # If token parsing fails, use default
                    pass

        result = service.create_policy(request, tenant_id, created_by)
        return result
    except ValueError as exc:
        error_code = "INVALID_REQUEST"
        error_message = str(exc)

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "configuration-policy-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "create_policy",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": False,
                    "tenant_id": tenant_id
                }
            }
        )
    except Exception as exc:
        error_code = "INTERNAL_ERROR"
        error_message = f"Policy creation failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "configuration-policy-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "create_policy",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True,
                    "tenant_id": tenant_id
                }
            }
        )


@router.post("/policies/{policy_id}/evaluate", response_model=EvaluatePolicyResponse)
def evaluate_policy(
    policy_id: str = Path(..., description="Policy identifier"),
    request: EvaluatePolicyRequest = ...,
    service: PolicyEvaluationEngine = Depends(get_policy_evaluation_engine)
) -> EvaluatePolicyResponse:
    """
    Evaluate policy against context per PRD (lines 368-400).

    Args:
        policy_id: Policy identifier
        request: Evaluate policy request
        service: Policy evaluation engine instance

    Returns:
        EvaluatePolicyResponse with decision, reason, violations

    Raises:
        HTTPException: If policy evaluation fails
    """
    try:
        result = service.evaluate_policy(
            policy_id=policy_id,
            context=request.context,
            principal=request.principal,
            resource=request.resource,
            action=request.action,
            tenant_id=request.tenant_id,
            environment=request.environment
        )
        return result
    except Exception as exc:
        error_code = "EVALUATION_ERROR"
        error_message = f"Policy evaluation failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "configuration-policy-management",
            "version": "1.1.0",
            "env": "development",
            "host": "localhost",
            "operation": "evaluate_policy",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True,
                    "tenant_id": request.tenant_id
                }
            }
        )


@router.post("/configurations", response_model=ConfigurationResponse, status_code=status.HTTP_201_CREATED)
def create_configuration(
    request: CreateConfigurationRequest,
    tenant_id: str = Query(..., description="Tenant identifier"),
    service: ConfigurationService = Depends(get_configuration_service)
) -> ConfigurationResponse:
    """
    Create a new configuration per PRD (lines 402-432).

    Args:
        request: Create configuration request
        tenant_id: Tenant identifier
        service: Configuration service instance

    Returns:
        ConfigurationResponse with config_id, version, status

    Raises:
        HTTPException: If configuration creation fails
    """
    try:
        result = service.create_configuration(request, tenant_id)
        return result
    except ValueError as exc:
        error_code = "INVALID_REQUEST"
        error_message = str(exc)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": False,
                    "tenant_id": tenant_id
                }
            }
        )
    except Exception as exc:
        error_code = "INTERNAL_ERROR"
        error_message = f"Configuration creation failed: {str(exc)}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True,
                    "tenant_id": tenant_id
                }
            }
        )


@router.get("/standards", response_model=ListGoldStandardsResponse)
def list_gold_standards(
    framework: Optional[str] = Query(None, description="Framework filter"),
    tenant_id: str = Query(..., description="Tenant identifier"),
    service: GoldStandardService = Depends(get_gold_standard_service)
) -> ListGoldStandardsResponse:
    """
    List gold standards for a tenant per PRD (lines 434-459).

    Args:
        framework: Optional framework filter
        tenant_id: Tenant identifier
        service: Gold standard service instance

    Returns:
        ListGoldStandardsResponse with items array

    Raises:
        HTTPException: If listing fails
    """
    try:
        items = service.list_gold_standards(framework, tenant_id)
        return ListGoldStandardsResponse(items=items)
    except Exception as exc:
        error_code = "INTERNAL_ERROR"
        error_message = f"Failed to list gold standards: {str(exc)}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True,
                    "tenant_id": tenant_id
                }
            }
        )


@router.post("/compliance/check", response_model=ComplianceCheckResponse)
def check_compliance(
    request: ComplianceCheckRequest,
    service: ComplianceChecker = Depends(get_compliance_checker)
) -> ComplianceCheckResponse:
    """
    Check compliance against gold standards per PRD (lines 460-487).

    Args:
        request: Compliance check request
        service: Compliance checker instance

    Returns:
        ComplianceCheckResponse with compliant, score, missing_controls

    Raises:
        HTTPException: If compliance check fails
    """
    try:
        result = service.check_compliance(
            framework=request.framework,
            context=request.context,
            evidence_required=request.evidence_required
        )
        return result
    except ValueError as exc:
        error_code = "INVALID_REQUEST"
        error_message = str(exc)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": False,
                    "tenant_id": request.context.get("tenant_id")
                }
            }
        )
    except Exception as exc:
        error_code = "INTERNAL_ERROR"
        error_message = f"Compliance check failed: {str(exc)}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True,
                    "tenant_id": request.context.get("tenant_id")
                }
            }
        )


@router.get("/audit", response_model=AuditSummaryResponse)
def get_audit_summary(
    tenant_id: str = Query(..., description="Tenant identifier")
) -> AuditSummaryResponse:
    """
    Retrieve audit trail summary per PRD (lines 489-500).

    Args:
        tenant_id: Tenant identifier

    Returns:
        AuditSummaryResponse with audit summary data

    Raises:
        HTTPException: If audit retrieval fails
    """
    try:
        # Retrieve audit summary from M27 Evidence Ledger
        receipts = _evidence_ledger.get_receipts_by_tenant(tenant_id)

        # Aggregate summary data
        summary = {
            "total_receipts": len(receipts),
            "receipts_by_type": {},
            "receipts_by_status": {},
            "recent_receipts": []
        }

        # Count receipts by type and status
        for receipt in receipts:
            receipt_type = receipt.get("operation", "unknown")
            summary["receipts_by_type"][receipt_type] = summary["receipts_by_type"].get(receipt_type, 0) + 1

            receipt_status = receipt.get("status", "unknown")
            summary["receipts_by_status"][receipt_status] = summary["receipts_by_status"].get(receipt_status, 0) + 1

        # Get recent receipts (last 10)
        sorted_receipts = sorted(receipts, key=lambda r: r.get("ts", ""), reverse=True)
        summary["recent_receipts"] = [
            {
                "receipt_id": r.get("receipt_id"),
                "operation": r.get("operation"),
                "timestamp": r.get("ts"),
                "status": r.get("status", "unknown")
            }
            for r in sorted_receipts[:10]
        ]

        return AuditSummaryResponse(
            tenant_id=tenant_id,
            summary=summary,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as exc:
        error_code = "INTERNAL_ERROR"
        error_message = f"Failed to retrieve audit summary: {str(exc)}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True,
                    "tenant_id": tenant_id
                }
            }
        )


@router.post("/remediation", response_model=RemediationResponse)
def trigger_remediation(
    request: TriggerRemediationRequest,
    service: ReceiptGenerator = Depends(get_receipt_generator)
) -> RemediationResponse:
    """
    Trigger remediation action per PRD.

    Args:
        request: Trigger remediation request
        service: Receipt generator instance

    Returns:
        RemediationResponse with remediation_id, status

    Raises:
        HTTPException: If remediation fails
    """
    try:
        # Generate remediation receipt
        receipt = service.generate_remediation_receipt(
            target_type=request.target_type,
            target_id=request.target_id,
            reason=request.reason,
            remediation_type=request.remediation_type,
            status="pending"
        )

        return RemediationResponse(
            remediation_id=receipt["receipt_id"],
            status="pending",
            target_type=request.target_type,
            target_id=request.target_id
        )
    except Exception as exc:
        error_code = "INTERNAL_ERROR"
        error_message = f"Remediation failed: {str(exc)}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "error_code": error_code,
                    "message": error_message,
                    "details": None,
                    "correlation_id": str(uuid.uuid4()),
                    "retriable": True,
                    "tenant_id": None
                }
            }
        )
