"""
SQLAlchemy ORM models for User Behaviour Intelligence (UBI) Module (EPC-9).

What: Database models matching PRD schema exactly
Why: Provides ORM layer for database operations
Reads/Writes: Reads/writes to PostgreSQL via SQLAlchemy
Contracts: PRD Section 10 (Data Model), NFR-3 (Scalability)
Risks: Model mismatch with PRD, constraint violations
"""

import uuid
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    Column, String, Integer, DateTime, CheckConstraint,
    UniqueConstraint, Index, Text, DECIMAL, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.types import TypeDecorator, CHAR, JSON as SQLJSON
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type."""

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
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
    """Platform-independent JSON type (JSONB for Postgres, JSON elsewhere)."""

    impl = SQLJSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        if dialect.name == "sqlite":
            return dialect.type_descriptor(SQLiteJSON())
        return dialect.type_descriptor(SQLJSON())


class BehaviouralEvent(Base):
    """
    BehaviouralEvent model matching PRD Section 10.1.

    Per PRD: Events derived from PM-3 SignalEnvelope, partitioned by tenant_id and dt.
    """
    __tablename__ = "behavioural_events"

    # Primary key
    event_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Required fields
    tenant_id = Column(String(255), nullable=False)
    actor_id = Column(String(255))
    actor_type = Column(String(50), nullable=False)
    source_system = Column(String(255))
    event_type = Column(String(255), nullable=False)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False)
    ingested_at = Column(DateTime(timezone=True), nullable=False)
    properties = Column(JSONType(), nullable=False, default={})
    privacy_tags = Column(JSONType(), nullable=False, default={})
    schema_version = Column(String(50), nullable=False)
    trace_id = Column(String(255))
    span_id = Column(String(255))
    correlation_id = Column(String(255))
    resource = Column(JSONType())
    
    # Partitioning column
    dt = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("actor_type IN ('human', 'ai_agent', 'service')", name='behavioural_events_actor_type_check'),
        Index('idx_behavioural_events_tenant_actor_timestamp', 'tenant_id', 'actor_id', 'timestamp_utc'),
        Index('idx_behavioural_events_tenant_dt', 'tenant_id', 'dt'),
        Index('idx_behavioural_events_tenant_event_type', 'tenant_id', 'event_type'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "event_id": str(self.event_id),
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "source_system": self.source_system,
            "event_type": self.event_type,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
            "properties": self.properties,
            "privacy_tags": self.privacy_tags,
            "schema_version": self.schema_version,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "correlation_id": self.correlation_id,
            "resource": self.resource,
        }


class BehaviouralFeature(Base):
    """
    BehaviouralFeature model matching PRD Section 10.2.

    Per PRD: Features computed over configurable windows, partitioned by tenant_id and dt.
    """
    __tablename__ = "behavioural_features"

    # Primary key
    feature_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Required fields
    tenant_id = Column(String(255), nullable=False)
    actor_scope = Column(String(50), nullable=False)
    actor_or_group_id = Column(String(255), nullable=False)
    feature_name = Column(String(255), nullable=False)
    window_start = Column(DateTime(timezone=True), nullable=False)
    window_end = Column(DateTime(timezone=True), nullable=False)
    value = Column(DECIMAL(20, 6), nullable=False)
    dimension = Column(String(50), nullable=False)
    confidence = Column(DECIMAL(3, 2), nullable=False)
    metadata_json = Column(
        "metadata",
        JSONType(),
        nullable=False,
        default={}
    )
    
    # Partitioning column
    dt = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("actor_scope IN ('actor', 'team', 'cohort')", name='behavioural_features_actor_scope_check'),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name='behavioural_features_confidence_check'),
        Index('idx_behavioural_features_tenant_scope_group', 'tenant_id', 'actor_scope', 'actor_or_group_id'),
        Index('idx_behavioural_features_tenant_feature_name', 'tenant_id', 'feature_name'),
        Index('idx_behavioural_features_tenant_dimension', 'tenant_id', 'dimension'),
        Index('idx_behavioural_features_tenant_dt', 'tenant_id', 'dt'),
        Index('idx_behavioural_features_window', 'window_start', 'window_end'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "feature_id": str(self.feature_id),
            "tenant_id": self.tenant_id,
            "actor_scope": self.actor_scope,
            "actor_or_group_id": self.actor_or_group_id,
            "feature_name": self.feature_name,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "window_end": self.window_end.isoformat() if self.window_end else None,
            "value": float(self.value) if self.value else None,
            "dimension": self.dimension,
            "confidence": float(self.confidence) if self.confidence else None,
            "metadata": self.metadata,
        }


class BehaviouralBaseline(Base):
    """
    BehaviouralBaseline model matching PRD Section 10.3.

    Per PRD: Baselines computed using EMA algorithm, partitioned by tenant_id and dt.
    """
    __tablename__ = "behavioural_baselines"

    # Primary key
    baseline_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Required fields
    tenant_id = Column(String(255), nullable=False)
    actor_scope = Column(String(50), nullable=False)
    actor_or_group_id = Column(String(255), nullable=False)
    feature_name = Column(String(255), nullable=False)
    window = Column(String(50), nullable=False)
    mean = Column(DECIMAL(20, 6), nullable=False)
    std_dev = Column(DECIMAL(20, 6), nullable=False)
    percentiles = Column(JSONType(), nullable=False, default={})
    last_recomputed_at = Column(DateTime(timezone=True), nullable=False)
    confidence = Column(DECIMAL(3, 2), nullable=False)
    
    # Partitioning column
    dt = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("actor_scope IN ('actor', 'team', 'cohort')", name='behavioural_baselines_actor_scope_check'),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name='behavioural_baselines_confidence_check'),
        Index('idx_behavioural_baselines_tenant_scope_group', 'tenant_id', 'actor_scope', 'actor_or_group_id'),
        Index('idx_behavioural_baselines_tenant_feature_name', 'tenant_id', 'feature_name'),
        Index('idx_behavioural_baselines_tenant_dt', 'tenant_id', 'dt'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "baseline_id": str(self.baseline_id),
            "tenant_id": self.tenant_id,
            "actor_scope": self.actor_scope,
            "actor_or_group_id": self.actor_or_group_id,
            "feature_name": self.feature_name,
            "window": self.window,
            "mean": float(self.mean) if self.mean else None,
            "std_dev": float(self.std_dev) if self.std_dev else None,
            "percentiles": self.percentiles,
            "last_recomputed_at": self.last_recomputed_at.isoformat() if self.last_recomputed_at else None,
            "confidence": float(self.confidence) if self.confidence else None,
        }


class BehaviouralSignal(Base):
    """
    BehaviouralSignal model matching PRD Section 10.4.

    Per PRD: Signals generated from features and baselines, partitioned by tenant_id and dt.
    """
    __tablename__ = "behavioural_signals"

    # Primary key
    signal_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Required fields
    tenant_id = Column(String(255), nullable=False)
    actor_scope = Column(String(50), nullable=False)
    actor_or_group_id = Column(String(255), nullable=False)
    dimension = Column(String(50), nullable=False)
    signal_type = Column(String(50), nullable=False)
    score = Column(DECIMAL(5, 2), nullable=False)
    severity = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    evidence_refs = Column(JSONType(), nullable=False, default=[])
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True))
    
    # Partitioning column
    dt = Column(DateTime, nullable=False)
    
    # Metadata (renamed to avoid conflict with created_at)
    created_at_meta = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        CheckConstraint("actor_scope IN ('actor', 'team', 'cohort', 'tenant')", name='behavioural_signals_actor_scope_check'),
        CheckConstraint("signal_type IN ('risk', 'opportunity', 'informational')", name='behavioural_signals_signal_type_check'),
        CheckConstraint("severity IN ('INFO', 'WARN', 'CRITICAL')", name='behavioural_signals_severity_check'),
        CheckConstraint("status IN ('active', 'resolved')", name='behavioural_signals_status_check'),
        CheckConstraint("score >= 0.0 AND score <= 100.0", name='behavioural_signals_score_check'),
        Index('idx_behavioural_signals_tenant_scope_group', 'tenant_id', 'actor_scope', 'actor_or_group_id'),
        Index('idx_behavioural_signals_tenant_dimension', 'tenant_id', 'dimension'),
        Index('idx_behavioural_signals_tenant_severity', 'tenant_id', 'severity'),
        Index('idx_behavioural_signals_tenant_status', 'tenant_id', 'status'),
        Index('idx_behavioural_signals_tenant_dt', 'tenant_id', 'dt'),
        Index('idx_behavioural_signals_created_at', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "signal_id": str(self.signal_id),
            "tenant_id": self.tenant_id,
            "actor_scope": self.actor_scope,
            "actor_or_group_id": self.actor_or_group_id,
            "dimension": self.dimension,
            "signal_type": self.signal_type,
            "score": float(self.score) if self.score else None,
            "severity": self.severity,
            "status": self.status,
            "evidence_refs": self.evidence_refs,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class TenantConfiguration(Base):
    """
    TenantConfiguration model matching PRD FR-12.

    Per PRD: Versioned tenant configurations for event filtering, feature windows, etc.
    """
    __tablename__ = "tenant_configurations"

    # Primary key
    config_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Required fields
    tenant_id = Column(String(255), nullable=False, unique=True)
    config_version = Column(String(50), nullable=False)
    enabled_event_categories = Column(JSONType(), nullable=False, default=[])
    feature_windows = Column(JSONType(), nullable=False, default={})
    aggregation_thresholds = Column(JSONType(), nullable=False, default={})
    enabled_signal_types = Column(JSONType(), nullable=False, default=[])
    privacy_settings = Column(JSONType(), nullable=False, default={})
    anomaly_thresholds = Column(JSONType(), nullable=False, default={})
    baseline_algorithm = Column(JSONType(), nullable=False, default={})
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "config_id": str(self.config_id),
            "tenant_id": self.tenant_id,
            "config_version": self.config_version,
            "enabled_event_categories": self.enabled_event_categories,
            "feature_windows": self.feature_windows,
            "aggregation_thresholds": self.aggregation_thresholds,
            "enabled_signal_types": self.enabled_signal_types,
            "privacy_settings": self.privacy_settings,
            "anomaly_thresholds": self.anomaly_thresholds,
            "baseline_algorithm": self.baseline_algorithm,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }


class ReceiptQueue(Base):
    """
    ReceiptQueue model for local queueing of receipts when ERIS is unavailable.

    Per PRD FR-13: Local persistent queue for receipt emission retries.
    """
    __tablename__ = "receipt_queue"

    # Primary key
    queue_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Required fields
    tenant_id = Column(String(255), nullable=False)
    receipt = Column(JSONType(), nullable=False)
    retry_count = Column(Integer, nullable=False, default=0)
    next_retry_at = Column(DateTime(timezone=True), nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_receipt_queue_tenant_next_retry', 'tenant_id', 'next_retry_at'),
        Index('idx_receipt_queue_next_retry', 'next_retry_at'),
    )


class ReceiptDLQ(Base):
    """
    ReceiptDLQ model for dead letter queue of failed receipts.

    Per PRD FR-13: DLQ for receipts that failed after max retry.
    """
    __tablename__ = "receipt_dlq"

    # Primary key
    dlq_id = Column(GUID(), primary_key=True, default=uuid.uuid4)

    # Required fields
    tenant_id = Column(String(255), nullable=False)
    receipt = Column(JSONType(), nullable=False)
    failure_reason = Column(Text, nullable=False)
    retry_count = Column(Integer, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_receipt_dlq_tenant_created', 'tenant_id', 'created_at'),
    )
