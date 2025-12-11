"""
Pydantic schemas for the Health & Reliability Monitoring APIs.

These models implement the contracts defined in the PRD, covering components,
telemetry payloads, health snapshots, SLO status, Safe-to-Act, and response envelopes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl, conint, confloat, field_validator

from .config import load_settings

settings = load_settings()

HealthState = Literal["OK", "DEGRADED", "FAILED", "UNKNOWN"]
MetricsProfile = Literal["GOLDEN_SIGNALS", "RED", "USE"]
ComponentType = Literal["service", "agent", "dependency", "plane", "composite_group"]


class DependencyReference(BaseModel):
    """Represents a dependency entry in the component registry."""

    component_id: str = Field(..., min_length=3, max_length=128)
    critical: bool = Field(default=True, description="Whether dependency is critical to availability.")


class ComponentDefinition(BaseModel):
    """Registry entity describing a monitored component."""

    component_id: str = Field(..., description="Unique component identifier", min_length=3, max_length=128)
    name: str = Field(..., max_length=255)
    component_type: ComponentType
    plane: Literal["Laptop", "Tenant", "Product", "Shared"]
    environment: Literal["dev", "test", "stage", "prod"] = Field(default="dev")
    tenant_scope: Literal["tenant", "global", "shared"]
    dependencies: List[DependencyReference] = Field(default_factory=list)
    metrics_profile: List[MetricsProfile] = Field(default_factory=list)
    health_policies: List[str] = Field(default_factory=list, description="Policy IDs from EPC-3")
    slo_target: Optional[float] = Field(default=None, description="SLO percentage (0-100)")
    error_budget_minutes: Optional[int] = Field(default=None, ge=0)
    owner_team: Optional[str] = Field(default=None, max_length=255)
    documentation_url: Optional[HttpUrl] = None


class ComponentRegistrationResponse(BaseModel):
    """Response for POST /v1/health/components."""

    component_id: str
    enrolled: bool = True
    message: str = Field(default="Component registered successfully.")


class TelemetryPayload(BaseModel):
    """Standardized telemetry ingestion payload."""

    component_id: str
    tenant_id: Optional[str] = None
    plane: str
    environment: str
    timestamp: datetime
    metrics: Dict[str, float] = Field(default_factory=dict)
    labels: Dict[str, str] = Field(default_factory=dict)
    telemetry_type: Literal["metrics", "probe", "heartbeat"]

    @field_validator("labels")
    @classmethod
    def enforce_label_cardinality(cls, labels: Dict[str, str]) -> Dict[str, str]:
        """Ensure labels remain compact to satisfy NFR-4."""
        limit = settings.telemetry.label_cardinality_limit
        if len(labels) > limit:
            raise ValueError(f"Label cardinality exceeds limit ({limit}).")
        return labels


class HealthSnapshot(BaseModel):
    """Evaluated health state for a component at a point in time."""

    snapshot_id: str
    component_id: str
    tenant_id: Optional[str] = None
    plane: str
    environment: str
    state: HealthState
    reason_code: str
    metrics_summary: Dict[str, float] = Field(default_factory=dict)
    slo_state: Optional[Literal["within_budget", "approaching", "breached"]] = None
    policy_version: Optional[str] = None
    evaluated_at: datetime


class TenantHealthView(BaseModel):
    """Aggregated tenant health response."""

    tenant_id: str
    plane_states: Dict[str, HealthState]
    counts: Dict[HealthState, int]
    error_budget: Dict[str, float] = Field(default_factory=dict)
    updated_at: datetime


class PlaneHealthView(BaseModel):
    """Aggregated plane health response."""

    plane: str
    environment: str
    state: HealthState
    component_breakdown: Dict[HealthState, List[str]]
    updated_at: datetime


class SLOStatus(BaseModel):
    """SLI/SLO posture for a component."""

    component_id: str
    slo_id: str
    window: Literal["7d", "30d", "90d"]
    sli_values: Dict[str, confloat(ge=0)] = Field(default_factory=dict)
    error_budget_total_minutes: Optional[int] = Field(default=None, ge=0)
    error_budget_consumed_minutes: Optional[int] = Field(default=None, ge=0)
    burn_rate: Optional[confloat(ge=0)] = None
    state: Literal["within_budget", "approaching", "breached", "none"] = "none"


class SafeToActRequest(BaseModel):
    """Request contract for Safe-to-Act API."""

    tenant_id: str
    plane: str = "Product"
    action_type: Literal[
        "auto_remediate",
        "rollout",
        "risky_migration",
        "standard_action",
        "deployment",
        "rollback",
        "scale",
        "migration",
    ]
    component_scope: Optional[List[str]] = Field(
        default=None, description="Optional list of component IDs relevant to gating."
    )


class SafeToActResponse(BaseModel):
    """Response contract for Safe-to-Act API."""

    allowed: bool
    recommended_mode: Literal["normal", "degraded", "read_only"]
    reason_codes: List[str]
    evaluated_at: datetime
    snapshot_refs: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    """Common error envelope."""

    error_code: str
    message: str
    correlation_id: str
    details: Optional[Dict[str, str]] = None
