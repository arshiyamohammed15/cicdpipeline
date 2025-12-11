"""
SQLAlchemy ORM models for Integration Adapters Module (M10).

What: Database models matching PRD Section 10.2 exactly
Why: Provide ORM access to provider registry, connections, webhooks, polling, events, and actions
Reads/Writes: PostgreSQL via SQLAlchemy (JSONB) with SQLite fallback for tests
Contracts: PRD database schema specification & indexing strategy
Risks: Model drift vs. schema, incorrect JSON handling, tenant isolation gaps
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    TIMESTAMP,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR, JSON as SQLJSON

try:  # pragma: no cover - PostgreSQL available in runtime
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB as PG_JSONB

    HAS_POSTGRES = True
    JSON_TYPE = PG_JSONB
    UUID_TYPE = PG_UUID(as_uuid=True)
except ImportError:  # pragma: no cover - SQLite fallback for tests
    from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON

    HAS_POSTGRES = False
    JSON_TYPE = SQLiteJSON  # type: ignore
    UUID_TYPE = String(36)

Base = declarative_base()
TIMESTAMP_TYPE = TIMESTAMP(timezone=True) if HAS_POSTGRES else DateTime


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

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_JSONB())
        return dialect.type_descriptor(SQLJSON)


class IntegrationProvider(Base):
    """ORM model for `integration_providers` table - Provider registry per FR-1."""

    __tablename__ = "integration_providers"

    provider_id = Column(String(255), primary_key=True)
    category = Column(String(50), nullable=False)  # SCM, issue_tracker, chat, ci_cd, observability, knowledge
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="alpha", server_default="alpha")  # alpha/beta/GA/deprecated
    capabilities = Column(JSONType(), nullable=False, default=lambda: {})  # webhook, polling, outbound_actions flags
    api_version = Column(String(50), nullable=True)
    
    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'status' not in kwargs:
            kwargs['status'] = 'alpha'
        if 'capabilities' not in kwargs:
            kwargs['capabilities'] = {}
        super().__init__(**kwargs)

    # Relationships
    connections = relationship("IntegrationConnection", back_populates="provider", cascade="all, delete-orphan")


class IntegrationConnection(Base):
    """ORM model for `integration_connections` table - Tenant-scoped connections per FR-2."""

    __tablename__ = "integration_connections"

    connection_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)
    provider_id = Column(String(255), ForeignKey("integration_providers.provider_id"), nullable=False)
    display_name = Column(String(255), nullable=False)
    auth_ref = Column(String(255), nullable=False)  # Reference to KMS secret (KID/secret_id)
    status = Column(String(50), nullable=False, default="pending_verification", server_default="pending_verification")  # pending_verification, active, suspended, error, deleted
    enabled_capabilities = Column(JSONType(), nullable=False, default=lambda: {})  # webhook, polling, outbound_actions
    metadata_tags = Column(JSONType(), nullable=False, default=lambda: {})  # e.g., default repo organisation
    created_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_verified_at = Column(TIMESTAMP_TYPE, nullable=True)
    
    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'status' not in kwargs:
            kwargs['status'] = 'pending_verification'
        if 'enabled_capabilities' not in kwargs:
            kwargs['enabled_capabilities'] = {}
        if 'metadata_tags' not in kwargs:
            kwargs['metadata_tags'] = {}
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.utcnow()
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.utcnow()
        if 'connection_id' not in kwargs:
            kwargs['connection_id'] = uuid.uuid4()
        super().__init__(**kwargs)

    # Relationships
    provider = relationship("IntegrationProvider", back_populates="connections")
    webhook_registrations = relationship("WebhookRegistration", back_populates="connection", cascade="all, delete-orphan")
    polling_cursors = relationship("PollingCursor", back_populates="connection", cascade="all, delete-orphan")
    adapter_events = relationship("AdapterEvent", back_populates="connection", cascade="all, delete-orphan")
    normalised_actions = relationship("NormalisedAction", back_populates="connection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_connections_tenant_provider", "tenant_id", "provider_id"),
        Index("idx_connections_status", "tenant_id", "status"),
    )


class WebhookRegistration(Base):
    """ORM model for `webhook_registrations` table - Webhook endpoint registrations per FR-4."""

    __tablename__ = "webhook_registrations"

    registration_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    connection_id = Column(GUID(), ForeignKey("integration_connections.connection_id"), nullable=False)
    public_url = Column(String(500), nullable=False)
    secret_ref = Column(String(255), nullable=False)  # Reference to KMS signing secret
    events_subscribed = Column(JSONType(), nullable=False, default=lambda: [])  # List of event types
    status = Column(String(50), nullable=False, default="pending", server_default="pending")  # pending, active, suspended, deleted
    created_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'events_subscribed' not in kwargs:
            kwargs['events_subscribed'] = []
        if 'status' not in kwargs:
            kwargs['status'] = 'pending'
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.utcnow()
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.utcnow()
        if 'registration_id' not in kwargs:
            kwargs['registration_id'] = uuid.uuid4()
        super().__init__(**kwargs)

    # Relationships
    connection = relationship("IntegrationConnection", back_populates="webhook_registrations")

    __table_args__ = (
        Index("idx_webhook_registrations_connection", "connection_id"),
    )


class PollingCursor(Base):
    """ORM model for `polling_cursors` table - Polling state per connection per FR-5."""

    __tablename__ = "polling_cursors"

    cursor_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    connection_id = Column(GUID(), ForeignKey("integration_connections.connection_id"), nullable=False)
    cursor_position = Column(Text, nullable=True)  # e.g., last event id/timestamp
    last_polled_at = Column(TIMESTAMP_TYPE, nullable=True)
    created_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.utcnow()
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.utcnow()
        if 'cursor_id' not in kwargs:
            kwargs['cursor_id'] = uuid.uuid4()
        super().__init__(**kwargs)

    # Relationships
    connection = relationship("IntegrationConnection", back_populates="polling_cursors")

    __table_args__ = (
        Index("idx_polling_cursors_connection", "connection_id"),
    )


class AdapterEvent(Base):
    """ORM model for `adapter_events` table - Raw event tracking (optional, for audit) per FR-6."""

    __tablename__ = "adapter_events"

    event_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    connection_id = Column(GUID(), ForeignKey("integration_connections.connection_id"), nullable=False)
    provider_event_type = Column(String(255), nullable=False)
    received_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, nullable=False)
    raw_payload_ref = Column(String(500), nullable=True)  # Reference to redacted raw payload if stored
    
    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'received_at' not in kwargs:
            kwargs['received_at'] = datetime.utcnow()
        if 'event_id' not in kwargs:
            kwargs['event_id'] = uuid.uuid4()
        super().__init__(**kwargs)

    # Relationships
    connection = relationship("IntegrationConnection", back_populates="adapter_events")

    __table_args__ = (
        Index("idx_adapter_events_connection", "connection_id", "received_at"),
    )


class NormalisedAction(Base):
    """ORM model for `normalised_actions` table - Outbound action queue per FR-7."""

    __tablename__ = "normalised_actions"

    action_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)
    provider_id = Column(String(255), nullable=False)
    connection_id = Column(GUID(), ForeignKey("integration_connections.connection_id"), nullable=False)
    canonical_type = Column(String(255), nullable=False)  # e.g., post_chat_message, create_issue, comment_on_pr
    target = Column(JSONType(), nullable=False, default=lambda: {})  # channel, issue_key, pr_id, etc.
    payload = Column(JSONType(), nullable=False, default=lambda: {})  # Structured action data
    idempotency_key = Column(String(255), nullable=False)  # Required for safe retries
    correlation_id = Column(String(255), nullable=True)  # Link back to MMM/Detection/UBI DecisionReceipt
    status = Column(String(50), nullable=False, default="pending", server_default="pending")  # pending, processing, completed, failed
    created_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP_TYPE, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(TIMESTAMP_TYPE, nullable=True)
    
    def __init__(self, **kwargs):
        """Initialize with defaults."""
        if 'target' not in kwargs:
            kwargs['target'] = {}
        if 'payload' not in kwargs:
            kwargs['payload'] = {}
        if 'status' not in kwargs:
            kwargs['status'] = 'pending'
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.utcnow()
        if 'updated_at' not in kwargs:
            kwargs['updated_at'] = datetime.utcnow()
        if 'action_id' not in kwargs:
            kwargs['action_id'] = uuid.uuid4()
        super().__init__(**kwargs)

    # Relationships
    connection = relationship("IntegrationConnection", back_populates="normalised_actions")

    __table_args__ = (
        Index("idx_normalised_actions_tenant", "tenant_id", "status", "created_at"),
        Index("idx_normalised_actions_idempotency", "idempotency_key"),
        Index("idx_normalised_actions_connection", "connection_id", "status"),
    )
