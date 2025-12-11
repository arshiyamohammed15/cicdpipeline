"""Normalization stub."""
from __future__ import annotations

from .models import SignalEnvelope


class NormalizationEngine:
    """No-op normalization for tests."""

    def __init__(self, schema_registry) -> None:
        self.schema_registry = schema_registry

    def normalize(self, signal: SignalEnvelope) -> SignalEnvelope:
        return signal
