"""
SQLAlchemy ORM models for ERIS database schema.

What: Database models matching schema.sql for receipts, batches, meta-receipts, exports
Why: Type-safe database access, query building, relationship management
Reads/Writes: Reads/writes to PostgreSQL database
Contracts: Database schema per PRD Section 8
Risks: Schema drift, performance issues with large datasets
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Date, Text, DECIMAL, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Receipt(Base):
    """Receipt ORM model per PRD Section 8.1."""
    __tablename__ = "receipts"

    # Canonical Receipt Fields
    receipt_id = Column(PGUUID(as_uuid=True), primary_key=True)
    gate_id = Column(String(255), nullable=False)
    schema_version = Column(String(50), nullable=False)
    policy_version_ids = Column(ARRAY(String), nullable=False)
    snapshot_hash = Column(String(255), nullable=False)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False)
    timestamp_monotonic_ms = Column(Integer, nullable=False)
    evaluation_point = Column(String(50), nullable=False)
    inputs = Column(JSONB, nullable=False)
    decision_status = Column(String(50), nullable=False)
    decision_rationale = Column(Text, nullable=False)
    decision_badges = Column(ARRAY(String))
    result = Column(JSONB)
    actor_repo_id = Column(String(255), nullable=False)
    actor_machine_fingerprint = Column(String(255))
    actor_type = Column(String(50))
    evidence_handles = Column(JSONB)
    degraded = Column(Boolean, default=False)
    signature = Column(Text, nullable=False)

    # ERIS-Specific Fields
    tenant_id = Column(String(255), nullable=False)
    plane = Column(String(100))
    environment = Column(String(50))
    module_id = Column(String(255))
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    severity = Column(String(50))
    risk_score = Column(DECIMAL(10, 2))

    # Cryptographic Integrity
    hash = Column(String(255), nullable=False)
    prev_hash = Column(String(255))
    chain_id = Column(String(500), nullable=False)
    signature_algo = Column(String(50))
    kid = Column(String(255))
    signature_verification_status = Column(String(50))

    # Receipt Linking
    parent_receipt_id = Column(PGUUID(as_uuid=True))
    related_receipt_ids = Column(ARRAY(PGUUID(as_uuid=True)))

    # Source
    emitter_service = Column(String(255))
    ingest_source = Column(String(100))

    # Time Partitioning
    dt = Column(Date, nullable=False)

    # Retention
    retention_state = Column(String(50), default="active")
    legal_hold = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class CourierBatch(Base):
    """Courier batch ORM model per PRD Section 8.3."""
    __tablename__ = "courier_batches"

    batch_id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String(255), nullable=False)
    emitter_service = Column(String(255), nullable=False)
    merkle_root = Column(String(255), nullable=False)
    sequence_numbers = Column(ARRAY(String), nullable=False)
    receipt_count = Column(Integer, nullable=False)
    leaf_hashes = Column(ARRAY(String), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class MetaReceipt(Base):
    """Meta-receipt ORM model for FR-9 access audit."""
    __tablename__ = "meta_receipts"

    access_event_id = Column(PGUUID(as_uuid=True), primary_key=True)
    requester_actor_id = Column(String(255), nullable=False)
    actor_type = Column(String(50), nullable=False)
    requester_role = Column(String(100))
    tenant_ids = Column(ARRAY(String), nullable=False)
    plane = Column(String(100))
    environment = Column(String(50))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    query_scope = Column(Text)
    decision = Column(String(50), nullable=False)
    receipt_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ExportJob(Base):
    """Export job ORM model for FR-11 export tracking."""
    __tablename__ = "export_jobs"

    export_id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")
    export_format = Column(String(50), nullable=False)
    compression = Column(String(50))
    filters = Column(JSONB)
    download_url = Column(Text)
    receipt_count = Column(Integer)
    file_size = Column(Integer)
    checksum = Column(String(255))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True))


class DLQEntry(Base):
    """DLQ entry ORM model for FR-2 invalid receipt storage."""
    __tablename__ = "dlq_entries"

    dlq_entry_id = Column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(String(255))
    receipt = Column(JSONB, nullable=False)
    rejection_reason = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
