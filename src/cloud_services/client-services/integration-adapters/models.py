"""
Pydantic domain models for Integration Adapters Module (M10).

What: Request/response models for API endpoints and internal operations
Why: Type safety, validation, and standardized data contracts per PRD
Reads/Writes: Request/response validation, no file I/O
Contracts: PRD Section 11 (APIs & Integration Contracts)
Risks: Model validation failures may expose internal error details if not handled properly
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

# Import SignalEnvelope from PM-3 if available, otherwise define locally
try:
    from signal_ingestion_normalization.models import SignalEnvelope, Resource, SignalKind, Environment
except ImportError:
    # Fallback: Define minimal SignalEnvelope structure
    from typing import Literal
    SignalKind = Literal["event", "metric", "log", "trace"]
    Environment = Literal["dev", "stage", "prod"]


# ============================================================================
# Enums
# ============================================================================

class ProviderCategory(str, Enum):
    """Provider category enumeration per FR-1."""
    SCM = "SCM"
    ISSUE_TRACKER = "issue_tracker"
    CHAT = "chat"
    CI_CD = "ci_cd"
    OBSERVABILITY = "observability"
    KNOWLEDGE = "knowledge"


class ProviderStatus(str, Enum):
    """Provider status enumeration per FR-1."""
    ALPHA = "alpha"
    BETA = "beta"
    GA = "GA"
    DEPRECATED = "deprecated"


class ConnectionStatus(str, Enum):
    """Connection status enumeration per FR-2."""
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ERROR = "error"
    DELETED = "deleted"


class WebhookStatus(str, Enum):
    """Webhook registration status."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class ActionStatus(str, Enum):
    """Normalised action status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Pydantic model configuration
# ---------------------------------------------------------------------------
BaseModel.model_config = ConfigDict(extra="ignore")


# ============================================================================
# Provider Models
# ============================================================================

class IntegrationProviderCreate(BaseModel):
    """Request model for creating an integration provider."""
    provider_id: str = Field(..., description="Provider identifier (e.g., github, jira)")
    category: ProviderCategory = Field(..., description="Provider category")
    name: str = Field(..., description="Provider display name")
    status: ProviderStatus = Field(default=ProviderStatus.ALPHA, description="Provider status")
    capabilities: Dict[str, bool] = Field(default_factory=dict, description="Capability flags")
    api_version: Optional[str] = Field(None, description="API version")


class IntegrationProviderResponse(BaseModel):
    """Response model for integration provider."""
    provider_id: str
    category: ProviderCategory
    name: str
    status: ProviderStatus
    capabilities: Dict[str, bool]
    api_version: Optional[str]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Connection Models
# ============================================================================

class IntegrationConnectionCreate(BaseModel):
    """Request model for creating an integration connection."""
    provider_id: str = Field(..., description="Provider identifier")
    display_name: str = Field(..., description="Connection display name")
    auth_ref: str = Field(..., description="Reference to KMS secret (KID/secret_id)")
    enabled_capabilities: Dict[str, bool] = Field(default_factory=dict, description="Enabled capabilities")
    metadata_tags: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags")


class IntegrationConnectionUpdate(BaseModel):
    """Request model for updating an integration connection."""
    display_name: Optional[str] = Field(None, description="Connection display name")
    status: Optional[ConnectionStatus] = Field(None, description="Connection status")
    enabled_capabilities: Optional[Dict[str, bool]] = Field(None, description="Enabled capabilities")
    metadata_tags: Optional[Dict[str, Any]] = Field(None, description="Metadata tags")


class IntegrationConnectionResponse(BaseModel):
    """Response model for integration connection."""
    connection_id: UUID
    tenant_id: str
    provider_id: str
    display_name: str
    status: ConnectionStatus
    enabled_capabilities: Dict[str, bool]
    metadata_tags: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_verified_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Webhook Models
# ============================================================================

class WebhookRegistrationCreate(BaseModel):
    """Request model for creating a webhook registration."""
    connection_id: UUID = Field(..., description="Connection ID")
    public_url: str = Field(..., description="Public webhook URL")
    secret_ref: str = Field(..., description="Reference to KMS signing secret")
    events_subscribed: List[str] = Field(default_factory=list, description="List of event types")


class WebhookRegistrationResponse(BaseModel):
    """Response model for webhook registration."""
    registration_id: UUID
    connection_id: UUID
    public_url: str
    events_subscribed: List[str]
    status: WebhookStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Polling Models
# ============================================================================

class PollingCursorCreate(BaseModel):
    """Request model for creating a polling cursor."""
    connection_id: UUID = Field(..., description="Connection ID")
    cursor_position: Optional[str] = Field(None, description="Cursor position (e.g., last event id/timestamp)")


class PollingCursorUpdate(BaseModel):
    """Request model for updating a polling cursor."""
    cursor_position: Optional[str] = Field(None, description="Cursor position")
    last_polled_at: Optional[datetime] = Field(None, description="Last polled timestamp")


class PollingCursorResponse(BaseModel):
    """Response model for polling cursor."""
    cursor_id: UUID
    connection_id: UUID
    cursor_position: Optional[str]
    last_polled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Action Models
# ============================================================================

class NormalisedActionCreate(BaseModel):
    """Request model for creating a normalised action."""
    provider_id: str = Field(..., description="Provider identifier")
    connection_id: UUID = Field(..., description="Connection ID")
    canonical_type: str = Field(..., description="Canonical action type (e.g., post_chat_message)")
    target: Dict[str, Any] = Field(..., description="Target (channel, issue_key, pr_id, etc.)")
    payload: Dict[str, Any] = Field(..., description="Structured action data")
    idempotency_key: str = Field(..., description="Idempotency key for safe retries")
    correlation_id: Optional[str] = Field(None, description="Link back to MMM/Detection/UBI DecisionReceipt")


class NormalisedActionResponse(BaseModel):
    """Response model for normalised action."""
    action_id: UUID
    tenant_id: str
    provider_id: str
    connection_id: UUID
    canonical_type: str
    target: Dict[str, Any]
    payload: Dict[str, Any]
    idempotency_key: str
    correlation_id: Optional[str]
    status: ActionStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Webhook Payload Models
# ============================================================================

class WebhookPayload(BaseModel):
    """Generic webhook payload model."""
    payload: Dict[str, Any] = Field(..., description="Provider-specific webhook payload")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response format per PRD Section 11."""
    error: Dict[str, Any] = Field(
        ...,
        description="Error details",
        json_schema_extra={
            "code": "ERROR_CODE",
            "message": "Human-readable error message",
            "details": {},
            "timestamp": "2025-01-01T00:00:00Z"
        }
    )


# ============================================================================
# Health Check Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ConnectionHealthResponse(BaseModel):
    """Connection health response."""
    connection_id: UUID
    status: ConnectionStatus
    last_successful_call: Optional[datetime]
    error_count: int = Field(default=0, description="Error count")
    rate_limit_state: Optional[Dict[str, Any]] = Field(None, description="Rate limit state")
