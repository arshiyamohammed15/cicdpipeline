"""
API routes for Key Management Service (KMS).

What: FastAPI route handlers for key generation, signing, verification, encryption, decryption per KMS spec v0.1.0
Why: Provides HTTP API endpoints for KMS operations, delegates to service layer
Reads/Writes: Reads HTTP request bodies, writes HTTP responses (no file I/O)
Contracts: KMS API contract (keys, sign, verify, encrypt, decrypt endpoints), error envelope per spec
Risks: Input validation failures, service unavailability, error message exposure
"""

import base64
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import Response
from .models import (
    GenerateKeyRequest, GenerateKeyResponse,
    SignDataRequest, SignDataResponse,
    VerifySignatureRequest, VerifySignatureResponse,
    EncryptDataRequest, EncryptDataResponse,
    DecryptDataRequest, DecryptDataResponse,
    RotateKeyRequest, RotateKeyResponse,
    RevokeKeyRequest, RevokeKeyResponse,
    IngestTrustAnchorRequest, IngestTrustAnchorResponse,
    HealthResponse, ConfigResponse,
    ErrorResponse, ErrorDetail,
    KMSContext
)
from .services import (
    KMSService,
    DEFAULT_KEY_ROTATION_SCHEDULE,
    DEFAULT_ROTATION_GRACE_PERIOD,
    ALLOWED_ALGORITHMS,
    DEFAULT_MAX_USAGE_PER_DAY,
    DUAL_AUTHORIZATION_OPERATIONS
)
from .dependencies import MockM27EvidenceLedger, MockM29DataPlane, MockM32TrustPlane, MockM21IAM
from .hsm import MockHSM

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize service instance
_kms_service: Optional[KMSService] = None


def get_service() -> KMSService:
    """
    Dependency to get KMSService instance.

    Returns:
        KMSService instance
    """
    global _kms_service
    if _kms_service is None:
        _kms_service = KMSService(
            hsm=MockHSM(),
            evidence_ledger=MockM27EvidenceLedger(),
            data_plane=MockM29DataPlane(),
            trust_plane=MockM32TrustPlane(),
            iam=MockM21IAM()
        )
    return _kms_service


def get_tenant_context(request: Request) -> Dict[str, str]:
    """
    Extract tenant context from request state (set by mTLS middleware).

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with tenant_id, environment, plane, module_id
    """
    return {
        "tenant_id": getattr(request.state, "tenant_id", "dev-tenant"),
        "environment": getattr(request.state, "environment", "dev"),
        "plane": getattr(request.state, "plane", "laptop"),
        "module_id": getattr(request.state, "module_id", "M21")  # Code identifier for EPC-1 (Identity & Access Management)
    }


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    details: Optional[Dict[str, Any]] = None,
    retryable: bool = False
) -> HTTPException:
    """
    Create error response per KMS spec Error Model.

    Args:
        code: Error code
        message: Error message
        status_code: HTTP status code
        details: Optional error details
        retryable: Whether error is retryable

    Returns:
        HTTPException with ErrorResponse
    """
    error_detail = ErrorDetail(
        code=code,
        message=message,
        details=details,
        retryable=retryable
    )
    error_response = ErrorResponse(error=error_detail)

    log_data_error = {
        "timestamp": datetime.utcnow().timestamp(),
        "level": "ERROR",
        "service": "key-management-service",
        "version": "0.1.0",
        "env": "development",
        "host": "localhost",
        "operation": "api_error",
        "error.code": code,
        "severity": "ERROR",
        "cause": message
    }
    logger.error(json.dumps(log_data_error))

    return HTTPException(
        status_code=status_code,
        detail=error_response.model_dump()
    )


