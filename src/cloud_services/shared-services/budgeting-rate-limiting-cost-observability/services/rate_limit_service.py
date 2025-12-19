"""
Rate-Limiting Service for EPC-13 (Budgeting, Rate-Limiting & Cost Observability).

What: Implements rate limiting with multiple algorithms (token bucket, leaky bucket, fixed window, sliding window log)
Why: Provides dynamic rate limiting per PRD lines 123-188
Reads/Writes: Reads/writes rate limit policies and usage to database and Redis
Contracts: Rate limiting API per PRD
Risks: Race conditions, algorithm selection errors, Redis unavailability
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.models import RateLimitPolicy, RateLimitUsage
from ..dependencies import MockM29DataPlane
from ..utils.cache import CacheManager
from ..utils.transactions import serializable_transaction

logger = logging.getLogger(__name__)

# Priority multipliers per PRD lines 174-178
PRIORITY_MULTIPLIERS = {
    "critical": 2.0,
    "high": 1.5,
    "normal": 1.0,
    "low": 0.5
}


class RateLimitService:
    """
    Rate-Limiting Service per M35 PRD Functional Components section 2.

    Handles: Rate limit CRUD, algorithm selection, enforcement, dynamic adjustment.
    """

    def __init__(
        self,
        db: Session,
        redis_client=None,
        data_plane: Optional[MockM29DataPlane] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize rate limit service.

        Args:
            db: Database session
            redis_client: Redis client for distributed rate limiting (optional)
            data_plane: M29 data plane for caching state (optional)
            cache_manager: Cache manager for rate limit data (optional)
        """
        self.db = db
        self.redis = redis_client  # Would be Redis client in production
        self.data_plane = data_plane
        self.cache_manager = cache_manager
        self._local_cache: Dict[str, Any] = {}
        self._policy_cache: Dict[Tuple[str, str], RateLimitPolicy] = {}

    def _now(self) -> datetime:
        """Return current UTC time. Extracted for easier testing."""
        return datetime.utcnow()

    def _cache_get(self, key: str) -> Optional[Any]:
        if self.cache_manager:
            return self.cache_manager.get(key)
        if self.data_plane:
            return self.data_plane.cache_get(key)
        return self._local_cache.get(key)

    def _cache_set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if self.cache_manager:
            self.cache_manager.set(key, value, ttl_seconds=ttl_seconds)
        elif self.data_plane:
            self.data_plane.cache_set(key, value, ttl_seconds=ttl_seconds)
        else:
            self._local_cache[key] = value

    def _select_algorithm(self, policy: RateLimitPolicy) -> str:
        """
        Select rate limiting algorithm per PRD lines 161-167.

        Args:
            policy: Rate limit policy

        Returns:
            Algorithm name
        """
        if policy.burst_capacity:
            return "token_bucket"
        elif policy.algorithm == "leaky_bucket":
            return "leaky_bucket"
        elif policy.algorithm == "fixed_window":
            return "fixed_window"
        elif policy.algorithm == "sliding_window_log":
            return "sliding_window_log"
        else:
            return "token_bucket"  # Default

    def _apply_priority_multiplier(
        self,
        limit_value: int,
        priority: Optional[str]
    ) -> int:
        """
        Apply priority-based scaling per PRD lines 172-178.

        Args:
            limit_value: Base limit value
            priority: Request priority

        Returns:
            Adjusted limit value
        """
        if not priority:
            return limit_value

        multiplier = PRIORITY_MULTIPLIERS.get(priority, 1.0)
        return int(limit_value * multiplier)

    def _parse_iso_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _apply_time_of_day_adjustment(self, overrides: Dict[str, Any]) -> float:
        adjustments = overrides.get("time_of_day_adjustments") or []
        if not adjustments:
            return 1.0
        current_hour = self._now().hour
        for adjustment in adjustments:
            start_hour = int(adjustment.get("start_hour", 0))
            end_hour = int(adjustment.get("end_hour", 24))
            multiplier = float(adjustment.get("multiplier", 1.0))
            if start_hour == end_hour:
                continue
            if start_hour < end_hour:
                if start_hour <= current_hour < end_hour:
                    return multiplier
            else:
                if current_hour >= start_hour or current_hour < end_hour:
                    return multiplier
        return 1.0

    def _calculate_recent_utilization(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        window_seconds: int
    ) -> Optional[float]:
        lookback_start = self._now() - timedelta(seconds=window_seconds)
        usage_rows = self.db.query(RateLimitUsage).filter(
            and_(
                RateLimitUsage.policy_id == policy.policy_id,
                RateLimitUsage.resource_key == resource_key,
                RateLimitUsage.window_start >= lookback_start
            )
        ).all()
        if not usage_rows:
            return None
        total_requests = sum(row.current_count for row in usage_rows)
        window_count = len(usage_rows)
        capacity = policy.limit_value * window_count
        if capacity <= 0:
            return None
        return float(total_requests / capacity)

    def _apply_usage_pattern_adjustment(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        overrides: Dict[str, Any]
    ) -> float:
        config = overrides.get("usage_pattern_analysis")
        if not config:
            return 1.0
        window_seconds = int(config.get("window_seconds", policy.time_window_seconds * 6))
        utilization = self._calculate_recent_utilization(policy, resource_key, window_seconds)
        if utilization is None:
            return 1.0
        high_threshold = float(config.get("high_utilization_threshold", 0.9))
        low_threshold = float(config.get("low_utilization_threshold", 0.5))
        scale_down = float(config.get("scale_down_multiplier", 0.8))
        scale_up = float(config.get("scale_up_multiplier", 1.2))
        if utilization >= high_threshold:
            return scale_down
        if utilization <= low_threshold:
            return scale_up
        return 1.0

    def _apply_emergency_multiplier(self, overrides: Dict[str, Any]) -> float:
        emergency = overrides.get("emergency_capacity")
        if not emergency or not emergency.get("enabled"):
            return 1.0
        expires_at = self._parse_iso_datetime(emergency.get("expires_at"))
        if expires_at and expires_at < self._now():
            return 1.0
        duration_seconds = emergency.get("duration_seconds")
        started_at = self._parse_iso_datetime(emergency.get("started_at"))
        if duration_seconds and started_at:
            if started_at + timedelta(seconds=int(duration_seconds)) < self._now():
                return 1.0
        return float(emergency.get("multiplier", 1.0))

    def _compute_dynamic_multiplier(
        self,
        policy: RateLimitPolicy,
        resource_key: str
    ) -> float:
        overrides = policy.overrides or {}
        multiplier = 1.0
        multiplier *= self._apply_time_of_day_adjustment(overrides)
        multiplier *= self._apply_usage_pattern_adjustment(policy, resource_key, overrides)
        multiplier *= self._apply_emergency_multiplier(overrides)
        return max(0.1, multiplier)

    def _effective_limits(
        self,
        policy: RateLimitPolicy,
        priority: Optional[str],
        resource_key: str
    ) -> Tuple[int, int]:
        dynamic_multiplier = self._compute_dynamic_multiplier(policy, resource_key)
        base_limit = max(1, int(policy.limit_value * dynamic_multiplier))
        prioritized_limit = max(1, self._apply_priority_multiplier(base_limit, priority))
        capacity = prioritized_limit + (policy.burst_capacity or 0)
        return prioritized_limit, capacity

    def _policy_cache_key(self, tenant_id: str, resource_type: str) -> Tuple[str, str]:
        return tenant_id, resource_type

    def _get_policy_cached(self, tenant_id: str, resource_type: str) -> Optional[RateLimitPolicy]:
        cache_key = self._policy_cache_key(tenant_id, resource_type)
        cached = self._policy_cache.get(cache_key)
        if cached:
            return cached

        policy = self.db.query(RateLimitPolicy).filter(
            and_(
                RateLimitPolicy.tenant_id == uuid.UUID(tenant_id),
                RateLimitPolicy.resource_type == resource_type
            )
        ).first()

        if policy:
            self._policy_cache[cache_key] = policy
        return policy

    def _invalidate_policy_cache(self, policy: RateLimitPolicy) -> None:
        cache_key = self._policy_cache_key(str(policy.tenant_id), policy.resource_type)
        self._policy_cache.pop(cache_key, None)

    def _record_usage(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        now: datetime,
        increment: int
    ) -> None:
        if increment <= 0:
            return
        window_seconds = policy.time_window_seconds
        window_start_ts = int(now.timestamp() // window_seconds) * window_seconds
        window_start = datetime.utcfromtimestamp(window_start_ts)
        window_end = window_start + timedelta(seconds=window_seconds)
        # Use SERIALIZABLE transaction isolation for rate limit usage updates per PRD
        with serializable_transaction(self.db):
            usage = self.db.query(RateLimitUsage).filter(
                and_(
                    RateLimitUsage.policy_id == policy.policy_id,
                    RateLimitUsage.resource_key == resource_key,
                    RateLimitUsage.window_start == window_start
                )
            ).first()
            if not usage:
                usage = RateLimitUsage(
                    usage_id=uuid.uuid4(),
                    policy_id=policy.policy_id,
                    tenant_id=policy.tenant_id,
                    resource_key=resource_key,
                    window_start=window_start,
                    window_end=window_end,
                    current_count=0,
                    last_request_at=now
                )
                self.db.add(usage)
            usage.current_count += increment
            usage.last_request_at = now
            # Transaction helper commits automatically

    def _token_bucket_check(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        request_count: int,
        priority: Optional[str] = None
    ) -> Tuple[bool, int, datetime]:
        """
        Token bucket algorithm per PRD lines 132-139.

        Args:
            policy: Rate limit policy
            resource_key: Resource key
            request_count: Request count
            priority: Request priority

        Returns:
            Tuple of (allowed, remaining_requests, reset_time, effective_limit)
        """
        now = self._now()
        window_start = now.replace(second=0, microsecond=0)
        window_end = window_start + timedelta(seconds=policy.time_window_seconds)

        # Get or create usage record
        usage = self.db.query(RateLimitUsage).filter(
            and_(
                RateLimitUsage.policy_id == policy.policy_id,
                RateLimitUsage.resource_key == resource_key,
                RateLimitUsage.window_start == window_start
            )
        ).first()

        if not usage:
            usage = RateLimitUsage(
                usage_id=uuid.uuid4(),
                policy_id=policy.policy_id,
                tenant_id=policy.tenant_id,
                resource_key=resource_key,
                window_start=window_start,
                window_end=window_end,
                current_count=0,
                last_request_at=now
            )
            self.db.add(usage)

        effective_limit, capacity = self._effective_limits(policy, priority, resource_key)

        # Refill tokens based on elapsed time
        elapsed_seconds = (now - window_start).total_seconds()
        refill_rate = effective_limit / policy.time_window_seconds
        tokens_refilled = max(0, int(elapsed_seconds * refill_rate))
        available_tokens = min(
            capacity,
            tokens_refilled + max(0, capacity - usage.current_count)
        )

        # Check if request is allowed
        if available_tokens >= request_count:
            usage.current_count += request_count
            usage.last_request_at = now
            self.db.commit()
            remaining = available_tokens - request_count
            return True, remaining, window_end, effective_limit
        else:
            self.db.commit()
            return False, 0, window_end, effective_limit

    def _token_bucket_fast_check(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        request_count: int,
        priority: Optional[str] = None
    ) -> Tuple[bool, int, datetime]:
        """
        Hot path for token bucket that uses in-memory cache to avoid per-call DB traffic.
        """
        now = self._now()
        window_start = now.replace(second=0, microsecond=0)
        window_end = window_start + timedelta(seconds=policy.time_window_seconds)

        prioritized_limit = max(1, self._apply_priority_multiplier(policy.limit_value, priority))
        capacity = prioritized_limit + (policy.burst_capacity or 0)

        state_key = f"token:{policy.policy_id}:{resource_key}"
        state = self._cache_get(state_key) or {"window_start": window_start, "used": 0}
        if state.get("window_start") != window_start:
            state = {"window_start": window_start, "used": 0}

        used = int(state.get("used", 0))
        elapsed_seconds = max(0.0, (now - window_start).total_seconds())
        refill_rate = prioritized_limit / policy.time_window_seconds if policy.time_window_seconds else prioritized_limit
        tokens_refilled = max(0, int(elapsed_seconds * refill_rate))
        available_tokens = min(
            capacity,
            tokens_refilled + max(0, capacity - used)
        )

        allowed = available_tokens >= request_count
        if allowed:
            used += request_count
            remaining = available_tokens - request_count
        else:
            remaining = 0

        state["used"] = used
        ttl_seconds = policy.time_window_seconds or 60
        self._cache_set(state_key, state, ttl_seconds=ttl_seconds)
        return allowed, remaining, window_end, prioritized_limit

    def _fixed_window_check(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        request_count: int,
        priority: Optional[str] = None
    ) -> Tuple[bool, int, datetime, int]:
        """
        Fixed window algorithm per PRD lines 147-153.

        Args:
            policy: Rate limit policy
            resource_key: Resource key
            request_count: Request count
            priority: Request priority

        Returns:
            Tuple of (allowed, remaining_requests, reset_time, effective_limit)
        """
        now = self._now()
        # Align window to time_window_seconds boundaries
        window_seconds = policy.time_window_seconds
        window_start_ts = int(now.timestamp() // window_seconds) * window_seconds
        window_start = datetime.utcfromtimestamp(window_start_ts)
        window_end = window_start + timedelta(seconds=window_seconds)

        # Get or create usage record
        usage = self.db.query(RateLimitUsage).filter(
            and_(
                RateLimitUsage.policy_id == policy.policy_id,
                RateLimitUsage.resource_key == resource_key,
                RateLimitUsage.window_start == window_start
            )
        ).first()

        if not usage:
            usage = RateLimitUsage(
                usage_id=uuid.uuid4(),
                policy_id=policy.policy_id,
                tenant_id=policy.tenant_id,
                resource_key=resource_key,
                window_start=window_start,
                window_end=window_end,
                current_count=0,
                last_request_at=now
            )
            self.db.add(usage)

        # Apply dynamic adjustments + priority
        adjusted_limit, _ = self._effective_limits(policy, priority, resource_key)

        # Check if request is allowed
        if usage.current_count + request_count <= adjusted_limit:
            usage.current_count += request_count
            usage.last_request_at = now
            self.db.commit()
            remaining = adjusted_limit - usage.current_count
            return True, remaining, window_end, adjusted_limit
        else:
            self.db.commit()
            return False, 0, window_end, adjusted_limit

    def _leaky_bucket_check(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        request_count: int,
        priority: Optional[str] = None
    ) -> Tuple[bool, int, datetime, int]:
        now = self._now()
        effective_limit, capacity = self._effective_limits(policy, priority, resource_key)
        leak_rate = effective_limit / policy.time_window_seconds if policy.time_window_seconds else effective_limit
        state_key = f"leaky:{policy.policy_id}:{resource_key}"
        state = self._cache_get(state_key) or {"last_ts": now.timestamp(), "queue": 0.0}
        elapsed = max(0.0, now.timestamp() - state["last_ts"])
        leaked_amount = elapsed * leak_rate
        queue_level = max(0.0, state.get("queue", 0.0) - leaked_amount)
        allowed = queue_level + request_count <= capacity
        if allowed:
            queue_level += request_count
            remaining = max(0, int(capacity - queue_level))
            self._record_usage(policy, resource_key, now, request_count)
        else:
            remaining = 0
        state["queue"] = queue_level
        state["last_ts"] = now.timestamp()
        ttl_seconds = policy.time_window_seconds or 60
        self._cache_set(state_key, state, ttl_seconds=ttl_seconds)
        reset_seconds = (queue_level / leak_rate) if leak_rate else ttl_seconds
        reset_time = now + timedelta(seconds=reset_seconds)
        return allowed, remaining, reset_time, effective_limit

    def _sliding_window_check(
        self,
        policy: RateLimitPolicy,
        resource_key: str,
        request_count: int,
        priority: Optional[str] = None
    ) -> Tuple[bool, int, datetime, int]:
        now = self._now()
        effective_limit, _ = self._effective_limits(policy, priority, resource_key)
        ttl_seconds = policy.time_window_seconds or 60
        state_key = f"sliding:{policy.policy_id}:{resource_key}"
        entries: List[Dict[str, Any]] = self._cache_get(state_key) or []
        window_start = now - timedelta(seconds=ttl_seconds)
        filtered: List[Dict[str, Any]] = [
            entry for entry in entries
            if entry.get("ts", 0) >= window_start.timestamp()
        ]
        current_count = sum(int(entry.get("count", 0)) for entry in filtered)
        allowed = current_count + request_count <= effective_limit
        if allowed:
            filtered.append({"ts": now.timestamp(), "count": request_count})
            current_count += request_count
            remaining = max(0, effective_limit - current_count)
            self._record_usage(policy, resource_key, now, request_count)
        else:
            remaining = max(0, effective_limit - current_count)
        self._cache_set(state_key, filtered, ttl_seconds=ttl_seconds)
        if filtered:
            oldest_ts = min(entry["ts"] for entry in filtered)
            reset_time = datetime.utcfromtimestamp(oldest_ts) + timedelta(seconds=ttl_seconds)
        else:
            reset_time = now
        return allowed, remaining, reset_time, effective_limit

    def create_rate_limit_policy(
        self,
        tenant_id: str,
        scope_type: str,
        scope_id: str,
        resource_type: str,
        limit_value: int,
        time_window_seconds: int,
        algorithm: str,
        burst_capacity: Optional[int] = None,
        overrides: Optional[Dict[str, Any]] = None
    ) -> RateLimitPolicy:
        """
        Create rate limit policy per PRD.

        Args:
            tenant_id: Tenant identifier
            scope_type: Scope type
            scope_id: Scope identifier
            resource_type: Resource type
            limit_value: Limit value
            time_window_seconds: Time window in seconds
            algorithm: Algorithm name
            burst_capacity: Burst capacity
            overrides: Policy overrides

        Returns:
            Created rate limit policy
        """
        policy = RateLimitPolicy(
            policy_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            scope_type=scope_type,
            scope_id=uuid.UUID(scope_id),
            resource_type=resource_type,
            limit_value=limit_value,
            time_window_seconds=time_window_seconds,
            algorithm=algorithm,
            burst_capacity=burst_capacity,
            overrides=overrides or {}
        )

        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        cache_key = self._policy_cache_key(tenant_id, resource_type)
        self._policy_cache[cache_key] = policy

        logger.info(f"Created rate limit policy {policy.policy_id} for tenant {tenant_id}")
        return policy

    def get_rate_limit_policy(self, policy_id: str) -> Optional[RateLimitPolicy]:
        """
        Get rate limit policy by ID.

        Args:
            policy_id: Policy identifier

        Returns:
            Rate limit policy or None
        """
        return self.db.query(RateLimitPolicy).filter(
            RateLimitPolicy.policy_id == uuid.UUID(policy_id)
        ).first()

    def list_rate_limit_policies(
        self,
        tenant_id: str,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 100
    ) -> Tuple[list, int]:
        """
        List rate limit policies with filtering and pagination.

        Args:
            tenant_id: Tenant identifier
            scope_type: Optional scope type filter
            scope_id: Optional scope ID filter
            resource_type: Optional resource type filter
            page: Page number
            page_size: Page size

        Returns:
            Tuple of (policies list, total count)
        """
        query = self.db.query(RateLimitPolicy).filter(
            RateLimitPolicy.tenant_id == uuid.UUID(tenant_id)
        )

        if scope_type:
            query = query.filter(RateLimitPolicy.scope_type == scope_type)
        if scope_id:
            query = query.filter(RateLimitPolicy.scope_id == uuid.UUID(scope_id))
        if resource_type:
            query = query.filter(RateLimitPolicy.resource_type == resource_type)

        total_count = query.count()
        policies = query.offset((page - 1) * page_size).limit(page_size).all()

        return policies, total_count

    def check_rate_limit(
        self,
        tenant_id: str,
        resource_type: str,
        request_count: int = 1,
        priority: Optional[str] = None,
        resource_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check rate limit per PRD lines 131-188.

        Args:
            tenant_id: Tenant identifier
            resource_type: Resource type
            request_count: Request count
            priority: Request priority
            resource_key: Resource key

        Returns:
            Rate limit check result dictionary
        """
        # Find applicable policy
        policy = self._get_policy_cached(tenant_id, resource_type)

        if not policy:
            # No policy found - allow by default
            return {
                "allowed": True,
                "remaining_requests": 999999,
                "reset_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "limit_value": None,
                "retry_after": None,
                "policy_id": None
            }

        # Use resource_key or default
        resource_key = resource_key or f"{tenant_id}:{resource_type}"

        # Select algorithm
        algorithm = self._select_algorithm(policy)

        # Execute algorithm
        if algorithm == "token_bucket":
            fast_path = not policy.overrides
            if fast_path:
                allowed, remaining, reset_time, effective_limit = self._token_bucket_fast_check(
                    policy, resource_key, request_count, priority
                )
            else:
                allowed, remaining, reset_time, effective_limit = self._token_bucket_check(
                    policy, resource_key, request_count, priority
                )
        elif algorithm == "fixed_window":
            allowed, remaining, reset_time, effective_limit = self._fixed_window_check(
                policy, resource_key, request_count, priority
            )
        elif algorithm == "leaky_bucket":
            allowed, remaining, reset_time, effective_limit = self._leaky_bucket_check(
                policy, resource_key, request_count, priority
            )
        elif algorithm == "sliding_window_log":
            allowed, remaining, reset_time, effective_limit = self._sliding_window_check(
                policy, resource_key, request_count, priority
            )
        else:
            allowed, remaining, reset_time, effective_limit = self._fixed_window_check(
                policy, resource_key, request_count, priority
            )

        retry_after = None
        if not allowed:
            retry_after = int((reset_time - datetime.utcnow()).total_seconds())

        return {
            "allowed": allowed,
            "remaining_requests": remaining,
            "reset_time": reset_time.isoformat(),
            "limit_value": effective_limit,
            "retry_after": retry_after,
            "policy_id": str(policy.policy_id)
        }

    def update_rate_limit_policy(
        self,
        policy_id: str,
        **updates
    ) -> Optional[RateLimitPolicy]:
        """
        Update rate limit policy.

        Args:
            policy_id: Policy identifier
            **updates: Fields to update

        Returns:
            Updated policy or None
        """
        policy = self.get_rate_limit_policy(policy_id)
        if not policy:
            return None

        for key, value in updates.items():
            if hasattr(policy, key) and value is not None:
                if key in ["tenant_id", "scope_id"]:
                    setattr(policy, key, uuid.UUID(value))
                else:
                    setattr(policy, key, value)

        self.db.commit()
        self.db.refresh(policy)
        cache_key = self._policy_cache_key(str(policy.tenant_id), policy.resource_type)
        self._policy_cache[cache_key] = policy
        return policy

    def delete_rate_limit_policy(self, policy_id: str) -> bool:
        """
        Delete rate limit policy.

        Args:
            policy_id: Policy identifier

        Returns:
            True if deleted, False if not found
        """
        policy = self.get_rate_limit_policy(policy_id)
        if not policy:
            return False

        # Check if there's active usage
        usage = self.db.query(RateLimitUsage).filter(
            RateLimitUsage.policy_id == uuid.UUID(policy_id)
        ).first()

        if usage and usage.current_count > 0:
            raise ValueError("Cannot delete policy with active usage")

        self.db.delete(policy)
        self.db.commit()
        self._invalidate_policy_cache(policy)
        return True
