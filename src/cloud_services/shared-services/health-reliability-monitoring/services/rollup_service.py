"""
Roll-up service for Health & Reliability Monitoring.

Aggregates component-level snapshots into plane + tenant views with dependency awareness.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..database import models as db_models
from ..models import HealthSnapshot, PlaneHealthView, TenantHealthView


class RollupService:
    """Provides aggregation utilities for tenant and plane queries."""

    _state_priority = {"FAILED": 3, "DEGRADED": 2, "UNKNOWN": 1, "OK": 0}

    def __init__(self, session: Session) -> None:
        self._session = session

    def latest_component_states(self) -> Dict[str, HealthSnapshot]:
        """Return latest snapshot per component."""
        stmt = (
            select(db_models.HealthSnapshot)
            .order_by(db_models.HealthSnapshot.component_id, db_models.HealthSnapshot.evaluated_at.desc())
        )
        snapshots: Dict[str, HealthSnapshot] = {}
        for row in self._session.scalars(stmt):
            if row.component_id in snapshots:
                continue
            snapshots[row.component_id] = HealthSnapshot(
                snapshot_id=row.snapshot_id,
                component_id=row.component_id,
                tenant_id=row.tenant_id,
                plane=row.plane,
                environment=row.environment,
                state=row.state,  # type: ignore[arg-type]
                reason_code=row.reason_code,
                metrics_summary=row.metrics_summary,
                slo_state=row.slo_state,  # type: ignore[arg-type]
                policy_version=row.policy_version,
                evaluated_at=row.evaluated_at,
            )
        if snapshots:
            self._apply_dependency_penalties(snapshots)
        return snapshots

    def _apply_dependency_penalties(self, snapshots: Dict[str, HealthSnapshot]) -> None:
        """Propagate critical dependency failures into component states."""
        stmt = select(db_models.Component).options(selectinload(db_models.Component.dependencies))
        priority = self._state_priority
        for component in self._session.scalars(stmt):
            if not component.dependencies:
                continue
            current = snapshots.get(component.component_id)
            if not current:
                continue
            for dep in component.dependencies:
                dep_snapshot = snapshots.get(dep.dependency_id)
                if not dep_snapshot and dep.critical:
                    snapshots[component.component_id] = current.model_copy(
                        update={
                            "state": "UNKNOWN",
                            "reason_code": f"dependency_unknown:{dep.dependency_id}",
                        }
                    )
                    break
                if dep_snapshot and dep.critical and priority[dep_snapshot.state] > priority[current.state]:
                    snapshots[component.component_id] = current.model_copy(
                        update={
                            "state": dep_snapshot.state,
                            "reason_code": f"dependency_{dep_snapshot.state.lower()}:{dep.dependency_id}",
                        }
                    )
                    break

    def tenant_view(self, tenant_id: str) -> TenantHealthView:
        """Build tenant view for GET /v1/health/tenants/{tenant_id}."""
        snapshots = [
            snap
            for snap in self.latest_component_states().values()
            if snap.tenant_id in (tenant_id, None)
        ]
        counts = Counter(snap.state for snap in snapshots)
        plane_states: Dict[str, str] = {}
        for snap in snapshots:
            current = plane_states.get(snap.plane)
            if not current or self._state_priority[snap.state] > self._state_priority[current]:
                plane_states[snap.plane] = snap.state

        return TenantHealthView(
            tenant_id=tenant_id,
            plane_states=plane_states,
            counts={
                "OK": counts.get("OK", 0),
                "DEGRADED": counts.get("DEGRADED", 0),
                "FAILED": counts.get("FAILED", 0),
                "UNKNOWN": counts.get("UNKNOWN", 0),
            },
            error_budget={},
            updated_at=datetime.utcnow(),
        )

    def plane_view(self, plane: str, environment: str) -> PlaneHealthView:
        """Build plane view for GET /v1/health/planes/{plane}/{environment}."""
        snapshots = [
            snap
            for snap in self.latest_component_states().values()
            if snap.plane == plane and snap.environment == environment
        ]
        state = "UNKNOWN"
        for snap in snapshots:
            if self._state_priority[snap.state] > self._state_priority[state]:
                state = snap.state

        breakdown: Dict[str, List[str]] = defaultdict(list)
        for snap in snapshots:
            breakdown[snap.state].append(snap.component_id)

        return PlaneHealthView(
            plane=plane,
            environment=environment,
            state=state,
            component_breakdown=breakdown,
            updated_at=datetime.utcnow(),
        )

