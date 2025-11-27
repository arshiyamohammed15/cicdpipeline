"""
SQLAlchemy ORM models for Data Governance & Privacy Module (M22).

What: Database models matching PRD schema exactly (lines 320-412)
Why: Provide ORM access to data classification, consent, lineage, and retention tables
Reads/Writes: PostgreSQL via SQLAlchemy (JSONB) with SQLite fallback for tests
Contracts: PRD database schema specification & indexing strategy
Risks: Model drift vs. schema, incorrect JSON handling, tenant isolation gaps
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, Numeric, String, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base

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


class DataClassification(Base):
    """ORM model for `data_classification` table."""

    __tablename__ = "data_classification"

    data_id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    data_location = Column(String(500), nullable=False)
    classification_level = Column(String(50), nullable=False)
    sensitivity_tags = Column(JSON_TYPE, nullable=False)
    classification_confidence = Column(Numeric(3, 2), nullable=True)
    classified_at = Column(TIMESTAMP_TYPE, nullable=False, default=datetime.utcnow)
    classified_by = Column(UUID_TYPE, nullable=False)
    tenant_id = Column(UUID_TYPE, nullable=False)

    __table_args__ = (
        Index(
            "idx_data_classification_data_tenant",
            "data_id",
            "tenant_id",
            unique=True,
        ),
        Index(
            "idx_classification_level_tenant",
            "classification_level",
            "tenant_id",
        ),
        *(  # PostgreSQL-specific search indexes
            [
                Index(
                    "idx_sensitivity_tags_gin",
                    "sensitivity_tags",
                    postgresql_using="gin",
                ),
                Index(
                    "idx_data_location_trgm",
                    "data_location",
                    postgresql_using="gin",
                    postgresql_ops={"data_location": "gin_trgm_ops"},
                ),
            ]
            if HAS_POSTGRES
            else []
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable representation."""
        return {
            "data_id": str(self.data_id),
            "data_location": self.data_location,
            "classification_level": self.classification_level,
            "sensitivity_tags": self.sensitivity_tags,
            "classification_confidence": float(self.classification_confidence)
            if self.classification_confidence is not None
            else None,
            "classified_at": self.classified_at.isoformat()
            if self.classified_at
            else None,
            "classified_by": str(self.classified_by),
            "tenant_id": str(self.tenant_id),
        }


class ConsentRecord(Base):
    """ORM model for `consent_records` table."""

    __tablename__ = "consent_records"

    consent_id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    data_subject_id = Column(UUID_TYPE, nullable=False)
    purpose = Column(String(255), nullable=False)
    legal_basis = Column(String(50), nullable=False)
    granted_at = Column(TIMESTAMP_TYPE, nullable=False)
    granted_through = Column(String(100), nullable=False)
    withdrawal_at = Column(TIMESTAMP_TYPE, nullable=True)
    version = Column(String(50), nullable=False)
    tenant_id = Column(UUID_TYPE, nullable=False)

    __table_args__ = (
        Index(
            "idx_consent_records_consent_subject",
            "consent_id",
            "data_subject_id",
            unique=True,
        ),
        Index(
            "idx_consent_subject_purpose",
            "data_subject_id",
            "purpose",
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable representation."""
        return {
            "consent_id": str(self.consent_id),
            "data_subject_id": str(self.data_subject_id),
            "purpose": self.purpose,
            "legal_basis": self.legal_basis,
            "granted_at": self.granted_at.isoformat()
            if self.granted_at
            else None,
            "granted_through": self.granted_through,
            "withdrawal_at": self.withdrawal_at.isoformat()
            if self.withdrawal_at
            else None,
            "version": self.version,
            "tenant_id": str(self.tenant_id),
        }


class DataLineage(Base):
    """ORM model for `data_lineage` table."""

    __tablename__ = "data_lineage"

    lineage_id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    source_data_id = Column(UUID_TYPE, nullable=False)
    target_data_id = Column(UUID_TYPE, nullable=False)
    transformation_type = Column(String(100), nullable=False)
    transformation_details = Column(JSON_TYPE, nullable=True)
    processed_at = Column(TIMESTAMP_TYPE, nullable=False)
    processed_by = Column(UUID_TYPE, nullable=False)
    tenant_id = Column(UUID_TYPE, nullable=False)

    __table_args__ = (
        Index(
            "idx_data_lineage_lineage_tenant",
            "lineage_id",
            "tenant_id",
            unique=True,
        ),
        Index(
            "idx_lineage_source_transformation",
            "source_data_id",
            "transformation_type",
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable representation."""
        return {
            "lineage_id": str(self.lineage_id),
            "source_data_id": str(self.source_data_id),
            "target_data_id": str(self.target_data_id),
            "transformation_type": self.transformation_type,
            "transformation_details": self.transformation_details,
            "processed_at": self.processed_at.isoformat()
            if self.processed_at
            else None,
            "processed_by": str(self.processed_by),
            "tenant_id": str(self.tenant_id),
        }


class RetentionPolicy(Base):
    """ORM model for `retention_policies` table."""

    __tablename__ = "retention_policies"

    policy_id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    data_category = Column(String(100), nullable=False)
    retention_period_months = Column(Integer, nullable=False)
    legal_hold = Column(Boolean, nullable=False, default=False)
    auto_delete = Column(Boolean, nullable=False, default=True)
    regulatory_basis = Column(String(255), nullable=True)
    tenant_id = Column(UUID_TYPE, nullable=False)

    __table_args__ = (
        Index(
            "idx_retention_category_tenant",
            "data_category",
            "tenant_id",
        ),
        *(
            [
                Index(
                    "idx_regulatory_basis_trgm",
                    "regulatory_basis",
                    postgresql_using="gin",
                    postgresql_ops={"regulatory_basis": "gin_trgm_ops"},
                )
            ]
            if HAS_POSTGRES
            else []
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return serializable representation."""
        return {
            "policy_id": str(self.policy_id),
            "data_category": self.data_category,
            "retention_period_months": self.retention_period_months,
            "legal_hold": bool(self.legal_hold),
            "auto_delete": bool(self.auto_delete),
            "regulatory_basis": self.regulatory_basis,
            "tenant_id": str(self.tenant_id),
        }
