"""
Pydantic domain models for MMM Engine (mirror/mentor/multiplier).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ActorType(str, Enum):
    HUMAN = "human"
    AI_AGENT = "ai_agent"


class ActionType(str, Enum):
    MIRROR = "mirror"
    MENTOR = "mentor"
    MULTIPLIER = "multiplier"


class Surface(str, Enum):
    IDE = "ide"
    CI = "ci"
    ALERT = "alert"


class MMMSignalInput(BaseModel):
    signal_id: str
    tenant_id: str
    actor_id: Optional[str]
    actor_type: Optional[ActorType] = ActorType.HUMAN
    source: str
    event_type: str
    severity: Optional[str]
    occurred_at: datetime
    payload: Dict[str, Any] = Field(default_factory=dict)


class MMMContext(BaseModel):
    tenant_id: str
    actor_id: Optional[str]
    actor_type: ActorType
    actor_roles: List[str] = Field(default_factory=list)
    repo_id: Optional[str]
    branch: Optional[str]
    file_path: Optional[str]
    policy_snapshot_id: Optional[str]
    quiet_hours: Optional[Dict[str, Any]]
    recent_signals: List[Dict[str, Any]] = Field(default_factory=list)


class PlaybookStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class MMMAction(BaseModel):
    action_id: str
    type: ActionType
    surfaces: List[Surface]
    payload: Dict[str, Any]
    requires_consent: bool = False
    requires_dual_channel: bool = False


class MMMDecision(BaseModel):
    decision_id: str
    tenant_id: str
    actor_id: Optional[str]
    actor_type: ActorType
    context: MMMContext
    actions: List[MMMAction]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    policy_snapshot_id: Optional[str]
    latency_warning: bool = False  # Per PRD NFR-1
    degraded_mode: bool = False  # Per PRD NFR-6


class MMMOutcome(BaseModel):
    decision_id: str
    action_id: str
    tenant_id: str
    actor_id: Optional[str]
    result: str
    reason: Optional[str]
    timestamp: Optional[datetime] = None


class Playbook(BaseModel):
    playbook_id: str
    tenant_id: str
    version: str
    name: str
    status: PlaybookStatus
    triggers: List[Dict[str, Any]] = Field(default_factory=list)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    limits: Dict[str, Any] = Field(default_factory=dict)


class PlaybookCreateRequest(BaseModel):
    version: str = "1.0.0"
    name: str
    triggers: List[Dict[str, Any]] = Field(default_factory=list)
    conditions: List[Dict[str, Any]] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)
    limits: Dict[str, Any] = Field(default_factory=dict)


class DecideRequest(BaseModel):
    tenant_id: str
    actor_id: Optional[str]
    actor_type: Optional[ActorType] = ActorType.HUMAN
    context: Dict[str, Any] = Field(default_factory=dict)
    signal: Optional[MMMSignalInput] = None


class DecideResponse(BaseModel):
    decision: MMMDecision


# Actor Preferences Models (FR-14)
class ActorPreferences(BaseModel):
    preference_id: str
    tenant_id: str
    actor_id: str
    opt_out_categories: List[str] = Field(default_factory=list)
    snooze_until: Optional[datetime] = None
    preferred_surfaces: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ActorPreferencesCreateRequest(BaseModel):
    opt_out_categories: List[str] = Field(default_factory=list)
    preferred_surfaces: List[str] = Field(default_factory=list)


class ActorPreferencesUpdateRequest(BaseModel):
    opt_out_categories: Optional[List[str]] = None
    preferred_surfaces: Optional[List[str]] = None
    snooze_until: Optional[datetime] = None


class ActorPreferencesSnoozeRequest(BaseModel):
    duration_hours: Optional[int] = None
    until: Optional[datetime] = None


# Tenant MMM Policy Models (FR-13)
class TenantMMMPolicy(BaseModel):
    policy_id: str
    tenant_id: str
    enabled_surfaces: List[str] = Field(default_factory=lambda: ["ide", "ci", "alert"])
    quotas: Dict[str, int] = Field(default_factory=lambda: {"max_actions_per_day": 10, "max_actions_per_hour": 3})
    quiet_hours: Dict[str, int] = Field(default_factory=lambda: {"start": 22, "end": 6})
    enabled_action_types: List[str] = Field(default_factory=lambda: ["mirror", "mentor", "multiplier"])
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TenantMMMPolicyUpdateRequest(BaseModel):
    enabled_surfaces: Optional[List[str]] = None
    quotas: Optional[Dict[str, int]] = None
    quiet_hours: Optional[Dict[str, int]] = None
    enabled_action_types: Optional[List[str]] = None


# Dual-Channel Approval Models (FR-6)
class DualChannelApprovalStatus(str, Enum):
    PENDING = "pending"
    FIRST_APPROVED = "first_approved"
    FULLY_APPROVED = "fully_approved"
    REJECTED = "rejected"


class DualChannelApproval(BaseModel):
    approval_id: str
    action_id: str
    decision_id: str
    actor_id: str
    approver_id: Optional[str] = None
    first_approval_at: Optional[datetime] = None
    second_approval_at: Optional[datetime] = None
    status: DualChannelApprovalStatus = DualChannelApprovalStatus.PENDING
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DualChannelApprovalRequest(BaseModel):
    action_id: str
    decision_id: str
    actor_id: str

