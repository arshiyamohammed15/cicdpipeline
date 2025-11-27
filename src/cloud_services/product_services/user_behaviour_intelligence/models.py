"""
Domain models for User Behaviour Intelligence (UBI) Module (EPC-9).

What: Pydantic models for API requests, responses, and data structures
Why: Type safety, validation, and standardized data contracts per UBI PRD v2.0
Reads/Writes: Request/response validation, no file I/O
Contracts: PRD Section 10 (Data Model), Section 11 (APIs)
Risks: Model validation failures may expose internal error details if not handled properly
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class ActorType(str, Enum):
    """Actor type enumeration per UBI PRD Section 6."""
    HUMAN = "human"
    AI_AGENT = "ai_agent"
    SERVICE = "service"


class ActorScope(str, Enum):
    """Actor scope enumeration per UBI PRD Section 10."""
    ACTOR = "actor"
    TEAM = "team"
    COHORT = "cohort"
    TENANT = "tenant"


class SignalType(str, Enum):
    """Signal type enumeration per UBI PRD Section 10.4."""
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    INFORMATIONAL = "informational"


class Severity(str, Enum):
    """Severity enumeration per UBI PRD FR-4."""
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


class SignalStatus(str, Enum):
    """Signal status enumeration per UBI PRD Section 10.4."""
    ACTIVE = "active"
    RESOLVED = "resolved"


class Dimension(str, Enum):
    """Dimension enumeration per UBI PRD FR-5."""
    ACTIVITY = "activity"
    FLOW = "flow"
    COLLABORATION = "collaboration"
    AGENT_SYNERGY = "agent_synergy"


# ============================================================================
# Data Models (per Section 10)
# ============================================================================

class BehaviouralEvent(BaseModel):
    """BehaviouralEvent model per UBI PRD Section 10.1."""
    event_id: str = Field(..., description="Event identifier (mapped from PM-3 signal_id)")
    tenant_id: str = Field(..., description="Tenant identifier")
    actor_id: Optional[str] = Field(None, description="Actor identifier")
    actor_type: ActorType = Field(..., description="Actor type")
    source_system: Optional[str] = Field(None, description="Source system (IDE, Git, CI, etc.)")
    event_type: str = Field(..., description="Canonical event type")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")
    ingested_at: str = Field(..., description="ISO 8601 ingestion timestamp")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Event properties")
    privacy_tags: Dict[str, Any] = Field(default_factory=dict, description="Privacy classification tags")
    schema_version: str = Field(..., description="Schema version")
    trace_id: Optional[str] = Field(None, description="Trace ID")
    span_id: Optional[str] = Field(None, description="Span ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    resource: Optional[Dict[str, Any]] = Field(None, description="Resource metadata")


class BehaviouralFeature(BaseModel):
    """BehaviouralFeature model per UBI PRD Section 10.2."""
    feature_id: str = Field(..., description="Feature identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    actor_scope: ActorScope = Field(..., description="Actor scope")
    actor_or_group_id: str = Field(..., description="Actor or group identifier")
    feature_name: str = Field(..., description="Feature name")
    window_start: str = Field(..., description="Window start timestamp (ISO 8601)")
    window_end: str = Field(..., description="Window end timestamp (ISO 8601)")
    value: float = Field(..., description="Feature value")
    dimension: Dimension = Field(..., description="Dimension")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Calculation metadata")


class BehaviouralBaseline(BaseModel):
    """BehaviouralBaseline model per UBI PRD Section 10.3."""
    baseline_id: str = Field(..., description="Baseline identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    actor_scope: ActorScope = Field(..., description="Actor scope")
    actor_or_group_id: str = Field(..., description="Actor or group identifier")
    feature_name: str = Field(..., description="Feature name")
    window: str = Field(..., description="Baseline window (e.g., '90d')")
    mean: float = Field(..., description="Mean value")
    std_dev: float = Field(..., description="Standard deviation")
    percentiles: Dict[str, float] = Field(default_factory=dict, description="Percentile values")
    last_recomputed_at: str = Field(..., description="Last recomputation timestamp (ISO 8601)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Baseline confidence")


class BehaviouralSignal(BaseModel):
    """BehaviouralSignal model per UBI PRD Section 10.4."""
    signal_id: str = Field(..., description="Signal identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    actor_scope: ActorScope = Field(..., description="Actor scope")
    actor_or_group_id: str = Field(..., description="Actor or group identifier")
    dimension: Dimension = Field(..., description="Dimension")
    signal_type: SignalType = Field(..., description="Signal type")
    score: float = Field(..., ge=0.0, le=100.0, description="Normalized score (0-100)")
    severity: Severity = Field(..., description="Severity level")
    status: SignalStatus = Field(..., description="Signal status")
    evidence_refs: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence references")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Update timestamp (ISO 8601)")
    resolved_at: Optional[str] = Field(None, description="Resolution timestamp (ISO 8601)")


# ============================================================================
# API Request/Response Models (per Section 11)
# ============================================================================

class ActorProfileResponse(BaseModel):
    """Response model for GET /v1/ubi/actors/{actor_id}/profile."""
    actor_id: str = Field(..., description="Actor identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    actor_type: ActorType = Field(..., description="Actor type")
    signals: Dict[str, List[BehaviouralSignal]] = Field(default_factory=dict, description="Signals grouped by dimension")
    features: List[BehaviouralFeature] = Field(default_factory=list, description="Recent features")
    baselines: List[BehaviouralBaseline] = Field(default_factory=list, description="Current baselines")
    stale: bool = Field(False, description="Whether data is stale")


class QuerySignalsRequest(BaseModel):
    """Request model for POST /v1/ubi/query/signals."""
    tenant_id: str = Field(..., description="Tenant identifier")
    scope: ActorScope = Field(..., description="Query scope")
    dimensions: Optional[List[Dimension]] = Field(None, description="Filter by dimensions")
    time_range: Dict[str, str] = Field(..., description="Time range with 'from' and 'to' ISO 8601 timestamps")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters (min_severity, actor_ids, team_ids, signal_types)")


class QuerySignalsResponse(BaseModel):
    """Response model for POST /v1/ubi/query/signals."""
    signals: List[BehaviouralSignal] = Field(..., description="Matching signals")
    stale: bool = Field(False, description="Whether data is stale")


class TenantConfigResponse(BaseModel):
    """Response model for GET /v1/ubi/config/{tenant_id}."""
    tenant_id: str = Field(..., description="Tenant identifier")
    config_version: str = Field(..., description="Configuration version identifier")
    enabled_event_categories: List[str] = Field(..., description="Allowed event types")
    feature_windows: Dict[str, str] = Field(..., description="Window configurations")
    aggregation_thresholds: Dict[str, int] = Field(..., description="Aggregation thresholds (e.g., min_team_size: 5)")
    enabled_signal_types: List[SignalType] = Field(..., description="Enabled signal types")
    privacy_settings: Dict[str, Any] = Field(..., description="Privacy configuration")
    anomaly_thresholds: Dict[str, Dict[str, float]] = Field(..., description="Z-score thresholds per dimension")
    baseline_algorithm: Dict[str, Any] = Field(..., description="Baseline algorithm parameters (e.g., alpha: 0.1)")


class TenantConfigRequest(BaseModel):
    """Request model for PUT /v1/ubi/config/{tenant_id}."""
    enabled_event_categories: Optional[List[str]] = Field(None, description="Allowed event types")
    feature_windows: Optional[Dict[str, str]] = Field(None, description="Window configurations")
    aggregation_thresholds: Optional[Dict[str, int]] = Field(None, description="Aggregation thresholds")
    enabled_signal_types: Optional[List[SignalType]] = Field(None, description="Enabled signal types")
    privacy_settings: Optional[Dict[str, Any]] = Field(None, description="Privacy configuration")
    anomaly_thresholds: Optional[Dict[str, Dict[str, float]]] = Field(None, description="Z-score thresholds per dimension")
    baseline_algorithm: Optional[Dict[str, Any]] = Field(None, description="Baseline algorithm parameters")


class TenantConfigUpdateResponse(BaseModel):
    """Response model for PUT /v1/ubi/config/{tenant_id}."""
    tenant_id: str = Field(..., description="Tenant identifier")
    config_version: str = Field(..., description="Configuration version identifier")
    config: TenantConfigResponse = Field(..., description="Updated configuration")
    receipt_id: Optional[str] = Field(None, description="Receipt ID for configuration change")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    ready: bool = Field(..., description="Ready status")
    checks: Dict[str, bool] = Field(..., description="Individual readiness checks")
    timestamp: Optional[datetime] = Field(None, description="Check timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")

