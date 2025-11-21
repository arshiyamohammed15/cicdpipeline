"""Policy-driven backup scheduler."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from .models import BackupPlan, duration_to_timedelta


class SchedulerError(RuntimeError):
    """Raised when schedules cannot be managed."""


class BackupScheduler:
    """Simplified scheduler that tracks next-run times for plans."""

    def __init__(self) -> None:
        self._entries: Dict[str, Dict[str, datetime | timedelta]] = {}

    def register_plan(self, plan: BackupPlan, now: datetime) -> None:
        interval = self._parse_interval(plan)
        self._entries[plan.plan_id] = {
            "next_run": now + interval,
            "interval": interval,
        }

    def remove_plan(self, plan_id: str) -> None:
        self._entries.pop(plan_id, None)

    def due(self, now: datetime) -> List[str]:
        due_ids: List[str] = []
        for plan_id, entry in self._entries.items():
            next_run = entry["next_run"]
            if isinstance(next_run, datetime) and now >= next_run:
                due_ids.append(plan_id)
        return due_ids

    def mark_executed(self, plan_id: str, now: datetime) -> None:
        if plan_id not in self._entries:
            msg = f"Plan {plan_id} not registered with scheduler"
            raise SchedulerError(msg)
        entry = self._entries[plan_id]
        interval = entry["interval"]
        if not isinstance(interval, timedelta):
            msg = f"Plan {plan_id} has invalid interval"
            raise SchedulerError(msg)
        entry["next_run"] = now + interval

    def _parse_interval(self, plan: BackupPlan) -> timedelta:
        try:
            return duration_to_timedelta(plan.backup_frequency)
        except ValueError as exc:
            msg = f"Plan {plan.plan_id} has invalid backup_frequency {plan.backup_frequency}"
            raise SchedulerError(msg) from exc

