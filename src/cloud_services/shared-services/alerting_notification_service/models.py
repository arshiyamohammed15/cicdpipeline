"""API schemas for Alerting & Notification Service."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RelatedLink(BaseModel):
    kind: str = Field(description="Type of link, e.g., metric, trace, log, runbook")
    href: str = Field(description="URL pointing to the resource")
    description: Optional[str] = None


class AlertPayload(BaseModel):
    schema_version: str = Field(default="1.0.0")
    alert_id: str
    tenant_id: str
    source_module: str
    plane: str
    environment: str
    component_id: str
    severity: str
    priority: Optional[str] = None
    category: str
    summary: str
    description: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict)
    started_at: datetime
    ended_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    dedup_key: str
    incident_id: Optional[str] = None
    policy_refs: List[str] = Field(default_factory=list)
    links: List[RelatedLink] = Field(default_factory=list)
    runbook_refs: List[str] = Field(default_factory=list)
    automation_hooks: List[str] = Field(default_factory=list)
    status: str = Field(default="open")
    slo_snapshot: Optional[str] = None


class AlertResponse(BaseModel):
    alert_id: str
    status: str
    incident_id: Optional[str] = None


class SearchFilters(BaseModel):
    severity: Optional[str] = None
    category: Optional[str] = None
    tenant_id: Optional[str] = None
    status: Optional[str] = None


class LifecycleRequest(BaseModel):
    actor: str
    reason: Optional[str] = None


class SnoozeRequest(BaseModel):
    actor: str
    duration_minutes: int = Field(ge=1, le=720)


class UserPreferencePayload(BaseModel):
    user_id: str
    tenant_id: str
    channels: List[str] = Field(default_factory=list)
    quiet_hours: Dict[str, str] = Field(default_factory=dict, description="DayOfWeek:HH:MM-HH:MM")
    severity_threshold: Dict[str, str] = Field(default_factory=dict)
    timezone: str = Field(default="UTC")
    channel_preferences: Dict[str, List[str]] = Field(default_factory=dict)
