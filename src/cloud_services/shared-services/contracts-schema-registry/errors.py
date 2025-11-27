"""
Error handling for Contracts & Schema Registry.

What: Comprehensive error codes, HTTP status mapping, retry guidance per PRD
Why: Provides consistent error handling across all endpoints
Reads/Writes: Reads error conditions, writes error responses
Contracts: PRD error code enumeration and HTTP status mapping
Risks: Error message exposure, incorrect status codes
"""

import uuid
from typing import Dict, Any, Optional
from enum import Enum

from .models import ErrorResponse, ErrorDetail


class ErrorCode(str, Enum):
    """Error code enumeration per PRD."""

    # Validation errors
    SCHEMA_VALIDATION_FAILED = "SCHEMA_VALIDATION_FAILED"
    INVALID_SCHEMA_DEFINITION = "INVALID_SCHEMA_DEFINITION"
    CONTRACT_VIOLATION = "CONTRACT_VIOLATION"

    # Not found errors
    SCHEMA_NOT_FOUND = "SCHEMA_NOT_FOUND"
    CONTRACT_NOT_FOUND = "CONTRACT_NOT_FOUND"
    VERSION_NOT_FOUND = "VERSION_NOT_FOUND"

    # Compatibility errors
    COMPATIBILITY_ERROR = "COMPATIBILITY_ERROR"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    SCHEMA_DEPENDENCY_VIOLATION = "SCHEMA_DEPENDENCY_VIOLATION"

    # Transformation errors
    TRANSFORMATION_FAILED = "TRANSFORMATION_FAILED"

    # Access errors
    TENANT_ACCESS_DENIED = "TENANT_ACCESS_DENIED"
    INVALID_TENANT_CONTEXT = "INVALID_TENANT_CONTEXT"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    UNAUTHORIZED = "UNAUTHORIZED"

    # Resource errors
    SCHEMA_ALREADY_EXISTS = "SCHEMA_ALREADY_EXISTS"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # System errors
    INVALID_REQUEST = "INVALID_REQUEST"
    RATE_LIMITED = "RATE_LIMITED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# HTTP status code mapping per PRD
ERROR_HTTP_STATUS = {
    ErrorCode.INVALID_REQUEST: 400,
    ErrorCode.INVALID_SCHEMA_DEFINITION: 400,
    ErrorCode.SCHEMA_VALIDATION_FAILED: 400,
    ErrorCode.TRANSFORMATION_FAILED: 400,
    ErrorCode.UNAUTHENTICATED: 401,
    ErrorCode.UNAUTHORIZED: 403,
    ErrorCode.TENANT_ACCESS_DENIED: 403,
    ErrorCode.SCHEMA_NOT_FOUND: 404,
    ErrorCode.CONTRACT_NOT_FOUND: 404,
    ErrorCode.VERSION_NOT_FOUND: 404,
    ErrorCode.SCHEMA_ALREADY_EXISTS: 409,
    ErrorCode.VERSION_CONFLICT: 409,
    ErrorCode.SCHEMA_DEPENDENCY_VIOLATION: 409,
    ErrorCode.COMPATIBILITY_ERROR: 422,
    ErrorCode.CONTRACT_VIOLATION: 422,
    ErrorCode.RATE_LIMITED: 429,
    ErrorCode.QUOTA_EXCEEDED: 429,
    ErrorCode.DEPENDENCY_UNAVAILABLE: 503,
    ErrorCode.INTERNAL_ERROR: 500,
    ErrorCode.INVALID_TENANT_CONTEXT: 500,
}

# Retriable errors per PRD
RETRIABLE_ERRORS = {
    ErrorCode.DEPENDENCY_UNAVAILABLE,
    ErrorCode.RATE_LIMITED,
    ErrorCode.INTERNAL_ERROR,  # If idempotent
}

# Error messages per PRD
ERROR_MESSAGES = {
    ErrorCode.SCHEMA_VALIDATION_FAILED: "Data does not conform to schema",
    ErrorCode.INVALID_SCHEMA_DEFINITION: "Schema definition is malformed or invalid",
    ErrorCode.CONTRACT_VIOLATION: "Data violates contract rules",
    ErrorCode.SCHEMA_NOT_FOUND: "Schema with given ID not found",
    ErrorCode.CONTRACT_NOT_FOUND: "Contract with given ID not found",
    ErrorCode.VERSION_NOT_FOUND: "Schema version not found",
    ErrorCode.COMPATIBILITY_ERROR: "Schema versions are incompatible",
    ErrorCode.VERSION_CONFLICT: "Version conflict during update",
    ErrorCode.SCHEMA_DEPENDENCY_VIOLATION: "Schema dependency constraint violated",
    ErrorCode.TRANSFORMATION_FAILED: "Data transformation between schemas failed",
    ErrorCode.TENANT_ACCESS_DENIED: "Access denied due to tenant isolation",
    ErrorCode.INVALID_TENANT_CONTEXT: "Tenant context missing or invalid",
    ErrorCode.UNAUTHENTICATED: "Authentication required",
    ErrorCode.UNAUTHORIZED: "Insufficient permissions",
    ErrorCode.SCHEMA_ALREADY_EXISTS: "Schema with same name/version already exists",
    ErrorCode.QUOTA_EXCEEDED: "Tenant quota limit exceeded",
    ErrorCode.INVALID_REQUEST: "Request format or parameters invalid",
    ErrorCode.RATE_LIMITED: "Rate limit exceeded",
    ErrorCode.DEPENDENCY_UNAVAILABLE: "Required dependency service unavailable",
    ErrorCode.INTERNAL_ERROR: "Internal server error",
}


def create_error_response(
    error_code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> ErrorResponse:
    """
    Create error response per PRD error schema.

    Args:
        error_code: Error code
        message: Optional custom error message
        details: Optional additional error details
        tenant_id: Optional tenant identifier
        correlation_id: Optional correlation identifier

    Returns:
        ErrorResponse model
    """
    return ErrorResponse(
        error=ErrorDetail(
            error_code=error_code.value,
            message=message or ERROR_MESSAGES.get(error_code, "An error occurred"),
            details=details,
            correlation_id=correlation_id or str(uuid.uuid4()),
            retriable=error_code in RETRIABLE_ERRORS,
            tenant_id=tenant_id
        )
    )


def get_http_status(error_code: ErrorCode) -> int:
    """
    Get HTTP status code for error code.

    Args:
        error_code: Error code

    Returns:
        HTTP status code
    """
    return ERROR_HTTP_STATUS.get(error_code, 500)


def is_retriable(error_code: ErrorCode) -> bool:
    """
    Check if error is retriable.

    Args:
        error_code: Error code

    Returns:
        True if retriable, False otherwise
    """
    return error_code in RETRIABLE_ERRORS
