"""
Pydantic models for Configuration & Policy Management service.

What: Defines Pydantic v2 models for request/response validation per PRD v1.1.0
Why: Ensures type safety, input validation, and standardized API contracts
Reads/Writes: Reads request data, writes response data (no file I/O)
Contracts: Policy API contract (8 endpoints), receipt schemas per PRD
Risks: Model validation failures may expose internal error details if not handled properly
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


# ============================================================================
# Health & Metrics Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status", pattern="^(healthy|degraded|unhealthy)$")
    version: str = Field(..., description="Module version")
    timestamp: str = Field(..., description="Health check timestamp (ISO 8601)")


class MetricsResponse(BaseModel):
    """Metrics snapshot response model."""

    metrics: List[Dict[str, Any]] = Field(..., description="Runtime metrics array")


class ConfigResponse(BaseModel):
    """Module configuration response model."""

    module_id: str = Field(..., description="Module identifier (e.g., M23 for EPC-3)")
    module_name: str = Field(..., description="Human-readable module name")
    version: str = Field(..., description="Module semantic version")
    config: Dict[str, Any] = Field(..., description="Effective module configuration")
    timestamp: str = Field(..., description="Config timestamp (ISO 8601)")


# ============================================================================
# Policy Models
# ============================================================================

class CreatePolicyRequest(BaseModel):
    """Request model for creating a policy (PRD lines 337-355)."""

    name: str = Field(..., description="Policy name", min_length=1, max_length=255)
    policy_type: str = Field(
        ...,
        description="Policy type",
        pattern="^(security|compliance|operational|governance)$"
    )
    policy_definition: Dict[str, Any] = Field(..., description="Policy definition (JSONB)")
    scope: Dict[str, Any] = Field(..., description="Policy scope (JSONB)")
    enforcement_level: Optional[str] = Field(
        default="advisory",
        description="Enforcement level",
        pattern="^(advisory|warning|enforcement)$"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata (JSONB)")
    description: Optional[str] = Field(default=None, description="Policy description")


class PolicyResponse(BaseModel):
    """Response model for policy operations (PRD lines 356-366)."""

    policy_id: str = Field(..., description="Policy identifier (UUID)")
    version: str = Field(..., description="Policy version (semver)")
    status: str = Field(
        ...,
        description="Policy status",
        pattern="^(draft|review|approved|active|deprecated)$"
    )


class EvaluatePolicyRequest(BaseModel):
    """Request model for policy evaluation (PRD lines 368-389)."""

    context: Dict[str, Any] = Field(..., description="Evaluation context")
    principal: Optional[Dict[str, Any]] = Field(default=None, description="Principal information")
    resource: Optional[Dict[str, Any]] = Field(default=None, description="Resource information")
    action: Optional[str] = Field(default=None, description="Action to evaluate")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier (UUID)")
    environment: Optional[str] = Field(
        default=None,
        description="Environment",
        pattern="^(production|staging|development)$"
    )


class ViolationDetail(BaseModel):
    """Violation detail model."""

    rule_id: str = Field(..., description="Rule identifier")
    policy_id: str = Field(..., description="Policy identifier (UUID)")
    violation_type: str = Field(..., description="Violation type")
    severity: str = Field(..., description="Violation severity", pattern="^(high|medium|low)$")


class EvaluatePolicyResponse(BaseModel):
    """Response model for policy evaluation (PRD lines 390-400)."""

    decision: str = Field(..., description="Evaluation decision", pattern="^(allow|deny|transform)$")
    reason: str = Field(..., description="Decision reason")
    violations: List[ViolationDetail] = Field(default_factory=list, description="List of violations")
    cached: Optional[bool] = Field(default=False, description="Whether result was cached")
    evaluation_time_ms: Optional[float] = Field(default=None, description="Evaluation time in milliseconds")


# ============================================================================
# Configuration Models
# ============================================================================

class CreateConfigurationRequest(BaseModel):
    """Request model for creating a configuration (PRD lines 402-421)."""

    name: str = Field(..., description="Configuration name", min_length=1, max_length=255)
    config_type: str = Field(
        ...,
        description="Configuration type",
        pattern="^(security|performance|feature|compliance)$"
    )
    config_definition: Dict[str, Any] = Field(..., description="Configuration definition (JSONB)")
    environment: str = Field(
        ...,
        description="Target environment",
        pattern="^(production|staging|development)$"
    )
    deployment_strategy: Optional[str] = Field(
        default="immediate",
        description="Deployment strategy",
        pattern="^(immediate|canary|blue_green)$"
    )
    rollback_config: Optional[Dict[str, Any]] = Field(default=None, description="Rollback configuration")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier (UUID)")


class ConfigurationResponse(BaseModel):
    """Response model for configuration operations (PRD lines 422-432)."""

    config_id: str = Field(..., description="Configuration identifier (UUID)")
    version: str = Field(..., description="Configuration version (semver)")
    status: str = Field(
        ...,
        description="Configuration status",
        pattern="^(draft|staging|active|deprecated)$"
    )


class ConfigurationDriftReport(BaseModel):
    """Configuration drift detection report."""

    drift_detected: bool = Field(..., description="Whether drift was detected")
    drift_severity: str = Field(
        ...,
        description="Drift severity",
        pattern="^(none|low|medium|high|critical)$"
    )
    drift_details: List[Dict[str, Any]] = Field(default_factory=list, description="Drift details")
    remediation_required: bool = Field(default=False, description="Whether remediation is required")


# ============================================================================
# Gold Standards Models
# ============================================================================

class ControlDefinition(BaseModel):
    """Control definition model."""

    control_id: str = Field(..., description="Control identifier")
    name: str = Field(..., description="Control name")
    description: Optional[str] = Field(default=None, description="Control description")
    severity: str = Field(..., description="Control severity", pattern="^(critical|high|medium|low)$")
    implementation_requirements: List[Dict[str, Any]] = Field(default_factory=list, description="Implementation requirements")


class GoldStandardResponse(BaseModel):
    """Response model for gold standard operations (PRD lines 434-459)."""

    standard_id: str = Field(..., description="Gold standard identifier (UUID)")
    name: str = Field(..., description="Standard name")
    framework: str = Field(..., description="Compliance framework", pattern="^(soc2|gdpr|hipaa|nist|custom)$")
    version: str = Field(..., description="Standard version")
    control_definitions: List[ControlDefinition] = Field(default_factory=list, description="Control definitions")
    compliance_rules: List[Dict[str, Any]] = Field(default_factory=list, description="Compliance rules")
    evidence_requirements: Dict[str, Any] = Field(default_factory=dict, description="Evidence requirements")


class ListGoldStandardsResponse(BaseModel):
    """Response model for listing gold standards."""

    items: List[GoldStandardResponse] = Field(default_factory=list, description="List of gold standards")


# ============================================================================
# Compliance Models
# ============================================================================

class ComplianceCheckRequest(BaseModel):
    """Request model for compliance check (PRD lines 460-487)."""

    framework: str = Field(..., description="Compliance framework", pattern="^(soc2|gdpr|hipaa|nist|custom)$")
    context: Dict[str, Any] = Field(..., description="Compliance check context")
    evidence_required: Optional[bool] = Field(default=False, description="Whether evidence is required")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier (UUID)")


class EvidenceGap(BaseModel):
    """Evidence gap model."""

    control_id: str = Field(..., description="Control identifier")
    evidence_type: str = Field(..., description="Evidence type")
    gap_description: str = Field(..., description="Gap description")


class ComplianceCheckResponse(BaseModel):
    """Response model for compliance check (PRD lines 476-487)."""

    compliant: bool = Field(..., description="Whether compliant")
    score: float = Field(..., description="Compliance score (0-100)", ge=0.0, le=100.0)
    missing_controls: List[str] = Field(default_factory=list, description="List of missing control IDs")
    evidence_gaps: List[EvidenceGap] = Field(default_factory=list, description="List of evidence gaps")
    framework: Optional[str] = Field(default=None, description="Framework name")
    controls_evaluated: Optional[int] = Field(default=None, description="Number of controls evaluated")
    controls_passing: Optional[int] = Field(default=None, description="Number of controls passing")
    controls_failing: Optional[int] = Field(default=None, description="Number of controls failing")


# ============================================================================
# Audit Models
# ============================================================================

class AuditSummaryResponse(BaseModel):
    """Response model for audit summary (PRD lines 489-500)."""

    tenant_id: str = Field(..., description="Tenant identifier (UUID)")
    summary: Dict[str, Any] = Field(..., description="Audit summary data")
    timestamp: str = Field(..., description="Summary timestamp (ISO 8601)")


# ============================================================================
# Remediation Models
# ============================================================================

class TriggerRemediationRequest(BaseModel):
    """Request model for triggering remediation."""

    target_type: str = Field(
        ...,
        description="Target type",
        pattern="^(policy|configuration|compliance_violation)$"
    )
    target_id: str = Field(..., description="Target identifier (UUID)")
    reason: str = Field(..., description="Remediation reason", min_length=1)
    remediation_type: str = Field(
        ...,
        description="Remediation type",
        pattern="^(automatic|manual|rollback)$"
    )


class RemediationResponse(BaseModel):
    """Response model for remediation operations."""

    remediation_id: str = Field(..., description="Remediation identifier (UUID)")
    status: str = Field(
        ...,
        description="Remediation status",
        pattern="^(pending|in_progress|completed|failed)$"
    )
    target_type: str = Field(..., description="Target type")
    target_id: str = Field(..., description="Target identifier (UUID)")
    remediation_time_ms: Optional[float] = Field(default=None, description="Remediation time in milliseconds")


# ============================================================================
# Error Models
# ============================================================================

class ErrorDetail(BaseModel):
    """Error detail model per PRD error schema."""

    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message", min_length=1)
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    correlation_id: str = Field(..., description="Correlation identifier (UUID)")
    retriable: bool = Field(default=False, description="Whether the error is retryable")
    tenant_id: Optional[str] = Field(default=None, description="Tenant identifier (UUID)")


class ErrorResponse(BaseModel):
    """Error response model per PRD error schema."""

    error: ErrorDetail = Field(..., description="Error information")


# ============================================================================
# Receipt Models (for internal use)
# ============================================================================

class EvidenceHandle(BaseModel):
    """Evidence handle model for receipts."""

    url: str = Field(..., description="Evidence URL")
    type: str = Field(..., description="Evidence type")
    description: str = Field(..., description="Evidence description")
    expires_at: Optional[str] = Field(default=None, description="Expiration timestamp (ISO 8601)")


class Actor(BaseModel):
    """Actor model for receipts."""

    repo_id: str = Field(..., description="Repository identifier")
    user_id: str = Field(..., description="User identifier (UUID)")
    machine_fingerprint: str = Field(..., description="Machine fingerprint")


class PolicyLifecycleReceipt(BaseModel):
    """Policy lifecycle receipt model (PRD lines 657-699)."""

    receipt_id: str = Field(..., description="Receipt identifier (UUID)")
    gate_id: str = Field(default="policy-management", description="Gate identifier")
    policy_version_ids: List[str] = Field(default_factory=list, description="Policy version IDs")
    snapshot_hash: str = Field(..., description="Snapshot hash (sha256:hex)")
    timestamp_utc: str = Field(..., description="Timestamp UTC (ISO 8601)")
    timestamp_monotonic_ms: float = Field(..., description="Monotonic timestamp in milliseconds")
    inputs: Dict[str, Any] = Field(..., description="Input data")
    decision: Dict[str, Any] = Field(..., description="Decision data")
    result: Dict[str, Any] = Field(..., description="Result data")
    evidence_handles: List[EvidenceHandle] = Field(default_factory=list, description="Evidence handles")
    actor: Actor = Field(..., description="Actor information")
    degraded: bool = Field(default=False, description="Degraded mode flag")
    signature: str = Field(..., description="Receipt signature")


class ConfigurationChangeReceipt(BaseModel):
    """Configuration change receipt model (PRD lines 701-745)."""

    receipt_id: str = Field(..., description="Receipt identifier (UUID)")
    gate_id: str = Field(default="configuration-management", description="Gate identifier")
    policy_version_ids: List[str] = Field(default_factory=list, description="Policy version IDs")
    snapshot_hash: str = Field(..., description="Snapshot hash (sha256:hex)")
    timestamp_utc: str = Field(..., description="Timestamp UTC (ISO 8601)")
    timestamp_monotonic_ms: float = Field(..., description="Monotonic timestamp in milliseconds")
    inputs: Dict[str, Any] = Field(..., description="Input data")
    decision: Dict[str, Any] = Field(..., description="Decision data")
    result: Dict[str, Any] = Field(..., description="Result data")
    evidence_handles: List[EvidenceHandle] = Field(default_factory=list, description="Evidence handles")
    actor: Actor = Field(..., description="Actor information")
    degraded: bool = Field(default=False, description="Degraded mode flag")
    signature: str = Field(..., description="Receipt signature")


class PolicyEvaluationDecisionReceipt(BaseModel):
    """Policy evaluation decision receipt model (PRD lines 747-803)."""

    receipt_id: str = Field(..., description="Receipt identifier (UUID)")
    gate_id: str = Field(default="policy-evaluation", description="Gate identifier")
    policy_version_ids: List[str] = Field(default_factory=list, description="Policy version IDs")
    snapshot_hash: str = Field(..., description="Snapshot hash (sha256:hex)")
    timestamp_utc: str = Field(..., description="Timestamp UTC (ISO 8601)")
    timestamp_monotonic_ms: float = Field(..., description="Monotonic timestamp in milliseconds")
    inputs: Dict[str, Any] = Field(..., description="Input data")
    decision: Dict[str, Any] = Field(..., description="Decision data")
    result: Dict[str, Any] = Field(..., description="Result data")
    evidence_handles: List[EvidenceHandle] = Field(default_factory=list, description="Evidence handles")
    actor: Actor = Field(..., description="Actor information")
    degraded: bool = Field(default=False, description="Degraded mode flag")
    signature: str = Field(..., description="Receipt signature")


class ComplianceCheckReceipt(BaseModel):
    """Compliance check receipt model (PRD lines 805-860)."""

    receipt_id: str = Field(..., description="Receipt identifier (UUID)")
    gate_id: str = Field(default="compliance-check", description="Gate identifier")
    policy_version_ids: List[str] = Field(default_factory=list, description="Policy version IDs")
    snapshot_hash: str = Field(..., description="Snapshot hash (sha256:hex)")
    timestamp_utc: str = Field(..., description="Timestamp UTC (ISO 8601)")
    timestamp_monotonic_ms: float = Field(..., description="Monotonic timestamp in milliseconds")
    inputs: Dict[str, Any] = Field(..., description="Input data")
    decision: Dict[str, Any] = Field(..., description="Decision data")
    result: Dict[str, Any] = Field(..., description="Result data")
    evidence_handles: List[EvidenceHandle] = Field(default_factory=list, description="Evidence handles")
    actor: Actor = Field(..., description="Actor information")
    degraded: bool = Field(default=False, description="Degraded mode flag")
    signature: str = Field(..., description="Receipt signature")


class RemediationActionReceipt(BaseModel):
    """Remediation action receipt model (PRD lines 862-904)."""

    receipt_id: str = Field(..., description="Receipt identifier (UUID)")
    gate_id: str = Field(default="remediation", description="Gate identifier")
    policy_version_ids: List[str] = Field(default_factory=list, description="Policy version IDs")
    snapshot_hash: str = Field(..., description="Snapshot hash (sha256:hex)")
    timestamp_utc: str = Field(..., description="Timestamp UTC (ISO 8601)")
    timestamp_monotonic_ms: float = Field(..., description="Monotonic timestamp in milliseconds")
    inputs: Dict[str, Any] = Field(..., description="Input data")
    decision: Dict[str, Any] = Field(..., description="Decision data")
    result: Dict[str, Any] = Field(..., description="Result data")
    evidence_handles: List[EvidenceHandle] = Field(default_factory=list, description="Evidence handles")
    actor: Actor = Field(..., description="Actor information")
    degraded: bool = Field(default=False, description="Degraded mode flag")
    signature: str = Field(..., description="Receipt signature")
