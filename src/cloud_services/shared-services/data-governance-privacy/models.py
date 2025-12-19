"""
Pydantic models for Data Governance & Privacy Module (M22) API contracts.

Mapped directly from PRD OpenAPI specification (lines 448-631) plus supporting
schemas for lineage, retention, and compliance operations.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
# Common Models
# --------------------------------------------------------------------------- #


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsSnapshot(BaseModel):
    classification: Dict[str, Any]
    consent_p95_ms: float
    privacy_p95_ms: float
    lineage_p95_ms: float


class MetricsResponse(BaseModel):
    metrics: MetricsSnapshot


class ConfigResponse(BaseModel):
    module_id: str = "EPC-2"
    version: str = "1.0.0"
    api_endpoints: Dict[str, str]
    performance_requirements: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    retriable: bool = False
    tenant_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #


class ClassificationRequest(BaseModel):
    data_location: str = Field(..., description="URI or logical location of the data")
    data_content: Dict[str, Any] = Field(..., description="Data content to classify")
    context: Dict[str, Any] = Field(..., description="Processing context")
    classification_hints: Optional[List[str]] = Field(default=None)
    tenant_id: str = Field(..., description="Tenant identifier")


class ClassificationResponse(BaseModel):
    classification_level: str
    sensitivity_tags: List[str]
    confidence: float = Field(..., ge=0.0, le=1.0)
    classification_id: str
    data_id: str
    review_required: bool
    performance: Dict[str, Any]

    @field_validator("classification_level")
    @classmethod
    def validate_level(cls, value: str) -> str:
        allowed = {"public", "internal", "confidential", "restricted"}
        if value not in allowed:
            raise ValueError(f"classification_level must be one of {allowed}")
        return value


# --------------------------------------------------------------------------- #
# Consent
# --------------------------------------------------------------------------- #


class ConsentCheckRequest(BaseModel):
    tenant_id: str
    data_subject_id: str
    purpose: str
    data_categories: List[str]
    legal_basis: Optional[str] = Field(
        default=None,
        description="Requested legal basis (consent, legitimate_interest, etc.)",
    )


class ConsentCheckResponse(BaseModel):
    allowed: bool
    consent_id: Optional[str]
    legal_basis: Optional[str]
    restrictions: List[str] = Field(default_factory=list)
    latency_ms: float
    p95_ms: float


# --------------------------------------------------------------------------- #
# Privacy Enforcement / Compliance
# --------------------------------------------------------------------------- #


class PrivacyEnforcementRequest(BaseModel):
    tenant_id: str
    user_id: str
    action: str
    resource: str
    policy_id: str
    context: Dict[str, Any]
    classification_record: Optional[Dict[str, Any]]
    consent_result: Optional[ConsentCheckResponse]
    override_token: Optional[str]


class PrivacyEnforcementResponse(BaseModel):
    allowed: bool
    violations: List[str]
    iam_reason: str
    policy_evidence: Dict[str, Any]
    receipt_id: str
    latency_ms: float
    p95_ms: float


# --------------------------------------------------------------------------- #
# Lineage
# --------------------------------------------------------------------------- #


class LineageRecord(BaseModel):
    tenant_id: str
    source_data_id: str
    target_data_id: str
    transformation_type: str
    transformation_details: Optional[Dict[str, Any]] = None
    processed_by: str
    system_component: str


class LineageQueryResponse(BaseModel):
    entries: List[Dict[str, Any]]
    latency_ms: float
    p95_ms: float


# --------------------------------------------------------------------------- #
# Retention
# --------------------------------------------------------------------------- #


class RetentionEvaluationRequest(BaseModel):
    tenant_id: str
    data_category: str
    last_activity_months: int = Field(..., ge=0)


class RetentionEvaluationResponse(BaseModel):
    action: str
    policy_id: Optional[str]
    legal_hold: Optional[bool]
    regulatory_basis: Optional[str]


# --------------------------------------------------------------------------- #
# Rights Requests
# --------------------------------------------------------------------------- #


class RightType(str, Enum):
    access = "access"
    rectification = "rectification"
    erasure = "erasure"
    restriction = "restriction"
    portability = "portability"
    objection = "objection"


class RightsRequest(BaseModel):
    tenant_id: str
    data_subject_id: str
    right_type: RightType
    verification_data: Dict[str, Any]
    additional_info: Optional[str]


class RightsResponse(BaseModel):
    request_id: str
    estimated_completion: datetime
    next_steps: List[str]
