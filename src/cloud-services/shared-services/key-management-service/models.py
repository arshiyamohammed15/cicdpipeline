"""
Pydantic models for Key Management Service (KMS).

What: Defines Pydantic v2 models for request/response validation per KMS spec v0.1.0
Why: Ensures type safety, input validation, and standardized API contracts
Reads/Writes: Reads request data, writes response data (no file I/O)
Contracts: KMS API contract (keys, sign, verify, encrypt, decrypt endpoints), error model
Risks: Model validation failures may expose internal error details if not handled properly
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# Request Models

class GenerateKeyRequest(BaseModel):
    """Request model for key generation."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    key_type: str = Field(..., description="Key type", pattern="^(RSA-2048|Ed25519|AES-256)$")
    key_usage: List[str] = Field(
        ...,
        description="List of key usage types",
        min_items=1
    )
    key_alias: Optional[str] = Field(None, description="Optional human-readable alias")
    approval_token: Optional[str] = Field(None, description="Optional approval token for dual-authorization")


class SignDataRequest(BaseModel):
    """Request model for data signing."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    key_id: str = Field(..., description="Key identifier")
    data: str = Field(..., description="Base64-encoded payload to sign", min_length=1)
    algorithm: Optional[str] = Field(None, description="Algorithm", pattern="^(RS256|EdDSA)$")


class VerifySignatureRequest(BaseModel):
    """Request model for signature verification."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    key_id: str = Field(..., description="Key identifier")
    data: str = Field(..., description="Base64-encoded payload that was signed", min_length=1)
    signature: str = Field(..., description="Base64-encoded signature", min_length=1)
    algorithm: Optional[str] = Field(None, description="Algorithm", pattern="^(RS256|EdDSA)$")


class EncryptDataRequest(BaseModel):
    """Request model for data encryption."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    key_id: str = Field(..., description="Key identifier")
    plaintext: str = Field(..., description="Base64-encoded plaintext", min_length=1)
    algorithm: Optional[str] = Field(None, description="Algorithm", pattern="^(AES-256-GCM|CHACHA20-POLY1305)$")
    aad: Optional[str] = Field(None, description="Optional Base64-encoded additional authenticated data")


class DecryptDataRequest(BaseModel):
    """Request model for data decryption."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    key_id: str = Field(..., description="Key identifier")
    ciphertext: str = Field(..., description="Base64-encoded ciphertext", min_length=1)
    iv: str = Field(..., description="Initialization vector / nonce used at encryption time", min_length=1)
    algorithm: Optional[str] = Field(None, description="Algorithm", pattern="^(AES-256-GCM|CHACHA20-POLY1305)$")
    aad: Optional[str] = Field(None, description="Optional Base64-encoded additional authenticated data")


class RotateKeyRequest(BaseModel):
    """Request model for key rotation."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    approval_token: Optional[str] = Field(None, description="Optional approval token for dual-authorization")


class RevokeKeyRequest(BaseModel):
    """Request model for key revocation."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    revocation_reason: str = Field(
        ...,
        description="Revocation reason",
        pattern="^(compromised|retired|policy_violation)$"
    )
    approval_token: Optional[str] = Field(None, description="Optional approval token for dual-authorization")


