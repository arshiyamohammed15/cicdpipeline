"""
SQLAlchemy ORM models for Configuration & Policy Management.

What: Database models matching PRD schema exactly (lines 128-186)
Why: Provides ORM layer for database operations
Reads/Writes: Reads/writes to PostgreSQL via SQLAlchemy
Contracts: PRD database schema specification
Risks: Model mismatch with PRD, constraint violations
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Text, ForeignKey, CheckConstraint,
    UniqueConstraint, Index
)
from sqlalchemy import DateTime, TIMESTAMP
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR

DATABASE_URL = os.getenv("DATABASE_URL", "").lower()
USE_POSTGRES_TYPES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

if USE_POSTGRES_TYPES:
    from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB as PGJSONB
    JSON_TYPE = PGJSONB

    def _uuid_type():
        return PGUUID(as_uuid=True)

else:
    JSON_TYPE = SQLiteJSON

    class GUIDType(TypeDecorator):
        """Platform-independent UUID string representation for SQLite."""

        impl = CHAR(36)
        cache_ok = True

        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            if isinstance(value, uuid.UUID):
                return str(value)
            return str(uuid.UUID(str(value)))

        def process_result_value(self, value, dialect):
            if value is None:
                return value
            return str(value)

    def _uuid_type():
        return GUIDType()


def _uuid_column(**kwargs):
    """
    Helper to create UUID/GUID columns usable across PostgreSQL and SQLite.
    """
    return Column(_uuid_type(), **kwargs)

Base = declarative_base()

class Policy(Base):
    """
    Policy model matching PRD policies table (lines 218-233).

    Per PRD: policies table with all constraints and indexes.
    """
    __tablename__ = "policies"

    # Primary key
    policy_id = _uuid_column(primary_key=True, default=uuid.uuid4)

    # Required fields per PRD
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    policy_type = Column(String(50), nullable=False)
    policy_definition = Column(JSON_TYPE, nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    scope = Column(JSON_TYPE, nullable=False)
    enforcement_level = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = _uuid_column(nullable=False)
    tenant_id = _uuid_column(nullable=False)

    # Optional metadata (renamed to avoid conflict with SQLAlchemy's metadata)
    metadata_json = Column(JSON_TYPE, nullable=True)

    # Constraints per PRD
    __table_args__ = (
        CheckConstraint(
            "policy_type IN ('security', 'compliance', 'operational', 'governance')",
            name='policies_policy_type_check'
        ),
        CheckConstraint(
            "status IN ('draft', 'review', 'approved', 'active', 'deprecated')",
            name='policies_status_check'
        ),
        CheckConstraint(
            "enforcement_level IN ('advisory', 'warning', 'enforcement')",
            name='policies_enforcement_level_check'
        ),
        # Primary indexes per PRD (lines 264)
        Index('idx_policies_policy_id_tenant_id', 'policy_id', 'tenant_id'),
        # Performance indexes per PRD (lines 268)
        Index('idx_policies_type_status_tenant', 'policy_type', 'status', 'tenant_id'),
        # Search indexes per PRD (lines 184)
        Index('idx_policies_definition_gin', 'policy_definition', postgresql_using='gin') if USE_POSTGRES_TYPES else None,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "policy_id": str(self.policy_id) if isinstance(self.policy_id, uuid.UUID) else self.policy_id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type,
            "policy_definition": self.policy_definition,
            "version": self.version,
            "status": self.status,
            "scope": self.scope,
            "enforcement_level": self.enforcement_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": str(self.created_by) if isinstance(self.created_by, uuid.UUID) else self.created_by,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "metadata": self.metadata_json or {}
        }


class Configuration(Base):
    """
    Configuration model matching PRD configurations table (lines 236-247).

    Per PRD: configurations table with all constraints and indexes.
    """
    __tablename__ = "configurations"

    # Primary key
    config_id = _uuid_column(primary_key=True, default=uuid.uuid4)

    # Required fields per PRD
    name = Column(String(255), nullable=False)
    config_type = Column(String(50), nullable=False)
    config_definition = Column(JSON_TYPE, nullable=False)
    version = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    deployed_at = Column(TIMESTAMP(timezone=True), nullable=True) if USE_POSTGRES_TYPES else Column(DateTime, nullable=True)
    deployed_by = _uuid_column(nullable=True)
    tenant_id = _uuid_column(nullable=False)
    environment = Column(String(50), nullable=False)

    # Constraints per PRD
    __table_args__ = (
        CheckConstraint(
            "config_type IN ('security', 'performance', 'feature', 'compliance')",
            name='configurations_config_type_check'
        ),
        CheckConstraint(
            "status IN ('draft', 'staging', 'active', 'deprecated')",
            name='configurations_status_check'
        ),
        CheckConstraint(
            "environment IN ('production', 'staging', 'development')",
            name='configurations_environment_check'
        ),
        # Primary indexes per PRD (lines 265)
        Index('idx_configurations_config_id_env_tenant', 'config_id', 'environment', 'tenant_id'),
        # Performance indexes per PRD (lines 269)
        Index('idx_configurations_type_status_env', 'config_type', 'status', 'environment'),
        # Search indexes per PRD (lines 185)
        Index('idx_configurations_definition_gin', 'config_definition', postgresql_using='gin') if USE_POSTGRES_TYPES else None,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "config_id": str(self.config_id) if isinstance(self.config_id, uuid.UUID) else self.config_id,
            "name": self.name,
            "config_type": self.config_type,
            "config_definition": self.config_definition,
            "version": self.version,
            "status": self.status,
            "deployed_at": self.deployed_at.isoformat() if self.deployed_at else None,
            "deployed_by": str(self.deployed_by) if self.deployed_by and isinstance(self.deployed_by, uuid.UUID) else (self.deployed_by if self.deployed_by else None),
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "environment": self.environment
        }


class GoldStandard(Base):
    """
    Gold Standard model matching PRD gold_standards table (lines 250-259).

    Per PRD: gold_standards table with all constraints and indexes.
    """
    __tablename__ = "gold_standards"

    # Primary key
    standard_id = _uuid_column(primary_key=True, default=uuid.uuid4)

    # Required fields per PRD
    name = Column(String(255), nullable=False)
    framework = Column(String(50), nullable=False)
    version = Column(String(50), nullable=False)
    control_definitions = Column(JSON_TYPE, nullable=False)
    compliance_rules = Column(JSON_TYPE, nullable=False)
    evidence_requirements = Column(JSON_TYPE, nullable=False)
    tenant_id = _uuid_column(nullable=False)

    # Constraints per PRD
    __table_args__ = (
        CheckConstraint(
            "framework IN ('soc2', 'gdpr', 'hipaa', 'nist', 'custom')",
            name='gold_standards_framework_check'
        ),
        # Primary indexes per PRD (lines 266)
        Index('idx_gold_standards_standard_id_framework_tenant', 'standard_id', 'framework', 'tenant_id'),
        # Performance indexes per PRD (lines 270)
        Index('idx_gold_standards_framework_version_tenant', 'framework', 'version', 'tenant_id'),
        # Search indexes per PRD (lines 186)
        Index('idx_gold_standards_control_definitions_gin', 'control_definitions', postgresql_using='gin') if USE_POSTGRES_TYPES else None,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "standard_id": str(self.standard_id) if isinstance(self.standard_id, uuid.UUID) else self.standard_id,
            "name": self.name,
            "framework": self.framework,
            "version": self.version,
            "control_definitions": self.control_definitions,
            "compliance_rules": self.compliance_rules,
            "evidence_requirements": self.evidence_requirements,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id
        }
