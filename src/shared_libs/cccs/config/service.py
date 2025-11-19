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
        self._hash = self._compute_hash()

    def _compute_hash(self) -> str:
        blob = json.dumps(
            {
                "local": self._layers.local,
                "tenant": self._layers.tenant,
                "product": self._layers.product,
            },
            sort_keys=True,
        ).encode()
        digest = hashlib.sha256(blob).hexdigest()
        return f"sha256:{digest}"

    def get_config(self, key: str, scope: str | None = None, overrides: dict | None = None) -> ConfigResult:
        """
        Returns merged value, tracking source layers and warnings.
        
        Merge precedence: local → tenant → product (first match wins).
        """
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

        return ConfigResult(
            value=value,
            source_layers=tuple(source_layers),
            config_snapshot_hash=self._hash,
            warnings=tuple(warnings),
        )