@router.post("/keys", response_model=GenerateKeyResponse, status_code=status.HTTP_201_CREATED)
def generate_key(
    request: GenerateKeyRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> GenerateKeyResponse:
    """
    Generate a new cryptographic key per KMS spec.

    Args:
        request: Generate key request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Generate key response with key_id and public_key

    Raises:
        HTTPException: If key generation fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Validate tenant context matches request
        if context["tenant_id"] != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch between mTLS and request",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Check dual-authorization if required
        approval_token = request.approval_token or http_request.headers.get("X-Approval-Token")
        is_authorized, auth_error = service.policy_enforcer.check_dual_authorization(
            "key_lifecycle",
            approval_token=approval_token
        )
        if not is_authorized:
            raise create_error_response(
                "UNAUTHORIZED",
                auth_error or "Dual authorization required",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Generate key
        key_id, public_key = service.lifecycle_manager.generate_key(
            tenant_id=request.tenant_id,
            environment=request.environment,
            plane=request.plane,
            key_type=request.key_type,
            key_usage=request.key_usage,
            key_alias=request.key_alias
        )

        # Publish event
        payload = {
            "key_id": key_id,
            "key_type": request.key_type,
            "key_usage": request.key_usage,
            "key_state": "active"
        }
        service.event_publisher.publish_event(
            "key_generated",
            request.tenant_id,
            request.environment,
            request.plane,
            payload
        )

        # Generate receipt
        kms_context = KMSContext(
            key_id=key_id,
            operation_type="generate",
            algorithm=request.key_type,
            key_size_bits=2048 if "2048" in request.key_type else 256,
            success=True,
            error_code=None
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "key_generated",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        service.metrics["key_generation_count"] += 1
        service.metrics["key_generation_latencies"].append(latency_ms)
        if len(service.metrics["key_generation_latencies"]) > 1000:
            service.metrics["key_generation_latencies"] = service.metrics["key_generation_latencies"][-1000:]

        return GenerateKeyResponse(key_id=key_id, public_key=public_key)

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Key generation failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Key generation failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.post("/sign", response_model=SignDataResponse)
def sign_data(
    request: SignDataRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> SignDataResponse:
    """
    Create a digital signature over data per KMS spec.

    Args:
        request: Sign data request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Sign data response with signature and key_id

    Raises:
        HTTPException: If signing fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Retrieve key metadata
        key_metadata = service.lifecycle_manager.retrieve_key_metadata(request.key_id)
        if not key_metadata:
            raise create_error_response(
                "KEY_NOT_FOUND",
                f"Key not found: {request.key_id}",
                status.HTTP_404_NOT_FOUND,
                details={"key_id": request.key_id},
                retryable=False
            )

        # Validate tenant isolation
        if key_metadata.tenant_id != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Check key state - must be active for cryptographic operations
        if key_metadata.key_state == "destroyed":
            raise create_error_response(
                "KEY_REVOKED",
                f"Key has been revoked: {request.key_id}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )
        elif key_metadata.key_state in ["pending_rotation", "archived"]:
            raise create_error_response(
                "KEY_INACTIVE",
                f"Key is not active: {key_metadata.key_state}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )

        # Evaluate access policy
        is_allowed, policy_error = service.policy_enforcer.evaluate_access_policy(
            key_metadata,
            context["module_id"],
            "sign"
        )
        if not is_allowed:
            raise create_error_response(
                "POLICY_VIOLATION",
                policy_error or "Access denied by policy",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Decode data
        try:
            data = base64.b64decode(request.data)
        except Exception as exc:
            raise create_error_response(
                "INVALID_REQUEST",
                f"Invalid base64 data: {str(exc)}",
                status.HTTP_400_BAD_REQUEST,
                retryable=False
            )

        # Sign data
        signature_bytes, algorithm = service.crypto_ops.sign_data(
            request.key_id,
            data,
            request.algorithm,
            request.tenant_id
        )

        # Increment usage
        service.policy_enforcer.increment_usage(request.key_id)

        # Publish event
        operation_id = str(uuid.uuid4())
        payload = {
            "key_id": request.key_id,
            "operation_id": operation_id,
            "algorithm": algorithm
        }
        service.event_publisher.publish_event(
            "signature_created",
            request.tenant_id,
            request.environment,
            request.plane,
            payload
        )

        # Generate receipt
        kms_context = KMSContext(
            key_id=request.key_id,
            operation_type="sign",
            algorithm=algorithm,
            key_size_bits=2048 if key_metadata.key_type == "RSA-2048" else 256,
            success=True,
            error_code=None
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "signature_created",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        service.metrics["signing_count"] += 1
        service.metrics["signing_latencies"].append(latency_ms)
        if len(service.metrics["signing_latencies"]) > 1000:
            service.metrics["signing_latencies"] = service.metrics["signing_latencies"][-1000:]

        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        return SignDataResponse(signature=signature_b64, key_id=request.key_id)

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Signing failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Signing failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.post("/verify", response_model=VerifySignatureResponse)
def verify_signature(
    request: VerifySignatureRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> VerifySignatureResponse:
    """
    Verify a digital signature per KMS spec.

    Args:
        request: Verify signature request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Verify signature response with valid flag, key_id, and algorithm

    Raises:
        HTTPException: If verification fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Retrieve key metadata
        key_metadata = service.lifecycle_manager.retrieve_key_metadata(request.key_id)
        if not key_metadata:
            raise create_error_response(
                "KEY_NOT_FOUND",
                f"Key not found: {request.key_id}",
                status.HTTP_404_NOT_FOUND,
                details={"key_id": request.key_id},
                retryable=False
            )

        # Validate tenant isolation
        if key_metadata.tenant_id != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Check key state - must be active for cryptographic operations
        if key_metadata.key_state == "destroyed":
            raise create_error_response(
                "KEY_REVOKED",
                f"Key has been revoked: {request.key_id}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )
        elif key_metadata.key_state in ["pending_rotation", "archived"]:
            raise create_error_response(
                "KEY_INACTIVE",
                f"Key is not active: {key_metadata.key_state}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )

        # Evaluate access policy
        is_allowed, policy_error = service.policy_enforcer.evaluate_access_policy(
            key_metadata,
            context["module_id"],
            "verify"
        )
        if not is_allowed:
            raise create_error_response(
                "POLICY_VIOLATION",
                policy_error or "Access denied by policy",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Decode data and signature
        try:
            data = base64.b64decode(request.data)
            signature = base64.b64decode(request.signature)
        except Exception as exc:
            raise create_error_response(
                "INVALID_REQUEST",
                f"Invalid base64 data: {str(exc)}",
                status.HTTP_400_BAD_REQUEST,
                retryable=False
            )

        # Verify signature
        is_valid, algorithm = service.crypto_ops.verify_signature(
            request.key_id,
            data,
            signature,
            request.algorithm,
            request.tenant_id
        )

        # Publish event
        operation_id = str(uuid.uuid4())
        payload = {
            "key_id": request.key_id,
            "operation_id": operation_id,
            "valid": is_valid
        }
        service.event_publisher.publish_event(
            "signature_verified",
            request.tenant_id,
            request.environment,
            request.plane,
            payload
        )

        # Generate receipt
        kms_context = KMSContext(
            key_id=request.key_id,
            operation_type="verify",
            algorithm=algorithm,
            key_size_bits=2048 if key_metadata.key_type == "RSA-2048" else 256,
            success=is_valid,
            error_code=None if is_valid else "SIGNATURE_INVALID"
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "signature_verified",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        service.metrics["verification_count"] += 1
        service.metrics["verification_latencies"].append(latency_ms)
        if len(service.metrics["verification_latencies"]) > 1000:
            service.metrics["verification_latencies"] = service.metrics["verification_latencies"][-1000:]

        return VerifySignatureResponse(
            valid=is_valid,
            key_id=request.key_id,
            algorithm=algorithm
        )

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Verification failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Verification failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.post("/encrypt", response_model=EncryptDataResponse)
def encrypt_data(
    request: EncryptDataRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> EncryptDataResponse:
    """
    Encrypt plaintext using a managed key per KMS spec.

    Args:
        request: Encrypt data request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Encrypt data response with ciphertext, key_id, algorithm, and iv

    Raises:
        HTTPException: If encryption fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Retrieve key metadata
        key_metadata = service.lifecycle_manager.retrieve_key_metadata(request.key_id)
        if not key_metadata:
            raise create_error_response(
                "KEY_NOT_FOUND",
                f"Key not found: {request.key_id}",
                status.HTTP_404_NOT_FOUND,
                details={"key_id": request.key_id},
                retryable=False
            )

        # Validate tenant isolation
        if key_metadata.tenant_id != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Check key state - must be active for cryptographic operations
        if key_metadata.key_state == "destroyed":
            raise create_error_response(
                "KEY_REVOKED",
                f"Key has been revoked: {request.key_id}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )
        elif key_metadata.key_state in ["pending_rotation", "archived"]:
            raise create_error_response(
                "KEY_INACTIVE",
                f"Key is not active: {key_metadata.key_state}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )

        # Evaluate access policy
        is_allowed, policy_error = service.policy_enforcer.evaluate_access_policy(
            key_metadata,
            context["module_id"],
            "encrypt"
        )
        if not is_allowed:
            raise create_error_response(
                "POLICY_VIOLATION",
                policy_error or "Access denied by policy",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Decode plaintext and AAD
        try:
            plaintext = base64.b64decode(request.plaintext)
            aad = base64.b64decode(request.aad) if request.aad else None
        except Exception as exc:
            raise create_error_response(
                "INVALID_REQUEST",
                f"Invalid base64 data: {str(exc)}",
                status.HTTP_400_BAD_REQUEST,
                retryable=False
            )

        # Encrypt data
        ciphertext, iv, algorithm = service.crypto_ops.encrypt_data(
            request.key_id,
            plaintext,
            request.algorithm,
            aad,
            request.tenant_id
        )

        # Increment usage
        service.policy_enforcer.increment_usage(request.key_id)

        # Generate receipt
        kms_context = KMSContext(
            key_id=request.key_id,
            operation_type="encrypt",
            algorithm=algorithm,
            key_size_bits=256,
            success=True,
            error_code=None
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "encrypt",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        service.metrics["encryption_count"] += 1
        service.metrics["encryption_latencies"].append(latency_ms)
        if len(service.metrics["encryption_latencies"]) > 1000:
            service.metrics["encryption_latencies"] = service.metrics["encryption_latencies"][-1000:]

        ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')
        iv_b64 = base64.b64encode(iv).decode('utf-8')
        return EncryptDataResponse(
            ciphertext=ciphertext_b64,
            key_id=request.key_id,
            algorithm=algorithm,
            iv=iv_b64
        )

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Encryption failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Encryption failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.post("/decrypt", response_model=DecryptDataResponse)
def decrypt_data(
    request: DecryptDataRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> DecryptDataResponse:
    """
    Decrypt ciphertext using a managed key per KMS spec.

    Args:
        request: Decrypt data request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Decrypt data response with plaintext and key_id

    Raises:
        HTTPException: If decryption fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Retrieve key metadata
        key_metadata = service.lifecycle_manager.retrieve_key_metadata(request.key_id)
        if not key_metadata:
            raise create_error_response(
                "KEY_NOT_FOUND",
                f"Key not found: {request.key_id}",
                status.HTTP_404_NOT_FOUND,
                details={"key_id": request.key_id},
                retryable=False
            )

        # Validate tenant isolation
        if key_metadata.tenant_id != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Check key state - must be active or archived for decryption (archived keys can decrypt historical data)
        if key_metadata.key_state == "destroyed":
            raise create_error_response(
                "KEY_REVOKED",
                f"Key has been revoked: {request.key_id}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )
        elif key_metadata.key_state == "pending_rotation":
            raise create_error_response(
                "KEY_INACTIVE",
                f"Key is not active: {key_metadata.key_state}",
                status.HTTP_409_CONFLICT,
                details={"key_id": request.key_id, "key_state": key_metadata.key_state},
                retryable=False
            )

        # Evaluate access policy
        is_allowed, policy_error = service.policy_enforcer.evaluate_access_policy(
            key_metadata,
            context["module_id"],
            "decrypt"
        )
        if not is_allowed:
            raise create_error_response(
                "POLICY_VIOLATION",
                policy_error or "Access denied by policy",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Decode ciphertext, IV, and AAD
        try:
            ciphertext = base64.b64decode(request.ciphertext)
            iv = base64.b64decode(request.iv)
            aad = base64.b64decode(request.aad) if request.aad else None
        except Exception as exc:
            raise create_error_response(
                "INVALID_REQUEST",
                f"Invalid base64 data: {str(exc)}",
                status.HTTP_400_BAD_REQUEST,
                retryable=False
            )

        # Decrypt data
        plaintext = service.crypto_ops.decrypt_data(
            request.key_id,
            ciphertext,
            iv,
            request.algorithm,
            aad,
            request.tenant_id
        )

        # Generate receipt
        kms_context = KMSContext(
            key_id=request.key_id,
            operation_type="decrypt",
            algorithm=request.algorithm or "AES-256-GCM",
            key_size_bits=256,
            success=True,
            error_code=None
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "decrypt",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        service.metrics["decryption_count"] += 1
        service.metrics["decryption_latencies"].append(latency_ms)
        if len(service.metrics["decryption_latencies"]) > 1000:
            service.metrics["decryption_latencies"] = service.metrics["decryption_latencies"][-1000:]

        plaintext_b64 = base64.b64encode(plaintext).decode('utf-8')
        return DecryptDataResponse(plaintext=plaintext_b64, key_id=request.key_id)

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Decryption failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Decryption failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.get("/health", response_model=HealthResponse)
def get_health(
    service: KMSService = Depends(get_service)
) -> HealthResponse:
    """
    Health status of KMS and its critical dependencies per KMS spec.

    Args:
        service: KMS service instance

    Returns:
        Health response with status and checks array
    """
    checks = []

    # Check HSM
    hsm_available = service.hsm.is_available()
    checks.append({
        "name": "hsm",
        "status": "pass" if hsm_available else "fail",
        "detail": "HSM connectivity check" if hsm_available else "HSM unavailable"
    })

    # Check metadata storage (M29)
    try:
        # Try to list keys as a connectivity check
        service.data_plane.list_keys()
        checks.append({
            "name": "storage",
            "status": "pass",
            "detail": "Metadata storage available"
        })
    except Exception as exc:
        checks.append({
            "name": "storage",
            "status": "fail",
            "detail": f"Metadata storage unavailable: {str(exc)}"
        })

    # Check trust store (M32)
    try:
        # Try to validate a mock certificate
        service.trust_plane.validate_certificate(b"mock-cert")
        checks.append({
            "name": "trust_store",
            "status": "pass",
            "detail": "Trust store available"
        })
    except Exception as exc:
        checks.append({
            "name": "trust_store",
            "status": "warn",
            "detail": f"Trust store check failed: {str(exc)}"
        })

    # Determine overall status
    if any(check["status"] == "fail" for check in checks):
        overall_status = "unhealthy"
    elif any(check["status"] == "warn" for check in checks):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return HealthResponse(status=overall_status, checks=checks)


@router.get("/metrics", response_class=Response)
def get_metrics(
    service: KMSService = Depends(get_service)
) -> Response:
    """
    Exposes service-level metrics in Prometheus format per KMS spec.

    Args:
        service: KMS service instance

    Returns:
        Metrics in Prometheus text format
    """
    metrics = service.get_metrics()

    # Format as Prometheus text format
    lines = [
        f"# HELP kms_requests_total Total number of KMS requests by operation and status",
        f"# TYPE kms_requests_total counter",
        f'kms_requests_total{{operation="key_generation",status="success"}} {metrics["key_generation_count"]}',
        f'kms_requests_total{{operation="sign",status="success"}} {metrics["signing_count"]}',
        f'kms_requests_total{{operation="verify",status="success"}} {metrics["verification_count"]}',
        f'kms_requests_total{{operation="encrypt",status="success"}} {metrics["encryption_count"]}',
        f'kms_requests_total{{operation="decrypt",status="success"}} {metrics["decryption_count"]}',
        f"# HELP kms_request_errors_total Total number of KMS request errors by error code",
        f"# TYPE kms_request_errors_total counter",
    ]

    # Add error counts by error code
    for error_code, count in metrics.get("request_errors", {}).items():
        lines.append(f'kms_request_errors_total{{error_code="{error_code}"}} {count}')

    lines.extend([
        f"# HELP kms_operation_latency_ms Operation latency in milliseconds",
        f"# TYPE kms_operation_latency_ms histogram",
        f'kms_operation_latency_ms{{operation="key_generation"}} {metrics["average_key_generation_latency_ms"]:.2f}',
        f'kms_operation_latency_ms{{operation="sign"}} {metrics["average_signing_latency_ms"]:.2f}',
        f'kms_operation_latency_ms{{operation="verify"}} {metrics["average_verification_latency_ms"]:.2f}',
        f'kms_operation_latency_ms{{operation="encrypt"}} {metrics["average_encryption_latency_ms"]:.2f}',
        f'kms_operation_latency_ms{{operation="decrypt"}} {metrics["average_decryption_latency_ms"]:.2f}',
        f"# HELP kms_keys_total Total number of keys by key_type and key_state",
        f"# TYPE kms_keys_total gauge",
    ])

    # Add key counts by key_type and key_state
    for key_label, count in metrics.get("key_counts", {}).items():
        # key_label format: "RSA-2048_active" -> split into key_type and key_state
        parts = key_label.rsplit("_", 1)
        if len(parts) == 2:
            key_type, key_state = parts
            lines.append(f'kms_keys_total{{key_type="{key_type}",key_state="{key_state}"}} {count}')

    metrics_text = "\n".join(lines)
    return Response(
        content=metrics_text,
        media_type="text/plain"
    )


@router.post("/keys/{key_id}/rotate", response_model=RotateKeyResponse, status_code=status.HTTP_200_OK)
def rotate_key(
    key_id: str,
    request: RotateKeyRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> RotateKeyResponse:
    """
    Rotate a cryptographic key per KMS spec.

    Args:
        key_id: Key identifier to rotate
        request: Rotate key request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Rotate key response with old_key_id, new_key_id, and new_public_key

    Raises:
        HTTPException: If key rotation fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Validate tenant context matches request
        if context["tenant_id"] != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch between mTLS and request",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Check dual-authorization if required
        approval_token = request.approval_token or http_request.headers.get("X-Approval-Token")
        is_authorized, auth_error = service.policy_enforcer.check_dual_authorization(
            "key_lifecycle",
            approval_token=approval_token
        )
        if not is_authorized:
            raise create_error_response(
                "UNAUTHORIZED",
                auth_error or "Dual authorization required",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Verify key exists and belongs to tenant
        key_metadata = service.lifecycle_manager.retrieve_key_metadata(key_id)
        if not key_metadata:
            raise create_error_response(
                "KEY_NOT_FOUND",
                f"Key not found: {key_id}",
                status.HTTP_404_NOT_FOUND,
                details={"key_id": key_id},
                retryable=False
            )

        if key_metadata.tenant_id != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Rotate key with event publisher
        new_key_id, new_public_key = service.lifecycle_manager.rotate_key(
            key_id=key_id,
            tenant_id=request.tenant_id,
            environment=request.environment,
            plane=request.plane,
            event_publisher=service.event_publisher
        )

        # Generate receipt
        kms_context = KMSContext(
            key_id=new_key_id,
            operation_type="generate",
            algorithm=key_metadata.key_type,
            key_size_bits=2048 if "2048" in key_metadata.key_type else 256,
            success=True,
            error_code=None
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "key_rotated",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        service.metrics["key_generation_count"] += 1
        service.metrics["key_generation_latencies"].append(latency_ms)
        if len(service.metrics["key_generation_latencies"]) > 1000:
            service.metrics["key_generation_latencies"] = service.metrics["key_generation_latencies"][-1000:]

        return RotateKeyResponse(
            old_key_id=key_id,
            new_key_id=new_key_id,
            new_public_key=new_public_key
        )

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Key rotation failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Key rotation failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.post("/keys/{key_id}/revoke", response_model=RevokeKeyResponse, status_code=status.HTTP_200_OK)
def revoke_key(
    key_id: str,
    request: RevokeKeyRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> RevokeKeyResponse:
    """
    Revoke a cryptographic key per KMS spec.

    Args:
        key_id: Key identifier to revoke
        request: Revoke key request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Revoke key response with key_id and revoked_at

    Raises:
        HTTPException: If key revocation fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Validate tenant context matches request
        if context["tenant_id"] != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch between mTLS and request",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Check dual-authorization if required
        approval_token = request.approval_token or http_request.headers.get("X-Approval-Token")
        is_authorized, auth_error = service.policy_enforcer.check_dual_authorization(
            "key_lifecycle",
            approval_token=approval_token
        )
        if not is_authorized:
            raise create_error_response(
                "UNAUTHORIZED",
                auth_error or "Dual authorization required",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Verify key exists and belongs to tenant
        key_metadata = service.lifecycle_manager.retrieve_key_metadata(key_id)
        if not key_metadata:
            raise create_error_response(
                "KEY_NOT_FOUND",
                f"Key not found: {key_id}",
                status.HTTP_404_NOT_FOUND,
                details={"key_id": key_id},
                retryable=False
            )

        if key_metadata.tenant_id != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Revoke key with event publisher
        service.lifecycle_manager.revoke_key(
            key_id=key_id,
            tenant_id=request.tenant_id,
            revocation_reason=request.revocation_reason,
            environment=request.environment,
            plane=request.plane,
            event_publisher=service.event_publisher
        )

        # Generate receipt
        revoked_at = datetime.utcnow()
        kms_context = KMSContext(
            key_id=key_id,
            operation_type="generate",
            algorithm=key_metadata.key_type,
            key_size_bits=2048 if "2048" in key_metadata.key_type else 256,
            success=True,
            error_code=None
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "key_revoked",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        # Note: No specific metric for revocation, but operation is logged

        return RevokeKeyResponse(
            key_id=key_id,
            revoked_at=revoked_at.isoformat()
        )

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Key revocation failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Key revocation failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.post("/trust-anchors", response_model=IngestTrustAnchorResponse, status_code=status.HTTP_201_CREATED)
def ingest_trust_anchor(
    request: IngestTrustAnchorRequest,
    http_request: Request,
    service: KMSService = Depends(get_service)
) -> IngestTrustAnchorResponse:
    """
    Ingest a trust anchor (certificate) per KMS spec.

    Args:
        request: Ingest trust anchor request
        service: KMS service instance
        http_request: FastAPI request object

    Returns:
        Ingest trust anchor response with trust_anchor_id and anchor_type

    Raises:
        HTTPException: If trust anchor ingestion fails (with error envelope per KMS spec)
    """
    start_time = time.perf_counter()
    context = get_tenant_context(http_request)

    try:
        # Validate tenant context matches request
        if context["tenant_id"] != request.tenant_id:
            raise create_error_response(
                "UNAUTHORIZED",
                "Tenant mismatch between mTLS and request",
                status.HTTP_403_FORBIDDEN,
                retryable=False
            )

        # Decode certificate
        try:
            certificate_bytes = base64.b64decode(request.certificate)
        except Exception as exc:
            raise create_error_response(
                "INVALID_REQUEST",
                f"Invalid base64 certificate: {str(exc)}",
                status.HTTP_400_BAD_REQUEST,
                retryable=False
            )

        # Ingest certificate with event publisher
        trust_anchor_id = service.trust_store_manager.ingest_certificate(
            certificate=certificate_bytes,
            anchor_type=request.anchor_type,
            tenant_id=request.tenant_id,
            environment=request.environment,
            plane=request.plane,
            event_publisher=service.event_publisher
        )

        # Generate receipt
        kms_context = KMSContext(
            key_id="",  # Not applicable for trust anchor
            operation_type="generate",
            algorithm="X.509",
            key_size_bits=2048,  # Default for X.509 certificates
            success=True,
            error_code=None
        )
        service.receipt_generator.generate_receipt(
            request.tenant_id,
            request.environment,
            request.plane,
            "trust_anchor_updated",
            kms_context,
            context["module_id"]
        )

        # Update metrics
        latency_ms = (time.perf_counter() - start_time) * 1000
        # Note: No specific metric for trust anchor ingestion, but operation is logged

        return IngestTrustAnchorResponse(
            trust_anchor_id=trust_anchor_id,
            anchor_type=request.anchor_type
        )

    except HTTPException as exc:
        # Track error metrics
        if hasattr(exc, 'detail') and isinstance(exc.detail, dict):
            error_code = exc.detail.get("error", {}).get("code", "UNKNOWN_ERROR")
            service.increment_error_count(error_code)
        raise
    except ValueError as exc:
        raise create_error_response(
            "INVALID_REQUEST",
            str(exc),
            status.HTTP_400_BAD_REQUEST,
            retryable=False
        )
    except ConnectionError as exc:
        logger.error(f"Dependency unavailable: {exc}", exc_info=True)
        raise create_error_response(
            "DEPENDENCY_UNAVAILABLE",
            f"Dependency unavailable: {str(exc)}",
            status.HTTP_503_SERVICE_UNAVAILABLE,
            retryable=True
        )
    except Exception as exc:
        logger.error(f"Trust anchor ingestion failed: {exc}", exc_info=True)
        raise create_error_response(
            "INTERNAL_ERROR",
            f"Trust anchor ingestion failed: {str(exc)}",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True
        )


@router.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    """
    Returns effective, read-only KMS configuration per KMS spec.

    Returns:
        Config response with rotation schedule, grace period, algorithms, etc.
    """
    return ConfigResponse(
        key_rotation_schedule=DEFAULT_KEY_ROTATION_SCHEDULE,
        rotation_grace_period=DEFAULT_ROTATION_GRACE_PERIOD,
        allowed_algorithms=ALLOWED_ALGORITHMS,
        max_usage_per_day_default=DEFAULT_MAX_USAGE_PER_DAY,
        dual_authorization_required_operations=DUAL_AUTHORIZATION_OPERATIONS
    )