class IngestTrustAnchorRequest(BaseModel):
    """Request model for trust anchor ingestion."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    certificate: str = Field(..., description="Base64-encoded certificate", min_length=1)
    anchor_type: str = Field(
        ...,
        description="Anchor type",
        pattern="^(internal_ca|external_ca|root)$"
    )


# Response Models

class GenerateKeyResponse(BaseModel):
    """Response model for key generation."""

    key_id: str = Field(..., description="Key identifier")
    public_key: str = Field(..., description="PEM-encoded public key")


class SignDataResponse(BaseModel):
    """Response model for data signing."""

    signature: str = Field(..., description="Base64-encoded signature")
    key_id: str = Field(..., description="Key identifier")


class VerifySignatureResponse(BaseModel):
    """Response model for signature verification."""

    valid: bool = Field(..., description="Whether signature is valid")
    key_id: str = Field(..., description="Key identifier")
    algorithm: Optional[str] = Field(None, description="Algorithm used during verification")


class EncryptDataResponse(BaseModel):
    """Response model for data encryption."""

    ciphertext: str = Field(..., description="Base64-encoded ciphertext")
    key_id: str = Field(..., description="Key identifier")
    algorithm: str = Field(..., description="Algorithm used")
    iv: str = Field(..., description="Initialization vector / nonce")


class DecryptDataResponse(BaseModel):
    """Response model for data decryption."""

    plaintext: str = Field(..., description="Base64-encoded plaintext")
    key_id: str = Field(..., description="Key identifier")


class RotateKeyResponse(BaseModel):
    """Response model for key rotation."""

    old_key_id: str = Field(..., description="Old key identifier")
    new_key_id: str = Field(..., description="New key identifier")
    new_public_key: str = Field(..., description="PEM-encoded new public key")


class RevokeKeyResponse(BaseModel):
    """Response model for key revocation."""

    key_id: str = Field(..., description="Revoked key identifier")
    revoked_at: str = Field(..., description="Revocation timestamp (ISO 8601)")


class IngestTrustAnchorResponse(BaseModel):
    """Response model for trust anchor ingestion."""

    trust_anchor_id: str = Field(..., description="Trust anchor identifier")
    anchor_type: str = Field(..., description="Anchor type")


class HealthCheck(BaseModel):
    """Health check item model."""

    name: str = Field(..., description="Check name")
    status: str = Field(..., description="Check status", pattern="^(pass|fail|warn)$")
    detail: Optional[str] = Field(None, description="Optional human-readable detail")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status", pattern="^(healthy|degraded|unhealthy)$")
    checks: List[HealthCheck] = Field(..., description="List of health checks", min_items=1)


class ConfigResponse(BaseModel):
    """Configuration response model."""

    key_rotation_schedule: str = Field(..., description="ISO-8601 duration (e.g. P90D)")
    rotation_grace_period: str = Field(..., description="ISO-8601 duration (e.g. P7D)")
    allowed_algorithms: List[str] = Field(..., description="List of allowed algorithms")
    max_usage_per_day_default: int = Field(..., description="Default maximum usage per day", ge=1)
    dual_authorization_required_operations: List[str] = Field(
        ...,
        description="List of operations requiring dual authorization"
    )


class ErrorDetail(BaseModel):
    """Error detail model for error envelope per KMS spec."""

    code: str = Field(
        ...,
        description="Error code",
        pattern="^(INVALID_REQUEST|UNAUTHENTICATED|UNAUTHORIZED|KEY_NOT_FOUND|KEY_REVOKED|KEY_INACTIVE|POLICY_VIOLATION|RATE_LIMITED|DEPENDENCY_UNAVAILABLE|INTERNAL_ERROR)$"
    )
    message: str = Field(..., description="Error message", min_length=1)
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    retryable: bool = Field(..., description="Whether the error is retryable")


class ErrorResponse(BaseModel):
    """Error response envelope model per KMS spec."""

    error: ErrorDetail = Field(..., description="Error information")


# Internal Models

class AccessPolicy(BaseModel):
    """Access policy model for key metadata."""

    allowed_modules: List[str] = Field(..., description="List of allowed module IDs", min_items=1)
    requires_approval: bool = Field(..., description="Whether approval is required")
    max_usage_per_day: int = Field(..., description="Maximum usage per day", ge=1)


class KeyMetadata(BaseModel):
    """Key metadata model per KMS spec Data Schemas section."""

    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    key_id: str = Field(..., description="Key identifier")
    key_type: str = Field(..., description="Key type", pattern="^(RSA-2048|Ed25519|AES-256)$")
    key_usage: List[str] = Field(..., description="List of key usage types", min_items=1)
    public_key: str = Field(..., description="PEM-encoded public key")
    key_state: str = Field(
        ...,
        description="Key state",
        pattern="^(active|pending_rotation|archived|destroyed)$"
    )
    created_at: datetime = Field(..., description="Creation timestamp (ISO 8601)")
    valid_from: datetime = Field(..., description="Valid from timestamp (ISO 8601)")
    valid_until: datetime = Field(..., description="Valid until timestamp (ISO 8601)")
    rotation_count: int = Field(..., description="Number of rotations", ge=0)
    access_policy: AccessPolicy = Field(..., description="Access policy")


class KMSContext(BaseModel):
    """KMS context model for cryptographic operation receipts."""

    key_id: str = Field(..., description="Key identifier")
    operation_type: str = Field(
        ...,
        description="Operation type",
        pattern="^(generate|sign|verify|encrypt|decrypt)$"
    )
    algorithm: str = Field(..., description="Algorithm used")
    key_size_bits: int = Field(..., description="Key size in bits", ge=1)
    success: bool = Field(..., description="Whether operation succeeded")
    error_code: Optional[str] = Field(None, description="Error code if operation failed")


class CryptographicOperationReceipt(BaseModel):
    """Cryptographic operation receipt model per KMS spec Data Schemas section."""

    receipt_id: str = Field(..., description="Receipt identifier (UUID)")
    ts: datetime = Field(..., description="Timestamp (ISO 8601)")
    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    module: str = Field(default="KMS", description="Module identifier")
    operation: str = Field(
        ...,
        description="Operation type",
        pattern="^(key_generated|key_rotated|key_revoked|signature_created|signature_verified|encrypt|decrypt|trust_anchor_updated)$"
    )
    kms_context: KMSContext = Field(..., description="KMS operation context")
    requesting_module: str = Field(..., description="Requesting module ID")
    signature: Optional[str] = Field(None, description="Ed25519 signature")


# Event Models

class EventEnvelope(BaseModel):
    """Common event envelope model per KMS spec Event Schemas section."""

    event_id: str = Field(..., description="Event identifier (UUID)")
    event_type: str = Field(
        ...,
        description="Event type",
        pattern="^(key_generated|key_rotated|key_revoked|signature_created|signature_verified|trust_anchor_updated)$"
    )
    ts: datetime = Field(..., description="Timestamp (ISO 8601)")
    tenant_id: str = Field(..., description="Tenant identifier")
    environment: str = Field(..., description="Environment", pattern="^(dev|staging|prod)$")
    plane: str = Field(..., description="Plane", pattern="^(laptop|tenant|product|shared)$")
    source_module: str = Field(default="M33", description="Source module ID")
    payload: Dict[str, Any] = Field(..., description="Event-specific payload")


class KeyGeneratedPayload(BaseModel):
    """Payload model for key_generated event."""

    key_id: str = Field(..., description="Key identifier")
    key_type: str = Field(..., description="Key type", pattern="^(RSA-2048|Ed25519|AES-256)$")
    key_usage: List[str] = Field(..., description="List of key usage types")
    key_state: str = Field(..., description="Key state", pattern="^(active|pending_rotation|archived|destroyed)$")


class KeyRotatedPayload(BaseModel):
    """Payload model for key_rotated event."""

    old_key_id: str = Field(..., description="Old key identifier")
    new_key_id: str = Field(..., description="New key identifier")
    rotation_ts: datetime = Field(..., description="Rotation timestamp (ISO 8601)")


class KeyRevokedPayload(BaseModel):
    """Payload model for key_revoked event."""

    key_id: str = Field(..., description="Key identifier")
    revocation_reason: str = Field(
        ...,
        description="Revocation reason",
        pattern="^(compromised|retired|policy_violation)$"
    )
    revoked_at: datetime = Field(..., description="Revocation timestamp (ISO 8601)")


class SignatureCreatedPayload(BaseModel):
    """Payload model for signature_created event."""

    key_id: str = Field(..., description="Key identifier")
    operation_id: str = Field(..., description="Operation identifier (UUID)")
    algorithm: str = Field(..., description="Algorithm used", pattern="^(RS256|EdDSA)$")


class SignatureVerifiedPayload(BaseModel):
    """Payload model for signature_verified event."""

    key_id: str = Field(..., description="Key identifier")
    operation_id: str = Field(..., description="Operation identifier (UUID)")
    valid: bool = Field(..., description="Whether signature is valid")


class TrustAnchorUpdatedPayload(BaseModel):
    """Payload model for trust_anchor_updated event."""

    trust_anchor_id: str = Field(..., description="Trust anchor identifier")
    anchor_type: str = Field(
        ...,
        description="Anchor type",
        pattern="^(internal_ca|external_ca|root)$"
    )
    version: str = Field(..., description="Anchor version")
