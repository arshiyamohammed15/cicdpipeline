"""
Pydantic models for Identity & Access Management (IAM) service.

What: Defines Pydantic v2 models for request/response validation per IAM spec v1.1.0
Why: Ensures type safety, input validation, and standardized API contracts
Reads/Writes: Reads request data, writes response data (no file I/O)
Contracts: IAM API contract (verify, decision, policies endpoints), IPC protocol error envelope
Risks: Model validation failures may expose internal error details if not handled properly
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class VerifyRequest(BaseModel):
    """Request model for token verification."""

    token: str = Field(..., description="JWT token to verify", min_length=1)


class VerifyResponse(BaseModel):
    """Response model for token verification."""

    sub: str = Field(..., description="Subject identifier")
    scope: List[str] = Field(..., description="List of granted scopes")
    valid_until: datetime = Field(..., description="Token expiration time (ISO 8601)")


class Subject(BaseModel):
    """Subject model for access decision requests."""

    sub: str = Field(..., description="Subject identifier")
    roles: List[str] = Field(
        ...,
        description="List of roles",
        min_items=1
    )
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional subject attributes"
    )


class DecisionContext(BaseModel):
    """Context model for access decision requests."""

    time: Optional[datetime] = Field(
        default=None,
        description="Request time (ISO 8601)"
    )
    device_posture: Optional[str] = Field(
        default=None,
        description="Device posture",
        pattern="^(secure|unknown|insecure)$"
    )
    location: Optional[str] = Field(
        default=None,
        description="Request location"
    )
    risk_score: Optional[float] = Field(
        default=None,
        description="Risk score",
        ge=0.0,
        le=1.0
    )
    crisis_mode: Optional[bool] = Field(
        default=None,
        description="Crisis mode flag for break-glass per IAM spec section 3.3"
    )


class BreakGlassRequest(BaseModel):
    """Break-glass request model per IAM spec section 3.3."""

    subject: Subject = Field(..., description="Subject requesting break-glass access")
    incident_id: str = Field(..., description="Incident identifier", min_length=1)
    justification: str = Field(..., description="Justification text (non-PII)", min_length=1)
    approver_identity: Optional[str] = Field(
        default=None,
        description="Approver identity (optional)"
    )
    resource: Optional[str] = Field(
        default=None,
        description="Resource to access (optional)"
    )


class ElevationRequest(BaseModel):
    """Elevation request model for JIT elevation."""

    request: bool = Field(..., description="Whether elevation is requested")
    scope: Optional[List[str]] = Field(
        default=None,
        description="Desired elevation scope"
    )
    duration: Optional[str] = Field(
        default=None,
        description="Desired elevation duration"
    )


class DecisionRequest(BaseModel):
    """Request model for access decision evaluation."""

    subject: Subject = Field(..., description="Subject requesting access")
    action: str = Field(..., description="Action to perform", min_length=1)
    resource: str = Field(..., description="Resource to access", min_length=1)
    context: Optional[DecisionContext] = Field(
        default=None,
        description="Request context (time, device, location, risk)"
    )
    elevation: Optional[ElevationRequest] = Field(
        default=None,
        description="JIT elevation request"
    )


class DecisionResponse(BaseModel):
    """Response model for access decision evaluation."""

    decision: str = Field(
        ...,
        description="Access decision",
        pattern="^(ALLOW|DENY|ELEVATION_REQUIRED|ELEVATION_GRANTED|BREAK_GLASS_GRANTED)$"
    )
    reason: str = Field(..., description="Decision reason", min_length=1)
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Decision expiration time (ISO 8601)"
    )
    receipt_id: str = Field(..., description="Receipt identifier (UUID)")


class PolicyRule(BaseModel):
    """Policy rule model."""

    rule_type: str = Field(..., description="Rule type")
    rule_data: Dict[str, Any] = Field(..., description="Rule data")


class Policy(BaseModel):
    """Policy model for policy bundles."""

    id: str = Field(..., description="Policy identifier", min_length=1)
    rules: List[PolicyRule] = Field(..., description="Policy rules", min_items=1)
    status: str = Field(
        ...,
        description="Policy status",
        pattern="^(draft|released|deprecated)$"
    )


class PolicyBundle(BaseModel):
    """Policy bundle model for policy management."""

    bundle_id: str = Field(..., description="Bundle identifier", min_length=1)
    version: str = Field(..., description="Bundle version", min_length=1)
    policies: List[Policy] = Field(..., description="List of policies", min_items=1)
    effective_from: Optional[datetime] = Field(
        default=None,
        description="Effective from time (ISO 8601)"
    )


class ErrorDetail(BaseModel):
    """Error detail model for error envelope per IPC protocol."""

    code: str = Field(
        ...,
        description="Error code",
        pattern="^(BAD_REQUEST|AUTH_FAILED|FORBIDDEN|CONFLICT|RATE_LIMITED|SERVER_ERROR)$"
    )
    message: str = Field(..., description="Error message", min_length=1)
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional error details"
    )


class ErrorResponse(BaseModel):
    """Error response envelope model per IPC protocol contract."""

    error: ErrorDetail = Field(..., description="Error information")


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp (ISO 8601)")


class MetricsResponse(BaseModel):
    """Metrics response model."""

    authentication_count: int = Field(..., description="Total authentication attempts", ge=0)
    decision_count: int = Field(..., description="Total access decisions", ge=0)
    policy_count: int = Field(..., description="Total policies", ge=0)
    average_auth_latency_ms: float = Field(..., description="Average auth latency (ms)", ge=0.0)
    average_decision_latency_ms: float = Field(..., description="Average decision latency (ms)", ge=0.0)
    average_policy_latency_ms: float = Field(..., description="Average policy evaluation latency (ms)", ge=0.0)
    timestamp: datetime = Field(..., description="Metrics timestamp (ISO 8601)")


class ConfigResponse(BaseModel):
    """Configuration response model."""

    module_id: str = Field(..., description="Module identifier")
    version: str = Field(..., description="Module version")
    api_endpoints: Dict[str, str] = Field(..., description="API endpoints")
    performance_requirements: Dict[str, Any] = Field(..., description="Performance requirements")
    timestamp: datetime = Field(..., description="Config timestamp (ISO 8601)")

