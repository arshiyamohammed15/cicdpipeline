"""Observability stubs."""
from __future__ import annotations

from typing import Dict, Any
from datetime import datetime


class MetricsRegistry:
    def __init__(self) -> None:
        self.counters: Dict[str, int] = {}

    def inc(self, name: str, amount: int = 1) -> None:
        self.counters[name] = self.counters.get(name, 0) + amount


class StructuredLogger:
    def __init__(self) -> None:
        self.messages: list[Dict[str, Any]] = []

    def info(self, message: str, **kwargs: Any) -> None:
        self.messages.append({"level": "info", "message": message, "extra": kwargs})

    def warning(self, message: str, **kwargs: Any) -> None:
        self.messages.append({"level": "warning", "message": message, "extra": kwargs})

    def error(self, message: str, **kwargs: Any) -> None:
        self.messages.append({"level": "error", "message": message, "extra": kwargs})


class HealthChecker:
    def __init__(self) -> None:
        self.last_check = datetime.utcnow()

    def health(self) -> Dict[str, Any]:
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
