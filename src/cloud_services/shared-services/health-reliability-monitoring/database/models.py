"""
SQLAlchemy models for the Health & Reliability Monitoring capability.

Captures Component registry, HealthSnapshot, and SLOStatus schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base."""


class Component(Base):
    """Monitored component definition."""

    __tablename__ = "health_reliability_monitoring_components"

    component_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    component_type: Mapped[str] = mapped_column(String(32), nullable=False)
    plane: Mapped[str] = mapped_column(String(32), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False, default="dev")
    tenant_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    metrics_profile: Mapped[List[str]] = mapped_column(JSON, default=list)
    health_policies: Mapped[List[str]] = mapped_column(JSON, default=list)
    slo_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_budget_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    owner_team: Mapped[Optional[str]] = mapped_column(String(255))
    documentation_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dependencies: Mapped[List["ComponentDependency"]] = relationship(
        "ComponentDependency",
        back_populates="component",
        cascade="all, delete-orphan",
    )


class ComponentDependency(Base):
    """Dependency edges for components."""

    __tablename__ = "health_reliability_monitoring_component_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[str] = mapped_column(
            String(128),
            ForeignKey("health_reliability_monitoring_components.component_id", ondelete="CASCADE"),
            nullable=False,
    )
    dependency_id: Mapped[str] = mapped_column(String(128), nullable=False)
    critical: Mapped[bool] = mapped_column(Boolean, default=True)

    component: Mapped[Component] = relationship("Component", back_populates="dependencies")


class HealthSnapshot(Base):
    """Persisted health evaluation."""

    __tablename__ = "health_reliability_monitoring_health_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    component_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("health_reliability_monitoring_components.component_id"), nullable=False
    )
    tenant_id: Mapped[Optional[str]] = mapped_column(String(64))
    plane: Mapped[str] = mapped_column(String(32), nullable=False)
    environment: Mapped[str] = mapped_column(String(32), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(128), nullable=False)
    metrics_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    slo_state: Mapped[Optional[str]] = mapped_column(String(32))
    policy_version: Mapped[Optional[str]] = mapped_column(String(64))
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class SLOStatus(Base):
    """Rolling SLO posture."""

    __tablename__ = "health_reliability_monitoring_slo_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    component_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    slo_id: Mapped[str] = mapped_column(String(64), nullable=False)
    window: Mapped[str] = mapped_column(String(8), nullable=False)
    sli_values: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    error_budget_total_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    error_budget_consumed_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    burn_rate: Mapped[Optional[float]] = mapped_column(Float)
    state: Mapped[str] = mapped_column(String(32), default="none")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

