"""Configuration & Feature Flags (CFFS) implementation."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, MutableMapping, Sequence

from ..types import ConfigLayers, ConfigResult


class ConfigService:
    """Merges local, tenant, and product configurations deterministically."""

    def __init__(self, layers: ConfigLayers):
        self._layers = layers
        # CR-041: Make hash computation lazy - compute on first access
        self._hash: str | None = None
        # CR-072: Cache config lookups
        self._config_cache: dict[str, ConfigResult] = {}
        self._cache_max_size = 1000

    def _compute_hash(self) -> str:
        """
        CR-041: Compute hash lazily and cache it.
        
        Computes a deterministic SHA-256 hash of the merged configuration layers.
        The hash is computed on first access and cached for subsequent calls.
        
        Returns:
            SHA-256 hash string prefixed with "sha256:"
        """
        if self._hash is None:
            blob = json.dumps(
                {
                    "local": self._layers.local,
                    "tenant": self._layers.tenant,
                    "product": self._layers.product,
                },
                sort_keys=True,
            ).encode()
            digest = hashlib.sha256(blob).hexdigest()
            self._hash = f"sha256:{digest}"
        return self._hash

    def get_config(self, key: str, scope: str | None = None, overrides: dict | None = None) -> ConfigResult:
        """
        Returns merged value, tracking source layers and warnings.
        
        Merge precedence: local → tenant → product (first match wins).
        """
        # CR-072: Check cache first
        cache_key = f"{key}:{scope}:{json.dumps(overrides or {}, sort_keys=True)}"
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]
        
        overrides = overrides or {}
        search_order: Sequence[tuple[str, MutableMapping[str, Any]]] = (
            ("local", self._layers.local),
            ("tenant", self._layers.tenant),
            ("product", self._layers.product),
        )
        value = overrides.get(key)
        source_layers: list[str] = []
        warnings: list[str] = []

        # Check overrides first
        if value is not None:
            source_layers.append("overrides")
        else:
            # Search in precedence order: local → tenant → product (first match wins)
            for name, layer in search_order:
                if scope and name != scope:
                    continue
                if key in layer:
                    value = layer[key]
                    source_layers.append(name)
                    break  # First match wins per precedence

        if value is None:
            warnings.append("config_gap")

        result = ConfigResult(
            value=value,
            source_layers=tuple(source_layers),
            config_snapshot_hash=self._compute_hash(),  # CR-041: Use lazy hash computation
            warnings=tuple(warnings),
        )
        
        # CR-072: Cache the result
        if len(self._config_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self._config_cache))
            del self._config_cache[oldest_key]
        self._config_cache[cache_key] = result
        
        return result


