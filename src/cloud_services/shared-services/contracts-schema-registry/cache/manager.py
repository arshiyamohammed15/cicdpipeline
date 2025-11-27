"""
Cache manager for Contracts & Schema Registry.

What: Redis and in-memory cache with TTL management per PRD
Why: Provides performance optimization through caching
Reads/Writes: Reads/writes cache entries with TTL
Contracts: PRD caching strategy (schema: 1h, validation: 5m, compatibility: 24h)
Risks: Cache invalidation issues, memory exhaustion
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Per PRD cache TTLs
SCHEMA_CACHE_TTL = 3600  # 1 hour
VALIDATION_CACHE_TTL = 300  # 5 minutes
COMPATIBILITY_CACHE_TTL = 86400  # 24 hours

# Per PRD cache sizes
SCHEMA_CACHE_MAX_ENTRIES = 10000
VALIDATION_CACHE_MAX_ENTRIES = 50000
COMPATIBILITY_CACHE_MAX_ENTRIES = 1000


class LRUCache:
    """
    LRU cache implementation for in-memory caching.

    Per PRD: LRU eviction policy for schema cache.
    """

    def __init__(self, max_size: int):
        """
        Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry = self.cache[key]

            # Check expiration
            if entry.get('expires_at'):
                expires_at = datetime.fromisoformat(entry['expires_at'])
                if datetime.utcnow() > expires_at:
                    del self.cache[key]
                    return None

            return entry.get('value')
        return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional TTL in seconds
        """
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)  # Remove oldest (first item)

        expires_at = None
        if ttl_seconds:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()

        self.cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
        # Move to end (most recently used)
        self.cache.move_to_end(key)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


class CacheManager:
    """
    Cache manager with Redis support and in-memory fallback.

    Per PRD: Schema cache (1h TTL, 10k entries), validation cache (5m TTL, 50k entries),
             compatibility cache (24h TTL, 1k entries).
    """

    def __init__(self):
        """Initialize cache manager."""
        self.redis_client = None
        self.use_redis = False

        # Try to connect to Redis
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                import redis
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                self.use_redis = True
                logger.info("Connected to Redis cache")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory cache: {e}")

        # In-memory caches with LRU eviction
        self.schema_cache = LRUCache(SCHEMA_CACHE_MAX_ENTRIES)
        self.validation_cache = LRUCache(VALIDATION_CACHE_MAX_ENTRIES)
        self.compatibility_cache = LRUCache(COMPATIBILITY_CACHE_MAX_ENTRIES)

    def _make_key(self, prefix: str, *args) -> str:
        """
        Create cache key from prefix and arguments.

        Args:
            prefix: Key prefix
            *args: Key components

        Returns:
            Cache key string
        """
        key_str = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """
        Get schema from cache.

        Args:
            schema_id: Schema identifier

        Returns:
            Cached schema or None
        """
        key = self._make_key("schema", schema_id)

        if self.use_redis:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")

        return self.schema_cache.get(key)

    def set_schema(self, schema_id: str, schema: Dict[str, Any]) -> None:
        """
        Set schema in cache.

        Args:
            schema_id: Schema identifier
            schema: Schema data
        """
        key = self._make_key("schema", schema_id)

        if self.use_redis:
            try:
                self.redis_client.setex(
                    key,
                    SCHEMA_CACHE_TTL,
                    json.dumps(schema)
                )
            except Exception as e:
                logger.error(f"Redis set failed: {e}")

        self.schema_cache.set(key, schema, SCHEMA_CACHE_TTL)

    def get_validation(self, schema_id: str, data_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get validation result from cache.

        Args:
            schema_id: Schema identifier
            data_hash: Hash of data being validated

        Returns:
            Cached validation result or None
        """
        key = self._make_key("validation", schema_id, data_hash)

        if self.use_redis:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")

        return self.validation_cache.get(key)

    def set_validation(self, schema_id: str, data_hash: str, result: Dict[str, Any]) -> None:
        """
        Set validation result in cache.

        Args:
            schema_id: Schema identifier
            data_hash: Hash of data being validated
            result: Validation result
        """
        key = self._make_key("validation", schema_id, data_hash)

        if self.use_redis:
            try:
                self.redis_client.setex(
                    key,
                    VALIDATION_CACHE_TTL,
                    json.dumps(result)
                )
            except Exception as e:
                logger.error(f"Redis set failed: {e}")

        self.validation_cache.set(key, result, VALIDATION_CACHE_TTL)

    def get_compatibility(self, source_schema_id: str, target_schema_id: str) -> Optional[Dict[str, Any]]:
        """
        Get compatibility check result from cache.

        Args:
            source_schema_id: Source schema identifier
            target_schema_id: Target schema identifier

        Returns:
            Cached compatibility result or None
        """
        key = self._make_key("compatibility", source_schema_id, target_schema_id)

        if self.use_redis:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")

        return self.compatibility_cache.get(key)

    def set_compatibility(
        self,
        source_schema_id: str,
        target_schema_id: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Set compatibility check result in cache.

        Args:
            source_schema_id: Source schema identifier
            target_schema_id: Target schema identifier
            result: Compatibility result
        """
        key = self._make_key("compatibility", source_schema_id, target_schema_id)

        if self.use_redis:
            try:
                self.redis_client.setex(
                    key,
                    COMPATIBILITY_CACHE_TTL,
                    json.dumps(result)
                )
            except Exception as e:
                logger.error(f"Redis set failed: {e}")

        self.compatibility_cache.set(key, result, COMPATIBILITY_CACHE_TTL)

    def clear_all(self) -> None:
        """Clear all caches."""
        self.schema_cache.clear()
        self.validation_cache.clear()
        self.compatibility_cache.clear()

        if self.use_redis:
            try:
                # Clear Redis keys with our prefixes
                for prefix in ["schema:", "validation:", "compatibility:"]:
                    keys = self.redis_client.keys(f"{prefix}*")
                    if keys:
                        self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear failed: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "schema_cache_size": self.schema_cache.size(),
            "validation_cache_size": self.validation_cache.size(),
            "compatibility_cache_size": self.compatibility_cache.size(),
            "using_redis": self.use_redis
        }

        if self.use_redis:
            try:
                stats["redis_info"] = self.redis_client.info("memory")
            except Exception as e:
                logger.error(f"Failed to get Redis info: {e}")

        return stats
