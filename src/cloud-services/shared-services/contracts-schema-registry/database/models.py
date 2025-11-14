"""
SQLAlchemy ORM models for Contracts & Schema Registry.

What: Database models matching PRD schema exactly
Why: Provides ORM layer for database operations
Reads/Writes: Reads/writes to PostgreSQL via SQLAlchemy
Contracts: PRD database schema specification
Risks: Model mismatch with PRD, constraint violations
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, CheckConstraint,
    UniqueConstraint, Index, Text
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy import TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Schema(Base):
    """
    Schema model matching PRD schemas table.

    Per PRD: schemas table with all constraints and indexes.
    """
    __tablename__ = "schemas"

    # Primary key
    schema_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Required fields
    name = Column(String(255), nullable=False)
    namespace = Column(String(255), nullable=False)
    schema_type = Column(String(50), nullable=False)
    schema_definition = Column(JSONB, nullable=False) if hasattr(JSONB, '__init__') else Column(SQLiteJSON, nullable=False)
    version = Column(String(50), nullable=False)
    compatibility = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow) if hasattr(JSONB, '__init__') else Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) if hasattr(JSONB, '__init__') else Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    # Optional metadata (renamed to avoid SQLAlchemy reserved name)
    schema_metadata = Column('metadata', JSONB) if hasattr(JSONB, '__init__') else Column('metadata', SQLiteJSON)

    # Relationships
    contracts = relationship("Contract", back_populates="schema", cascade="all, delete-orphan")
    dependencies_as_parent = relationship(
        "SchemaDependency",
        foreign_keys="SchemaDependency.parent_schema_id",
        back_populates="parent_schema",
        cascade="all, delete-orphan"
    )
    dependencies_as_child = relationship(
        "SchemaDependency",
        foreign_keys="SchemaDependency.child_schema_id",
        back_populates="child_schema",
        cascade="all, delete-orphan"
    )
    analytics = relationship("SchemaAnalytics", back_populates="schema", cascade="all, delete-orphan")

    # Constraints per PRD
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', 'version', name='schemas_tenant_name_version_unique'),
        CheckConstraint(
            "schema_type IN ('json_schema', 'avro', 'protobuf')",
            name='schemas_schema_type_check'
        ),
        CheckConstraint(
            "compatibility IN ('backward', 'forward', 'full', 'none')",
            name='schemas_compatibility_check'
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'deprecated')",
            name='schemas_status_check'
        ),
        # Indexes per PRD
        Index('idx_schemas_type_status', 'schema_type', 'status'),
        Index('idx_schemas_tenant_status', 'tenant_id', 'status'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "schema_id": str(self.schema_id),
            "name": self.name,
            "namespace": self.namespace,
            "schema_type": self.schema_type,
            "schema_definition": self.schema_definition,
            "version": self.version,
            "compatibility": self.compatibility,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by),
            "tenant_id": str(self.tenant_id),
            "metadata": self.schema_metadata or {}
        }


class Contract(Base):
    """
    Contract model matching PRD contracts table.

    Per PRD: contracts table with all constraints and indexes.
    """
    __tablename__ = "contracts"

    # Primary key
    contract_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Required fields
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    schema_id = Column(UUID(as_uuid=True), ForeignKey('schemas.schema_id'), nullable=True)
    validation_rules = Column(JSONB, nullable=False) if hasattr(JSONB, '__init__') else Column(SQLiteJSON, nullable=False)
    enforcement_level = Column(String(20), nullable=False)
    violation_actions = Column(JSONB, nullable=False) if hasattr(JSONB, '__init__') else Column(SQLiteJSON, nullable=False)
    version = Column(String(50), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow) if hasattr(JSONB, '__init__') else Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) if hasattr(JSONB, '__init__') else Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)

    # Relationships
    schema = relationship("Schema", back_populates="contracts")

    # Constraints per PRD
    __table_args__ = (
        CheckConstraint(
            "type IN ('api', 'event', 'data')",
            name='contracts_type_check'
        ),
        CheckConstraint(
            "enforcement_level IN ('strict', 'warning', 'advisory')",
            name='contracts_enforcement_level_check'
        ),
        # Indexes per PRD
        Index('idx_contracts_schema_id', 'schema_id'),
        Index('idx_contracts_tenant_id', 'tenant_id'),
        Index('idx_contracts_type', 'type'),
        Index('idx_contracts_created_at', 'created_at'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "contract_id": str(self.contract_id),
            "name": self.name,
            "type": self.type,
            "schema_id": str(self.schema_id) if self.schema_id else None,
            "validation_rules": self.validation_rules,
            "enforcement_level": self.enforcement_level,
            "violation_actions": self.violation_actions,
            "version": self.version,
            "tenant_id": str(self.tenant_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by)
        }


class SchemaDependency(Base):
    """
    Schema dependency model matching PRD schema_dependencies table.

    Per PRD: schema_dependencies table for tracking schema relationships.
    """
    __tablename__ = "schema_dependencies"

    # Composite primary key
    parent_schema_id = Column(UUID(as_uuid=True), ForeignKey('schemas.schema_id'), primary_key=True)
    child_schema_id = Column(UUID(as_uuid=True), ForeignKey('schemas.schema_id'), primary_key=True)
    dependency_type = Column(String(50), nullable=False)

    # Relationships
    parent_schema = relationship("Schema", foreign_keys=[parent_schema_id], back_populates="dependencies_as_parent")
    child_schema = relationship("Schema", foreign_keys=[child_schema_id], back_populates="dependencies_as_child")

    # Indexes per PRD
    __table_args__ = (
        Index('idx_schema_deps_parent', 'parent_schema_id'),
        Index('idx_schema_deps_child', 'child_schema_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "parent_schema_id": str(self.parent_schema_id),
            "child_schema_id": str(self.child_schema_id),
            "dependency_type": self.dependency_type
        }


class SchemaAnalytics(Base):
    """
    Schema analytics model matching PRD schema_analytics table.

    Per PRD: schema_analytics table for storing aggregated metrics.
    """
    __tablename__ = "schema_analytics"

    # Primary key
    analytics_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Required fields
    schema_id = Column(UUID(as_uuid=True), ForeignKey('schemas.schema_id'), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    period = Column(String(20), nullable=False)
    period_start = Column(TIMESTAMP(timezone=True), nullable=False) if hasattr(JSONB, '__init__') else Column(DateTime, nullable=False)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False) if hasattr(JSONB, '__init__') else Column(DateTime, nullable=False)
    metrics = Column(JSONB, nullable=False) if hasattr(JSONB, '__init__') else Column(SQLiteJSON, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow) if hasattr(JSONB, '__init__') else Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    schema = relationship("Schema", back_populates="analytics")

    # Constraints per PRD
    __table_args__ = (
        UniqueConstraint('schema_id', 'tenant_id', 'period', 'period_start', name='schema_analytics_unique'),
        CheckConstraint(
            "period IN ('hourly', 'daily', 'weekly', 'monthly')",
            name='schema_analytics_period_check'
        ),
        # Indexes per PRD
        Index('idx_schema_analytics_schema_tenant', 'schema_id', 'tenant_id'),
        Index('idx_schema_analytics_period', 'period', 'period_start'),
        Index('idx_schema_analytics_tenant_period', 'tenant_id', 'period', 'period_start'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "analytics_id": str(self.analytics_id),
            "schema_id": str(self.schema_id),
            "tenant_id": str(self.tenant_id),
            "period": self.period,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
