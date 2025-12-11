"""
SQLAlchemy ORM models for Budgeting, Rate-Limiting & Cost Observability (M35).

What: Database models matching PRD schema exactly (lines 322-420)
Why: Provides ORM layer for database operations
Reads/Writes: Reads/writes to PostgreSQL via SQLAlchemy
Contracts: PRD database schema specification
Risks: Model mismatch with PRD, constraint violations
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Boolean, Numeric, CheckConstraint,
    UniqueConstraint, Index, ForeignKey, Text
)
from sqlalchemy import DateTime, TIMESTAMP
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB as PGJSONB

DATABASE_URL = os.getenv("DATABASE_URL", "").lower()
USE_POSTGRES_TYPES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

if USE_POSTGRES_TYPES:
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


def _uuid_column(*args, **kwargs):
    """Helper to create UUID/GUID columns usable across PostgreSQL and SQLite."""
    return Column(_uuid_type(), *args, **kwargs)


Base = declarative_base()


class BudgetDefinition(Base):
    """
    Budget Definitions model matching PRD schema (lines 323-340).

    Per PRD: budget_definitions table with all constraints and indexes.
    """
    __tablename__ = "budget_definitions"

    budget_id = _uuid_column(primary_key=True, default=uuid.uuid4)
    tenant_id = _uuid_column(nullable=False, index=True)
    budget_name = Column(String(255), nullable=False)
    budget_type = Column(String(50), nullable=False)
    budget_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    period_type = Column(String(20), nullable=False)
    start_date = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=True) if USE_POSTGRES_TYPES else Column(DateTime, nullable=True)
    allocated_to_type = Column(String(50), nullable=False)
    allocated_to_id = _uuid_column(nullable=False)
    enforcement_action = Column(String(50), nullable=False)
    thresholds = Column(JSON_TYPE, nullable=True)
    notifications = Column(JSON_TYPE, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = _uuid_column(nullable=False)

    __table_args__ = (
        CheckConstraint("budget_amount > 0", name='budget_amount_positive'),
        CheckConstraint("end_date IS NULL OR end_date > start_date", name='budget_dates_valid'),
        CheckConstraint("budget_type IN ('tenant', 'project', 'user', 'feature')", name='budget_type_valid'),
        CheckConstraint("enforcement_action IN ('hard_stop', 'soft_limit', 'throttle', 'escalate')", name='enforcement_action_valid'),
        Index('idx_budget_definitions_tenant_id', 'tenant_id'),
        Index('idx_budget_definitions_allocated', 'tenant_id', 'allocated_to_type', 'allocated_to_id'),
        Index('idx_budget_definitions_period', 'start_date', 'end_date', postgresql_where=USE_POSTGRES_TYPES and Column('end_date').isnot(None)) if USE_POSTGRES_TYPES else None,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "budget_id": str(self.budget_id) if isinstance(self.budget_id, uuid.UUID) else self.budget_id,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "budget_name": self.budget_name,
            "budget_type": self.budget_type,
            "budget_amount": float(self.budget_amount) if self.budget_amount else None,
            "currency": self.currency,
            "period_type": self.period_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "allocated_to_type": self.allocated_to_type,
            "allocated_to_id": str(self.allocated_to_id) if isinstance(self.allocated_to_id, uuid.UUID) else self.allocated_to_id,
            "enforcement_action": self.enforcement_action,
            "thresholds": self.thresholds or {},
            "notifications": self.notifications or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": str(self.created_by) if isinstance(self.created_by, uuid.UUID) else self.created_by,
        }


class RateLimitPolicy(Base):
    """
    Rate Limit Policies model matching PRD schema (lines 342-355).

    Per PRD: rate_limit_policies table with all constraints and indexes.
    """
    __tablename__ = "rate_limit_policies"

    policy_id = _uuid_column(primary_key=True, default=uuid.uuid4)
    tenant_id = _uuid_column(nullable=False, index=True)
    scope_type = Column(String(50), nullable=False)
    scope_id = _uuid_column(nullable=False)
    resource_type = Column(String(100), nullable=False)
    limit_value = Column(Integer, nullable=False)
    time_window_seconds = Column(Integer, nullable=False)
    algorithm = Column(String(50), nullable=False)
    burst_capacity = Column(Integer, nullable=True)
    overrides = Column(JSON_TYPE, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("limit_value > 0", name='limit_value_positive'),
        CheckConstraint("time_window_seconds > 0", name='time_window_positive'),
        CheckConstraint("algorithm IN ('token_bucket', 'leaky_bucket', 'fixed_window', 'sliding_window_log')", name='algorithm_valid'),
        Index('idx_rate_limit_policies_tenant_id', 'tenant_id'),
        Index('idx_rate_limit_policies_scope', 'scope_type', 'scope_id'),
        Index('idx_rate_limit_policies_resource', 'resource_type', 'tenant_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "policy_id": str(self.policy_id) if isinstance(self.policy_id, uuid.UUID) else self.policy_id,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "scope_type": self.scope_type,
            "scope_id": str(self.scope_id) if isinstance(self.scope_id, uuid.UUID) else self.scope_id,
            "resource_type": self.resource_type,
            "limit_value": self.limit_value,
            "time_window_seconds": self.time_window_seconds,
            "algorithm": self.algorithm,
            "burst_capacity": self.burst_capacity,
            "overrides": self.overrides or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CostRecord(Base):
    """
    Cost Records model matching PRD schema (lines 357-373).

    Per PRD: cost_records table with all constraints and indexes.
    """
    __tablename__ = "cost_records"

    cost_id = _uuid_column(primary_key=True, default=uuid.uuid4)
    tenant_id = _uuid_column(nullable=False, index=True)
    resource_id = _uuid_column(nullable=False)
    resource_type = Column(String(100), nullable=False)
    cost_amount = Column(Numeric(15, 6), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    usage_quantity = Column(Numeric(15, 6), nullable=True)
    usage_unit = Column(String(50), nullable=True)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False, index=True) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False, index=True)
    attributed_to_type = Column(String(50), nullable=False)
    attributed_to_id = _uuid_column(nullable=False)
    service_name = Column(String(100), nullable=False)
    region = Column(String(50), nullable=True)
    tags = Column(JSON_TYPE, nullable=True)

    __table_args__ = (
        CheckConstraint("cost_amount >= 0", name='cost_amount_positive'),
        CheckConstraint("usage_quantity IS NULL OR usage_quantity >= 0", name='usage_quantity_positive'),
        Index('idx_cost_records_tenant_id', 'tenant_id'),
        Index('idx_cost_records_timestamp', 'timestamp', 'tenant_id', postgresql_ops={'timestamp': 'DESC'}) if USE_POSTGRES_TYPES else Index('idx_cost_records_timestamp', 'timestamp', 'tenant_id'),
        Index('idx_cost_records_attributed', 'attributed_to_type', 'attributed_to_id', 'tenant_id'),
        Index('idx_cost_records_resource_type', 'resource_type', 'attributed_to_type'),
        Index('idx_cost_records_service_region', 'service_name', 'region'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "cost_id": str(self.cost_id) if isinstance(self.cost_id, uuid.UUID) else self.cost_id,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "resource_id": str(self.resource_id) if isinstance(self.resource_id, uuid.UUID) else self.resource_id,
            "resource_type": self.resource_type,
            "cost_amount": float(self.cost_amount) if self.cost_amount else None,
            "currency": self.currency,
            "usage_quantity": float(self.usage_quantity) if self.usage_quantity else None,
            "usage_unit": self.usage_unit,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "attributed_to_type": self.attributed_to_type,
            "attributed_to_id": str(self.attributed_to_id) if isinstance(self.attributed_to_id, uuid.UUID) else self.attributed_to_id,
            "service_name": self.service_name,
            "region": self.region,
            "tags": self.tags or {},
        }


class QuotaAllocation(Base):
    """
    Quota Allocations model matching PRD schema (lines 375-392).

    Per PRD: quota_allocations table with all constraints and indexes.
    """
    __tablename__ = "quota_allocations"

    quota_id = _uuid_column(primary_key=True, default=uuid.uuid4)
    tenant_id = _uuid_column(nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    allocated_amount = Column(Numeric(15, 6), nullable=False)
    used_amount = Column(Numeric(15, 6), nullable=False, default=0)
    period_start = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    allocation_type = Column(String(50), nullable=False)
    max_burst_amount = Column(Numeric(15, 6), nullable=True)
    auto_renew = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("allocated_amount > 0", name='quota_allocated_amount_positive'),
        CheckConstraint("used_amount >= 0", name='quota_used_amount_positive'),
        CheckConstraint("used_amount <= allocated_amount + COALESCE(max_burst_amount, 0)", name='quota_used_within_limit'),
        CheckConstraint("period_end > period_start", name='quota_period_valid'),
        Index('idx_quota_allocations_tenant_id', 'tenant_id'),
        Index('idx_quota_allocations_period', 'period_start', 'period_end', 'tenant_id'),
        Index('idx_quota_allocations_resource', 'resource_type', 'tenant_id'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "quota_id": str(self.quota_id) if isinstance(self.quota_id, uuid.UUID) else self.quota_id,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "resource_type": self.resource_type,
            "allocated_amount": float(self.allocated_amount) if self.allocated_amount else None,
            "used_amount": float(self.used_amount) if self.used_amount else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "allocation_type": self.allocation_type,
            "max_burst_amount": float(self.max_burst_amount) if self.max_burst_amount else None,
            "auto_renew": self.auto_renew,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BudgetUtilization(Base):
    """
    Budget Utilization Tracking model matching PRD schema (lines 394-406).

    Per PRD: budget_utilization table with all constraints and indexes.
    """
    __tablename__ = "budget_utilization"

    utilization_id = _uuid_column(primary_key=True, default=uuid.uuid4)
    budget_id = _uuid_column(ForeignKey('budget_definitions.budget_id', ondelete='CASCADE'), nullable=False, index=True)
    tenant_id = _uuid_column(nullable=False)
    period_start = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    period_end = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    spent_amount = Column(Numeric(15, 2), nullable=False, default=0)
    last_updated = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('budget_id', 'period_start', 'period_end', name='uq_budget_utilization_period'),
        CheckConstraint("spent_amount >= 0", name='budget_utilization_spent_positive'),
        CheckConstraint("period_end > period_start", name='budget_utilization_period_valid'),
        Index('idx_budget_utilization_budget_id', 'budget_id'),
        Index('idx_budget_utilization_period', 'budget_id', 'period_start', 'period_end'),
        Index('idx_budget_utilization_tenant', 'tenant_id', 'period_start'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "utilization_id": str(self.utilization_id) if isinstance(self.utilization_id, uuid.UUID) else self.utilization_id,
            "budget_id": str(self.budget_id) if isinstance(self.budget_id, uuid.UUID) else self.budget_id,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "spent_amount": float(self.spent_amount) if self.spent_amount else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


class RateLimitUsage(Base):
    """
    Rate Limit Usage Counters model matching PRD schema (lines 408-420).

    Per PRD: rate_limit_usage table with all constraints and indexes.
    """
    __tablename__ = "rate_limit_usage"

    usage_id = _uuid_column(primary_key=True, default=uuid.uuid4)
    policy_id = _uuid_column(ForeignKey('rate_limit_policies.policy_id', ondelete='CASCADE'), nullable=False)
    tenant_id = _uuid_column(nullable=False)
    resource_key = Column(String(255), nullable=False)
    window_start = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    window_end = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    current_count = Column(Integer, nullable=False, default=0)
    last_request_at = Column(TIMESTAMP(timezone=True), nullable=True) if USE_POSTGRES_TYPES else Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('policy_id', 'resource_key', 'window_start', name='uq_rate_limit_usage'),
        CheckConstraint("current_count >= 0", name='rate_limit_usage_count_positive'),
        CheckConstraint("window_end > window_start", name='rate_limit_usage_window_valid'),
        Index('idx_rate_limit_usage_policy', 'policy_id', 'resource_key', 'window_start'),
        Index('idx_rate_limit_usage_window', 'window_start', 'window_end', postgresql_where=USE_POSTGRES_TYPES and Column('window_end') > datetime.utcnow()) if USE_POSTGRES_TYPES else None,
        Index('idx_rate_limit_usage_tenant', 'tenant_id', 'window_start'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "usage_id": str(self.usage_id) if isinstance(self.usage_id, uuid.UUID) else self.usage_id,
            "policy_id": str(self.policy_id) if isinstance(self.policy_id, uuid.UUID) else self.policy_id,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "resource_key": self.resource_key,
            "window_start": self.window_start.isoformat() if self.window_start else None,
            "window_end": self.window_end.isoformat() if self.window_end else None,
            "current_count": self.current_count,
            "last_request_at": self.last_request_at.isoformat() if self.last_request_at else None,
        }


class QuotaUsageHistory(Base):
    """
    Quota Usage History model matching PRD schema (lines 422-428).

    Per PRD: quota_usage_history table with all constraints and indexes.
    """
    __tablename__ = "quota_usage_history"

    usage_id = _uuid_column(primary_key=True, default=uuid.uuid4)
    quota_id = _uuid_column(ForeignKey('quota_allocations.quota_id', ondelete='CASCADE'), nullable=False, index=True)
    tenant_id = _uuid_column(nullable=False)
    usage_timestamp = Column(TIMESTAMP(timezone=True), nullable=False) if USE_POSTGRES_TYPES else Column(DateTime, nullable=False)
    usage_amount = Column(Numeric(15, 6), nullable=False)
    operation_type = Column(String(50), nullable=False)
    resource_id = _uuid_column(nullable=True)

    __table_args__ = (
        CheckConstraint("usage_amount >= 0", name='quota_usage_history_amount_positive'),
        Index('idx_quota_usage_history_quota_id', 'quota_id', 'usage_timestamp', postgresql_ops={'usage_timestamp': 'DESC'}) if USE_POSTGRES_TYPES else Index('idx_quota_usage_history_quota_id', 'quota_id', 'usage_timestamp'),
        Index('idx_quota_usage_history_tenant', 'tenant_id', 'usage_timestamp', postgresql_ops={'usage_timestamp': 'DESC'}) if USE_POSTGRES_TYPES else Index('idx_quota_usage_history_tenant', 'tenant_id', 'usage_timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "usage_id": str(self.usage_id) if isinstance(self.usage_id, uuid.UUID) else self.usage_id,
            "quota_id": str(self.quota_id) if isinstance(self.quota_id, uuid.UUID) else self.quota_id,
            "tenant_id": str(self.tenant_id) if isinstance(self.tenant_id, uuid.UUID) else self.tenant_id,
            "usage_timestamp": self.usage_timestamp.isoformat() if self.usage_timestamp else None,
            "usage_amount": float(self.usage_amount) if self.usage_amount else None,
            "operation_type": self.operation_type,
            "resource_id": str(self.resource_id) if isinstance(self.resource_id, uuid.UUID) else self.resource_id if self.resource_id else None,
        }
