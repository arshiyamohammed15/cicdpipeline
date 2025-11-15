"""
API routes for Deployment & Infrastructure (EPC-8) service.

What: FastAPI route handlers for deployment operations, environment parity, infrastructure status per deployment API contract
Why: Provides HTTP API endpoints for deployment operations, delegates to service layer
Reads/Writes: Reads HTTP request bodies, writes HTTP responses (no file I/O)
Contracts: Deployment API contract, error envelope per Rule 4171
Risks: Input validation failures, service unavailability, error message exposure
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, status
from .models import (
    DeployRequest, DeployResponse,
    EnvironmentParityRequest, EnvironmentParityResponse,
    InfrastructureStatusRequest, InfrastructureStatusResponse,
    HealthResponse,
    ErrorResponse, ErrorDetail
)
from .services import DeploymentService, EnvironmentParityService, InfrastructureStatusService

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton service instances
_deployment_service: Optional[DeploymentService] = None
_parity_service: Optional[EnvironmentParityService] = None
_status_service: Optional[InfrastructureStatusService] = None


def get_deployment_service() -> DeploymentService:
    """
    Dependency to get DeploymentService instance.

    Returns:
        DeploymentService instance
    """
    global _deployment_service
    if _deployment_service is None:
        _deployment_service = DeploymentService()
    return _deployment_service


def get_parity_service() -> EnvironmentParityService:
    """
    Dependency to get EnvironmentParityService instance.

    Returns:
        EnvironmentParityService instance
    """
    global _parity_service
    if _parity_service is None:
        _parity_service = EnvironmentParityService()
    return _parity_service


def get_status_service() -> InfrastructureStatusService:
    """
    Dependency to get InfrastructureStatusService instance.

    Returns:
        InfrastructureStatusService instance
    """
    global _status_service
    if _status_service is None:
        _status_service = InfrastructureStatusService()
    return _status_service


@router.post("/deploy", response_model=DeployResponse)
def deploy(
    request: DeployRequest,
    service: DeploymentService = Depends(get_deployment_service)
) -> DeployResponse:
    """
    Deploy to specified environment and target.

    Args:
        request: Deploy request with environment, target, etc.
        service: Deployment service instance

    Returns:
        Deploy response with deployment_id, status, etc.

    Raises:
        HTTPException: If deployment fails (with error envelope per Rule 4171)
    """
    try:
        result = service.deploy(
            environment=request.environment,
            target=request.target,
            service=request.service,
            config=request.config
        )
        return DeployResponse(**result)
    except ValueError as exc:
        error_code = "DEPLOYMENT_FAILED"
        error_message = str(exc)

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "deployment-infrastructure",
            "version": "1.0.0",
            "env": "development",
            "host": "localhost",
            "operation": "deploy",
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
        error_message = f"Deployment failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "deployment-infrastructure",
            "version": "1.0.0",
            "env": "development",
            "host": "localhost",
            "operation": "deploy",
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


@router.post("/parity", response_model=EnvironmentParityResponse)
def verify_parity(
    request: EnvironmentParityRequest,
    service: EnvironmentParityService = Depends(get_parity_service)
) -> EnvironmentParityResponse:
    """
    Verify environment parity between source and target.

    Args:
        request: Parity request with source and target environments
        service: Environment parity service instance

    Returns:
        Parity response with differences

    Raises:
        HTTPException: If parity check fails (with error envelope per Rule 4171)
    """
    try:
        result = service.verify_parity(
            source_environment=request.source_environment,
            target_environment=request.target_environment,
            check_resources=request.check_resources
        )
        return EnvironmentParityResponse(**result)
    except ValueError as exc:
        error_code = "PARITY_CHECK_FAILED"
        error_message = str(exc)

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "deployment-infrastructure",
            "version": "1.0.0",
            "env": "development",
            "host": "localhost",
            "operation": "verify_parity",
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
        error_message = f"Parity check failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "deployment-infrastructure",
            "version": "1.0.0",
            "env": "development",
            "host": "localhost",
            "operation": "verify_parity",
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


@router.get("/status", response_model=InfrastructureStatusResponse)
def get_infrastructure_status(
    environment: Optional[str] = None,
    resource_type: Optional[str] = None,
    service: InfrastructureStatusService = Depends(get_status_service)
) -> InfrastructureStatusResponse:
    """
    Get infrastructure status.

    Args:
        environment: Environment to check (optional query parameter)
        resource_type: Resource type to check (optional query parameter)
        service: Infrastructure status service instance

    Returns:
        Infrastructure status response

    Raises:
        HTTPException: If status check fails (with error envelope per Rule 4171)
    """
    try:
        result = service.get_status(
            environment=environment,
            resource_type=resource_type
        )
        return InfrastructureStatusResponse(**result)
    except Exception as exc:
        error_code = "SERVER_ERROR"
        error_message = f"Status check failed: {str(exc)}"

        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "deployment-infrastructure",
            "version": "1.0.0",
            "env": "development",
            "host": "localhost",
            "operation": "get_status",
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


@router.get("/deployments/{deployment_id}")
def get_deployment(
    deployment_id: str,
    service: DeploymentService = Depends(get_deployment_service)
) -> Dict[str, Any]:
    """
    Get deployment status by deployment_id.

    Args:
        deployment_id: Deployment identifier
        service: Deployment service instance

    Returns:
        Deployment status

    Raises:
        HTTPException: If deployment not found (with error envelope per Rule 4171)
    """
    deployment = service.get_deployment_status(deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "DEPLOYMENT_NOT_FOUND",
                    "message": f"Deployment {deployment_id} not found",
                    "details": None
                }
            }
        )
    return deployment
