"""
Caching utilities for M35 per PRD lines 536-560.

What: Redis-based caching layer with TTLs and invalidation
Why: Performance optimization for frequently accessed data
Reads/Writes: Reads/writes to Redis cluster
Contracts: Caching strategy per PRD
Risks: Cache inconsistency, Redis unavailability
"""

import logging
from typing import Optional, Any, Dict
from datetime import timedelta

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Cache manager for M35 per PRD caching strategy.

    Handles: Rate limit data, budget definitions, cost aggregations.
    """

    def __init__(self, redis_client=None):
        """
        Initialize cache manager.

        Args:
            redis_client: Redis client (optional, uses in-memory fallback if None)
        """
        self.redis = redis_client
        self._memory_cache: Dict[str, tuple] = {}  # (value, expiry_time)

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if self.redis:
            try:
                return self.redis.get(key)
            except Exception as e:
                logger.warning(f"Redis get failed for key {key}: {e}")
                # Fallback to memory cache
                pass

        # In-memory fallback
        if key in self._memory_cache:
            value, expiry = self._memory_cache[key]
            from datetime import datetime
            if datetime.utcnow() < expiry:
                return value
            else:
                del self._memory_cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds

        Returns:
            True if successful
        """
        if self.redis:
            try:
                return self.redis.setex(key, ttl_seconds, value)
            except Exception as e:
                logger.warning(f"Redis set failed for key {key}: {e}")
                # Fallback to memory cache
                pass

        # In-memory fallback
        from datetime import datetime, timedelta
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._memory_cache[key] = (value, expiry)
        return True

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if self.redis:
            try:
                return bool(self.redis.delete(key))
            except Exception as e:
                logger.warning(f"Redis delete failed for key {key}: {e}")
                pass

        # In-memory fallback
        self._memory_cache.pop(key, None)
        return True

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern.

        Args:
            pattern: Key pattern (e.g., "budget:tenant:*")

        Returns:
            Number of keys invalidated
        """
        if self.redis:
            try:
                keys = list(self.redis.scan_iter(match=pattern))
                if keys:
                    return self.redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis pattern invalidation failed: {e}")
                pass

        # In-memory fallback
        from fnmatch import fnmatch
        count = 0
        keys_to_delete = [k for k in self._memory_cache.keys() if fnmatch(k, pattern)]
        for key in keys_to_delete:
            del self._memory_cache[key]
            count += 1
        return count

