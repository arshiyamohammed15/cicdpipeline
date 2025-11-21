"""Observability helpers for the BDR backend."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from .models import BackupStatus


class MetricsRegistry:
    """Minimal in-memory metrics collector."""

    def __init__(self) -> None:
        self._counters: Dict[str, Dict[str, int]] = {}
        self._gauges: Dict[str, Dict[str, float]] = {}

    def increment(self, metric: str, label: str, value: int = 1) -> None:
        labels = self._counters.setdefault(metric, {})
        labels[label] = labels.get(label, 0) + value

    def set_gauge(self, metric: str, label: str, value: float) -> None:
        labels = self._gauges.setdefault(metric, {})
        labels[label] = value

    def get_counter(self, metric: str, label: str) -> int:
        return self._counters.get(metric, {}).get(label, 0)

    def get_gauge(self, metric: str, label: str) -> float:
        return self._gauges.get(metric, {}).get(label, 0.0)


class StructuredLogger:
    """Simple structured logger capturing events for assertions."""

    def __init__(self) -> None:
        self._entries: List[dict] = []

    def info(self, message: str, **fields: object) -> None:
        self._entries.append(
            {
                "level": "INFO",
                "message": message,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    def error(self, message: str, **fields: object) -> None:
        self._entries.append(
            {
                "level": "ERROR",
                "message": message,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    @property
    def entries(self) -> List[dict]:
        return list(self._entries)

