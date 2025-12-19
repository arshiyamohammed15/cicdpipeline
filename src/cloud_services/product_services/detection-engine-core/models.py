"""
Domain models for Detection Engine Core Module (PM-4).

What: Pydantic models for decision requests, responses, receipts, and related data structures
Why: Type safety, validation, and standardized data contracts per PRD v1.0
Reads/Writes: Request/response validation, no file I/O
Contracts: PRD §3.2, §3.7, Trust_as_a_Capability_V_0_1.md TR-1.2.1
Risks: Model validation failures may expose internal error details if not handled properly
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class DecisionStatus(str, Enum):
    """Decision status enumeration per PRD §3.2 and GSMD receipts_schema."""
    PASS = "pass"
    WARN = "warn"
    SOFT_BLOCK = "soft_block"
    HARD_BLOCK = "hard_block"


class EvaluationPoint(str, Enum):
    """Evaluation point enumeration per PRD §3.1."""
    PRE_COMMIT = "pre-commit"
    PRE_MERGE = "pre-merge"
    PRE_DEPLOY = "pre-deploy"
    POST_DEPLOY = "post-deploy"


class ActorType(str, Enum):
    """Actor type enumeration per Trust TR-6.2.1."""
    HUMAN = "human"
    AI = "ai"
    AUTOMATED = "automated"


class DataCategory(str, Enum):
    """Data category enumeration per Trust TR-4.4.1."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class Surface(str, Enum):
    """Surface enumeration per Trust TR-1.2.3."""
    IDE = "ide"
    PR = "pr"
    CI = "ci"


# ============================================================================
# Evidence Handle Model
# ============================================================================

class EvidenceHandle(BaseModel):
    """Evidence handle model per DecisionReceipt interface."""
    url: str = Field(..., description="Evidence URL")
    type: str = Field(..., description="Evidence type")
    description: str = Field(..., description="Evidence description")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp (ISO 8601)")


# ============================================================================
# Decision Receipt Model (TR-1.2.1)
# ============================================================================

class DecisionReceiptModel(BaseModel):
    """Decision Receipt model per Trust TR-1.2.1 and PRD §3.2."""
    receipt_id: str = Field(..., description="Unique receipt identifier (UUID)")
    gate_id: str = Field(..., description="Gate identifier (e.g., 'detection-engine-core', 'pre-commit-gate')")
    policy_version_ids: List[str] = Field(..., description="Array of policy version IDs evaluated")
    snapshot_hash: str = Field(..., description="SHA256 hash of policy snapshot (format: 'sha256:hex')")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")
    timestamp_monotonic_ms: int = Field(..., description="Hardware monotonic timestamp in milliseconds")
    evaluation_point: EvaluationPoint = Field(..., description="Evaluation point")
    inputs: Dict[str, Any] = Field(..., description="Input signals (metadata only, no raw code/secrets)")
    decision: Dict[str, Any] = Field(..., description="Decision object with status, rationale, badges")
    evidence_handles: List[EvidenceHandle] = Field(default_factory=list, description="Array of evidence references")
    actor: Dict[str, Any] = Field(..., description="Actor information")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")
    override: Optional[Dict[str, Any]] = Field(None, description="Optional override information")
    data_category: Optional[DataCategory] = Field(None, description="Data classification")
    degraded: bool = Field(False, description="Degraded mode flag")
    signature: str = Field(..., description="Cryptographic signature")


# ============================================================================
# Decision Request/Response Models
# ============================================================================

class DecisionRequest(BaseModel):
    """Request model for decision evaluation."""
    evaluation_point: EvaluationPoint = Field(..., description="Evaluation point")
    inputs: Dict[str, Any] = Field(..., description="Input signals (metadata only)")
    actor: Dict[str, Any] = Field(..., description="Actor information")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context information")
    policy_version_ids: Optional[List[str]] = Field(None, description="Policy version IDs to evaluate")


class DecisionResponse(BaseModel):
    """Response model for decision evaluation per PRD §3.7."""
    receipt: DecisionReceiptModel = Field(..., description="Decision receipt")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level (0.0-1.0)")
    accuracy_metrics: Optional[Dict[str, float]] = Field(None, description="Accuracy metrics (precision, recall, F1, etc.)")


class DecisionResponseError(BaseModel):
    """Error response model for decision evaluation."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    degraded: bool = Field(False, description="Degraded mode flag")


# ============================================================================
# Feedback Receipt Model
# ============================================================================

class FeedbackReceiptModel(BaseModel):
    """Feedback receipt model per PRD §3.6."""
    feedback_id: str = Field(..., description="Unique identifier for the feedback receipt")
    decision_receipt_id: str = Field(..., description="ID of the decision receipt this feedback relates to")
    pattern_id: Literal["FB-01", "FB-02", "FB-03", "FB-04"] = Field(..., description="Feedback pattern identifier")
    choice: Literal["worked", "partly", "didnt"] = Field(..., description="User choice indicating feedback outcome")
    tags: List[str] = Field(default_factory=list, description="Optional tags for categorizing feedback")
    actor: Dict[str, Any] = Field(..., description="Actor information")
    timestamp_utc: str = Field(..., description="UTC timestamp when feedback was generated (ISO 8601)")
    signature: str = Field(..., description="Cryptographic signature of the receipt")


class FeedbackRequest(BaseModel):
    """Request model for feedback submission."""
    decision_receipt_id: str = Field(..., description="ID of the decision receipt")
    pattern_id: Literal["FB-01", "FB-02", "FB-03", "FB-04"] = Field(..., description="Feedback pattern identifier")
    choice: Literal["worked", "partly", "didnt"] = Field(..., description="User choice")
    tags: List[str] = Field(default_factory=list, description="Optional tags")
    actor: Dict[str, Any] = Field(..., description="Actor information")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission."""
    feedback_id: str = Field(..., description="Feedback receipt ID")
    status: str = Field(..., description="Status (e.g., 'accepted')")
    message: Optional[str] = Field(None, description="Status message")


# ============================================================================
# Evidence Link Model
# ============================================================================

class EvidenceLink(BaseModel):
    """Evidence link model per PRD §3.7."""
    type: str = Field(..., description="Evidence type")
    href: str = Field(..., description="Evidence URL")
    label: str = Field(..., description="Evidence label/description")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp (ISO 8601)")


# ============================================================================
# Health Check Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    ready: bool = Field(..., description="Ready status")
    checks: Dict[str, bool] = Field(..., description="Individual readiness checks")
    timestamp: Optional[datetime] = Field(None, description="Check timestamp")

