"""
Pydantic models aligned with the authoritative JSON schemas defined in
`contracts/schemas/*.json`. These models keep request/response contracts in sync
with FastAPI validation and enforce policy metadata requirements.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, constr


class ActorType(str, Enum):
    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"


class OperationType(str, Enum):
    CHAT = "chat"
    COMPLETION = "completion"
    EMBEDDING = "embedding"
    TOOL_SUGGEST = "tool_suggest"
    CLASSIFICATION = "classification"
    CUSTOM = "custom"


class Decision(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    TRANSFORMED = "TRANSFORMED"
    DEGRADED = "DEGRADED"


class RiskClass(str, Enum):
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    R5 = "R5"


class Severity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


class SafetyAction(str, Enum):
    BLOCK = "blocked"
    REDACT = "redacted"
    DOWNGRADE = "downgraded"
    ALERTED = "alerted"
    ROUTED_BACKUP = "routed_backup"


class SafetyCheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    DEGRADED = "degraded"
    SKIPPED = "skipped"


class Actor(BaseModel):
    actor_id: constr(min_length=3)
    actor_type: ActorType
    roles: List[constr(min_length=2)]
    capabilities: List[constr(min_length=2)]
    scopes: Optional[List[constr(min_length=2)]] = None
    session_assurance_level: Optional[str] = None
    workspace_id: Optional[str] = None


class Tenant(BaseModel):
    tenant_id: constr(min_length=3)
    region: str
    data_residency: Optional[str] = None


class ContentRef(BaseModel):
    hash: constr(min_length=8)
    location: constr(min_length=3)


class ContextSegment(BaseModel):
    segment_id: constr(min_length=4)
    segment_type: constr(min_length=3)
    label: str
    sensitivity: constr(pattern="^(public|internal|confidential|restricted)$")
    content_ref: ContentRef
    truncated: bool = False
    source: Optional[Dict[str, Any]] = None


class Budget(BaseModel):
    max_tokens: int = Field(ge=1, le=32768)
    timeout_ms: int = Field(ge=100, le=120_000)
    priority: constr(pattern="^(low|normal|high|critical)$")
    temperature: Optional[float] = Field(default=0.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tool_allowlist: Optional[List[str]] = None
    seed: Optional[int] = Field(default=None, description="Deterministic seed for LLM invocation")


class SafetyOverrides(BaseModel):
    fail_open_allowed: bool = False
    degradation_mode: constr(pattern="^(default|prefer_backup|simulation_only)$") = "default"
    risk_tolerance: constr(pattern="^(strict|balanced|permissive)$") = "strict"


class TelemetryContext(BaseModel):
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    additional_attributes: Dict[str, Any] = Field(default_factory=dict)


class MeasurableSignals(BaseModel):
    """Measurable signals for task classification per LLM Strategy Directives Section 2."""
    changed_files_count: int = Field(default=0, ge=0)
    estimated_diff_loc: int = Field(default=0, ge=0)
    rag_context_bytes: int = Field(default=0, ge=0)
    tool_calls_planned: int = Field(default=0, ge=0)
    high_stakes_flag: bool = Field(default=False, description="Release/rollback/policy/security/compliance flag")


class TaskType(str, Enum):
    """Task type classification per LLM Strategy Directives."""
    CODE = "code"
    TEXT = "text"
    RETRIEVAL = "retrieval"
    PLANNING = "planning"
    SUMMARISE = "summarise"


class Plane(str, Enum):
    """Deployment plane identifier per ADR-LLM-001."""
    IDE = "ide"
    TENANT = "tenant"
    PRODUCT = "product"
    SHARED = "shared"


class LLMRequest(BaseModel):
    request_id: constr(min_length=8, max_length=64)
    schema_version: constr(pattern="^v\\d+$") = "v1"
    actor: Actor
    tenant: Tenant
    workspace_id: Optional[str] = None
    logical_model_id: constr(min_length=3)
    operation_type: OperationType
    intended_capability: Optional[str] = None
    sensitivity_level: constr(pattern="^(low|medium|high)$")
    system_prompt_id: constr(min_length=3)
    user_prompt: constr(min_length=1)
    context_segments: List[ContextSegment] = Field(default_factory=list, max_length=50)
    policy_snapshot_id: constr(min_length=8)
    policy_version_ids: List[constr(min_length=4)]
    budget: Budget
    safety_overrides: SafetyOverrides = Field(default_factory=SafetyOverrides)
    dry_run: bool = False
    telemetry_context: Optional[TelemetryContext] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    # Optional list of logical tool/action identifiers the model proposes to
    # execute. Used by the safety pipeline to enforce FR-8 (tool/action
    # safety) via IAM capabilities and policy constraints.
    proposed_tool_calls: Optional[List[str]] = None
    # Measurable signals for task classification (LLM Strategy Directives Section 2)
    measurable_signals: Optional[MeasurableSignals] = Field(default_factory=MeasurableSignals)
    # Task type for routing (LLM Strategy Directives Section 1.2)
    task_type: Optional[TaskType] = None
    # Plane context (determined from request or configuration)
    plane: Optional[Plane] = None


class Tokens(BaseModel):
    tokens_in: int = Field(ge=0)
    tokens_out: int = Field(ge=0)
    model_cost_estimate: float = Field(ge=0.0)


class RiskFlag(BaseModel):
    risk_class: RiskClass
    severity: Severity
    actions: List[SafetyAction]


class ToolCallResult(BaseModel):
    tool_name: str
    status: constr(pattern="^(allowed|blocked|downgraded)$")
    reason: Optional[str] = None


class ResponseOutput(BaseModel):
    content: Optional[str] = None
    redacted_output_summary: Optional[str] = None
    tool_calls: Optional[List[ToolCallResult]] = None


class LLMResponse(BaseModel):
    response_id: constr(min_length=8, max_length=64)
    schema_version: constr(pattern="^v\\d+$") = "v1"
    request_id: constr(min_length=8, max_length=64)
    decision: Decision
    receipt_id: constr(min_length=8, max_length=64)
    tokens: Tokens
    output: Optional[ResponseOutput] = None
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    policy_snapshot_id: constr(min_length=8)
    policy_version_ids: List[constr(min_length=4)]
    fail_open: bool = False
    degradation_stage: Optional[str] = None
    fallback_chain: Optional[List[Dict[str, Any]]] = None
    telemetry_ids: Optional[Dict[str, str]] = None
    timestamp_utc: datetime


class DryRunDecision(BaseModel):
    decision_id: constr(min_length=8, max_length=64)
    schema_version: constr(pattern="^v\\d+$") = "v1"
    request_id: constr(min_length=8, max_length=64)
    policy_snapshot_id: constr(min_length=8)
    policy_version_ids: List[constr(min_length=4)]
    decision: constr(
        pattern="^(ALLOW|BLOCK|REQUIRE_SANITISATION|REQUIRE_REDACTION)$"
    )
    reasons: List[str]
    simulated_actions: List[Dict[str, str]]
    policy_latency_ms: int = Field(ge=0)
    timestamp_utc: datetime


class SafetyCheck(BaseModel):
    name: str
    status: SafetyCheckStatus
    score: float = Field(ge=0.0, le=1.0)
    details: Optional[str] = None
    classifier_version: Optional[str] = None


class SafetyAssessment(BaseModel):
    assessment_id: constr(min_length=8, max_length=64)
    schema_version: constr(pattern="^v\\d+$") = "v1"
    request_id: constr(min_length=8, max_length=64)
    input_checks: List[SafetyCheck]
    output_checks: List[SafetyCheck]
    risk_classes: List[RiskFlag]
    actions_taken: List[Dict[str, str]]
    metrics: Dict[str, Any]
    generated_at: datetime


class SafetyIncident(BaseModel):
    incident_id: constr(min_length=8, max_length=64)
    schema_version: constr(pattern="^v\\d+$") = "v1"
    tenant_id: str
    workspace_id: str
    actor_id: str
    risk_class: RiskClass
    severity: Severity
    status: constr(pattern="^(OPEN|ACKNOWLEDGED|CLOSED)$") = "OPEN"
    related_request_ids: List[str]
    policy_snapshot_id: str
    policy_version_ids: List[str]
    decision: Decision
    receipt_id: str
    dedupe_key: str
    correlation_hints: Dict[str, Any] = Field(default_factory=dict)
    alert_payload: Dict[str, Any]
    timestamp_utc: datetime


# Resolve postponed annotations for pydantic models that use constr with future annotations
Actor.model_rebuild(_types_namespace={"constr": constr})
SafetyIncident.model_rebuild(_types_namespace={"constr": constr})

__all__ = [
    "Actor",
    "ActorType",
    "Budget",
    "Decision",
    "DryRunDecision",
    "LLMRequest",
    "LLMResponse",
    "MeasurableSignals",
    "OperationType",
    "Plane",
    "RiskClass",
    "RiskFlag",
    "SafetyAssessment",
    "SafetyIncident",
    "SafetyOverrides",
    "SafetyCheck",
    "SafetyCheckStatus",
    "Severity",
    "TaskType",
    "Tenant",
    "Tokens",
    "SafetyAction",
]
