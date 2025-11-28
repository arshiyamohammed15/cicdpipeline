"""
Eligibility, prioritisation, and fatigue controls per MMM PRD FR-7.

Per PRD NFR-2, FatigueManager state moved to Redis for horizontal scaling.
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional

from .models import MMMContext, Playbook

logger = logging.getLogger(__name__)

# Try to import Redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory fatigue state")

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
    """
    Enforces per-actor fatigue and quiet-hour suppression.

    Per PRD NFR-2, uses Redis for state storage to support horizontal scaling.
    Falls back to in-memory storage if Redis unavailable.
    """

    def __init__(self) -> None:
        self.redis_client: Optional[Any] = None
        self.use_redis = False
        # Fallback in-memory storage
        self.history: Dict[str, Deque[datetime]] = defaultdict(deque)

        if REDIS_AVAILABLE:
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
                # Test connection
                self.redis_client.ping()
                self.use_redis = True
                logger.info("FatigueManager using Redis for state storage")
            except Exception as exc:
                logger.warning("Redis unavailable, using in-memory fatigue state: %s", exc)
                self.redis_client = None
                self.use_redis = False

    def can_emit(self, tenant_id: str, actor_id: str, action_type: str, limits: FatigueLimits, now: datetime) -> bool:
        key = self._key(tenant_id, actor_id, action_type)

        if self.use_redis and self.redis_client:
            return self._can_emit_redis(key, limits, now)
        else:
            return self._can_emit_memory(key, limits, now)

    def _can_emit_redis(self, key: str, limits: FatigueLimits, now: datetime) -> bool:
        """Check fatigue using Redis."""
        try:
            # Get all timestamps from Redis (stored as sorted set)
            redis_key = f"mmm:fatigue:{key}"
            # Get timestamps from last 24 hours
            threshold = (now - timedelta(hours=24)).timestamp()
            timestamps = self.redis_client.zrangebyscore(
                redis_key, threshold, "+inf", withscores=True
            )

            # Count recent emissions
            recent_count = len(timestamps)
            if recent_count >= limits.max_per_day:
                return False

            # Check cooldown
            if timestamps:
                last_timestamp = timestamps[-1][1]
                last_emit = datetime.fromtimestamp(last_timestamp)
                if (now - last_emit) < timedelta(minutes=limits.cooldown_minutes):
                    return False

            # Check quiet hours
            quiet = limits.quiet_hours
            if quiet:
                start = int(quiet.get("start", 22))
                end = int(quiet.get("end", 6))
                if _hour_in_range(now.hour, start, end):
                    return False

            return True
        except Exception as exc:
            logger.warning("Redis fatigue check failed, falling back to memory: %s", exc)
            return self._can_emit_memory(key, limits, now)

    def _can_emit_memory(self, key: str, limits: FatigueLimits, now: datetime) -> bool:
        """Check fatigue using in-memory storage (fallback)."""
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
        """Record action emission with TTL-based expiration."""
        key = self._key(tenant_id, actor_id, action_type)

        if self.use_redis and self.redis_client:
            self._record_redis(key, timestamp)
        else:
            self._record_memory(key, timestamp)

    def _record_redis(self, key: str, timestamp: datetime) -> None:
        """Record in Redis with 24-hour TTL."""
        try:
            redis_key = f"mmm:fatigue:{key}"
            # Add timestamp to sorted set (score = timestamp)
            self.redis_client.zadd(redis_key, {str(timestamp.timestamp()): timestamp.timestamp()})
            # Set TTL to 24 hours (automatic expiration)
            self.redis_client.expire(redis_key, 86400)  # 24 hours in seconds
        except Exception as exc:
            logger.warning("Redis record failed, falling back to memory: %s", exc)
            self._record_memory(key, timestamp)

    def _record_memory(self, key: str, timestamp: datetime) -> None:
        """Record in in-memory storage (fallback)."""
        self.history[key].append(timestamp)

    def _key(self, tenant_id: str, actor_id: str, action_type: str) -> str:
        """Generate Redis key: mmm:fatigue:{tenant_id}:{actor_id}:{action_type}"""
        return f"{tenant_id}:{actor_id}:{action_type}"

    def _prune(self, window: Deque[datetime], now: datetime) -> None:
        """Prune old entries from in-memory window."""
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


