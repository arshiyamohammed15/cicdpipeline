"""
Pydantic domain models for MMM Engine (mirror/mentor/multiplier).
"""

from __future__ import annotations

from datetime import datetime
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


class MMMOutcome(BaseModel):
    decision_id: str
    action_id: str
    tenant_id: str
    actor_id: Optional[str]
    result: str
    reason: Optional[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


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


