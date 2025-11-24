"""
SLO tracking utilities for Health & Reliability Monitoring.

Calculates SLIs, burn rate, and persists status for API queries.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import PolicyClient
from ..models import SLOStatus
from ..database import models as db_models

logger = logging.getLogger(__name__)


class SLOService:
    """Provides SLO calculations based on telemetry roll-ups."""

    def __init__(self, session: Session, policy_client: PolicyClient) -> None:
        self._session = session
        self._policy_client = policy_client

    async def update_slo(
        self,
        component_id: str,
        slo_id: str,
        success_minutes: int,
        total_minutes: int,
    ) -> SLOStatus:
        """Update SLO posture given success/total minutes sample."""
        slo_definition = await self._policy_client.fetch_slo(slo_id)
        target_percentage = slo_definition["target_percentage"]
        error_budget_total = slo_definition["error_budget_minutes"]

        availability = (success_minutes / total_minutes) * 100 if total_minutes else 0
        error_minutes = max(total_minutes - success_minutes, 0)
        burn_rate = (error_minutes / error_budget_total) if error_budget_total else 0

        if availability >= target_percentage:
            state = "within_budget"
        elif burn_rate >= 1:
            state = "breached"
        else:
            state = "approaching"

        entity = db_models.SLOStatus(
            component_id=component_id,
            slo_id=slo_id,
            window=f"{slo_definition['window_days']}d",
            sli_values={"availability_pct": availability},
            error_budget_total_minutes=error_budget_total,
            error_budget_consumed_minutes=error_minutes,
            burn_rate=burn_rate,
            state=state,
        )
        self._session.add(entity)
        self._session.flush()

        return SLOStatus(
            component_id=component_id,
            slo_id=slo_id,
            window=entity.window,  # type: ignore[arg-type]
            sli_values=entity.sli_values,
            error_budget_total_minutes=entity.error_budget_total_minutes,
            error_budget_consumed_minutes=entity.error_budget_consumed_minutes,
            burn_rate=entity.burn_rate,
            state=entity.state,  # type: ignore[arg-type]
        )

    def latest_slo(self, component_id: str) -> Optional[SLOStatus]:
        """Fetch the latest SLO status for component."""
        stmt = (
            select(db_models.SLOStatus)
            .where(db_models.SLOStatus.component_id == component_id)
            .order_by(db_models.SLOStatus.updated_at.desc())
        )
        result = self._session.scalars(stmt).first()
        if not result:
            return None
        return SLOStatus(
            component_id=result.component_id,
            slo_id=result.slo_id,
            window=result.window,  # type: ignore[arg-type]
            sli_values=result.sli_values,
            error_budget_total_minutes=result.error_budget_total_minutes,
            error_budget_consumed_minutes=result.error_budget_consumed_minutes,
            burn_rate=result.burn_rate,
            state=result.state,  # type: ignore[arg-type]
        )

