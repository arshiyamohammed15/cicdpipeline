"""
Eligibility, prioritisation, and fatigue controls per MMM PRD FR-7.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional

from .models import MMMContext, Playbook

SEVERITY_SCORES = {
    "critical": 4,
    "high": 3,
    "warn": 2,
    "info": 1,
}


def _hour_in_range(hour: int, start: int, end: int) -> bool:
    if start == end:
        return True  # quiet hours disabled
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


class EligibilityEngine:
    """Determines whether a playbook should fire for the given context."""

    def is_eligible(self, playbook: Playbook, context: MMMContext) -> bool:
        conditions = playbook.conditions or []
        if not conditions:
            return True
        for condition in conditions:
            ctype = condition.get("type")
            value = condition.get("value")
            if ctype == "role" and value not in context.actor_roles:
                return False
            if ctype == "branch" and value and value != context.branch:
                return False
            if ctype == "actor_type" and value and value != context.actor_type.value:
                return False
        return True


@dataclass
class FatigueLimits:
    max_per_day: int = 5
    cooldown_minutes: int = 30
    quiet_hours: Optional[Dict[str, int]] = None


class FatigueManager:
    """Enforces per-actor fatigue and quiet-hour suppression."""

    def __init__(self) -> None:
        self.history: Dict[str, Deque[datetime]] = defaultdict(deque)

    def can_emit(self, tenant_id: str, actor_id: str, action_type: str, limits: FatigueLimits, now: datetime) -> bool:
        key = self._key(tenant_id, actor_id, action_type)
        window = self.history[key]
        self._prune(window, now)

        if len(window) >= limits.max_per_day:
            return False

        if window and (now - window[-1]) < timedelta(minutes=limits.cooldown_minutes):
            return False

        quiet = limits.quiet_hours
        if quiet:
            start = int(quiet.get("start", 22))
            end = int(quiet.get("end", 6))
            if _hour_in_range(now.hour, start, end):
                return False

        return True

    def record(self, tenant_id: str, actor_id: str, action_type: str, timestamp: datetime) -> None:
        key = self._key(tenant_id, actor_id, action_type)
        self.history[key].append(timestamp)

    def _key(self, tenant_id: str, actor_id: str, action_type: str) -> str:
        return f"{tenant_id}:{actor_id}:{action_type}"

    def _prune(self, window: Deque[datetime], now: datetime) -> None:
        threshold = now - timedelta(hours=24)
        while window and window[0] < threshold:
            window.popleft()


class PrioritizationEngine:
    """Scores and ranks actions by severity, policy priority, and fatigue pressure."""

    def score_playbook(self, playbook: Playbook, context: MMMContext, reverse_order_index: int) -> float:
        base_priority = float(playbook.limits.get("priority", 1)) if playbook.limits else 1.0
        severity_boost = 0.0
        for signal in context.recent_signals:
            severity = (signal.get("severity") or "").lower()
            severity_boost = max(severity_boost, SEVERITY_SCORES.get(severity, 0))
        tie_breaker = reverse_order_index * 0.0001
        return base_priority + severity_boost + tie_breaker

    def order(self, actions: List, score_lookup: Dict[str, float]) -> List:
        return sorted(
            actions,
            key=lambda action: score_lookup.get(action.action_id, 0),
            reverse=True,
        )


