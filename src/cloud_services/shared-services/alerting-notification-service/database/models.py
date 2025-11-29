"""SQLModel ORM entities for Alerting & Notification Service."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    alert_id: str = Field(primary_key=True, index=True)
    schema_version: str = Field(default="1.0.0")
    tenant_id: str = Field(index=True)
    source_module: str
    plane: str
    environment: str
    component_id: str
    severity: str
    priority: Optional[str] = None
    category: str
    summary: str
    description: Optional[str] = None
    labels: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    started_at: datetime
    ended_at: Optional[datetime] = None
    last_seen_at: datetime
    dedup_key: str = Field(index=True)
    incident_id: Optional[str] = Field(foreign_key="incidents.incident_id")
    policy_refs: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    status: str = Field(default="open", index=True)
    snoozed_until: Optional[datetime] = None
    links: List[Dict[str, str]] = Field(default_factory=list, sa_column=Column(JSON))
    runbook_refs: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    automation_hooks: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    component_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    slo_snapshot_url: Optional[str] = None


class Incident(SQLModel, table=True):
    __tablename__ = "incidents"

    incident_id: str = Field(primary_key=True)
    schema_version: str = Field(default="1.0.0")
    tenant_id: str = Field(index=True)
    plane: Optional[str] = None
    component_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: str
    opened_at: datetime
    resolved_at: Optional[datetime] = None
    mitigated_at: Optional[datetime] = None
    owner_group: Optional[str] = None
    on_call_schedule_id: Optional[str] = None
    status: str = Field(default="open")
    alert_ids: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    correlation_keys: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    dependency_refs: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    policy_refs: List[str] = Field(default_factory=list, sa_column=Column(JSON))

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    notification_id: str = Field(primary_key=True)
    schema_version: str = Field(default="1.0.0")
    tenant_id: str = Field(index=True)
    alert_id: Optional[str] = Field(default=None, foreign_key="alerts.alert_id")
    incident_id: Optional[str] = Field(default=None, foreign_key="incidents.incident_id")
    target_id: str
    channel: str
    status: str = Field(default="pending")
    attempts: int = Field(default=0)
    last_attempt_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    next_attempt_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    channel_context: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    policy_id: Optional[str] = None


class EscalationPolicy(SQLModel, table=True):
    __tablename__ = "escalation_policies"

    policy_id: str = Field(primary_key=True)
    name: str
    scope: str
    enabled: bool = Field(default=True)
    steps: List[Dict[str, str]] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    fallback_targets: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    policy_metadata: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))


class UserNotificationPreference(SQLModel, table=True):
    __tablename__ = "user_notification_preferences"

    user_id: str = Field(primary_key=True)
    tenant_id: str
    channels: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    quiet_hours: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    severity_threshold: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    timezone: str = Field(default="UTC")
    channel_preferences: Dict[str, List[str]] = Field(default_factory=dict, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)
