"""
SQLAlchemy ORM models for MMM Engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Index,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import TypeDecorator, CHAR, JSON as SQLJSON

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent UUID/GUID type."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID

            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if not isinstance(value, uuid.UUID):
            return str(uuid.UUID(value))
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)


class JSONType(TypeDecorator):
    """JSON type portable across Postgres/SQLite."""

    impl = SQLJSON
    cache_ok = True


class PlaybookModel(Base):
    __tablename__ = "mmm_playbooks"

    playbook_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="draft")
    description = Column(Text, nullable=True)
    triggers = Column(JSONType(), nullable=False, default=list)
    conditions = Column(JSONType(), nullable=False, default=list)
    actions = Column(JSONType(), nullable=False, default=list)
    limits = Column(JSONType(), nullable=False, default=dict)
    metadata_json = Column(JSONType(), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_playbooks_tenant", "tenant_id"),
        Index("idx_playbooks_status", "tenant_id", "status"),
    )


class DecisionModel(Base):
    __tablename__ = "mmm_decisions"

    decision_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False)
    actor_id = Column(String(255), nullable=True)
    actor_type = Column(String(50), nullable=False, default="human")
    context = Column(JSONType(), nullable=False, default=dict)
    signal_reference = Column(JSONType(), nullable=True)
    policy_snapshot_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    actions = relationship("ActionModel", back_populates="decision", cascade="all, delete-orphan")
    outcomes = relationship("OutcomeModel", back_populates="decision", cascade="all, delete-orphan")

    __table_args__ = (Index("idx_decisions_tenant", "tenant_id", "created_at"),)


class ActionModel(Base):
    __tablename__ = "mmm_actions"

    action_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_id = Column(GUID(), ForeignKey("mmm_decisions.decision_id", ondelete="CASCADE"), nullable=False)
    type = Column(String(20), nullable=False)
    surfaces = Column(JSONType(), nullable=False, default=list)
    payload = Column(JSONType(), nullable=False, default=dict)
    requires_consent = Column(Boolean, default=False)
    requires_dual_channel = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    decision = relationship("DecisionModel", back_populates="actions")


class OutcomeModel(Base):
    __tablename__ = "mmm_outcomes"

    outcome_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    decision_id = Column(GUID(), ForeignKey("mmm_decisions.decision_id", ondelete="CASCADE"), nullable=False)
    action_id = Column(GUID(), nullable=False)
    actor_id = Column(String(255), nullable=True)
    result = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    metadata_json = Column(JSONType(), nullable=False, default=dict)
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    decision = relationship("DecisionModel", back_populates="outcomes")


class ExperimentModel(Base):
    __tablename__ = "mmm_experiments"

    experiment_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="active")
    config = Column(JSONType(), nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (Index("idx_experiments_tenant", "tenant_id", "status"),)


class ActorPreferencesModel(Base):
    __tablename__ = "mmm_actor_preferences"

    preference_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False)
    actor_id = Column(String(255), nullable=False)
    opt_out_categories = Column(JSONType(), nullable=False, default=list)
    snooze_until = Column(DateTime(timezone=True), nullable=True)
    preferred_surfaces = Column(JSONType(), nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_actor_preferences_tenant_actor", "tenant_id", "actor_id", unique=True),
    )


class TenantPolicyModel(Base):
    __tablename__ = "mmm_tenant_policies"

    policy_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, unique=True)
    enabled_surfaces = Column(JSONType(), nullable=False, default=lambda: ["ide", "ci", "alert"])
    quotas = Column(JSONType(), nullable=False, default=lambda: {"max_actions_per_day": 10, "max_actions_per_hour": 3})
    quiet_hours = Column(JSONType(), nullable=False, default=lambda: {"start": 22, "end": 6})
    enabled_action_types = Column(JSONType(), nullable=False, default=lambda: ["mirror", "mentor", "multiplier"])
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_tenant_policies_tenant", "tenant_id", unique=True),
    )


class DualChannelApprovalModel(Base):
    __tablename__ = "mmm_dual_channel_approvals"

    approval_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    action_id = Column(GUID(), nullable=False)
    decision_id = Column(GUID(), nullable=False)
    actor_id = Column(String(255), nullable=False)
    approver_id = Column(String(255), nullable=True)
    first_approval_at = Column(DateTime(timezone=True), nullable=True)
    second_approval_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_dual_channel_action", "action_id"),
        Index("idx_dual_channel_decision", "decision_id"),
        Index("idx_dual_channel_status", "status"),
    )


