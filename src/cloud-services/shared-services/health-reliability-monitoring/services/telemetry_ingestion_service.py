"""
Telemetry ingestion service for Health & Reliability Monitoring.

Consumes metrics/probes/heartbeats payloads, enforces guardrails, and forwards
normalized frames to the evaluation engine queue.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta
from typing import Deque, List, Tuple

from ..config import load_settings
from ..models import TelemetryPayload
from ..telemetry.otel_pipeline import TelemetryGuards
from ..metrics import telemetry_ingested_total, queue_depth_gauge

logger = logging.getLogger(__name__)
settings = load_settings()


class TelemetryIngestionService:
    """Manages in-memory queues for telemetry payloads destined for the evaluator."""

    def __init__(self, guards: TelemetryGuards | None = None) -> None:
        self._guards = guards or TelemetryGuards()
        self._queue: Deque[TelemetryPayload] = deque()
        self._last_ingest_at: datetime | None = None
        self._lock = asyncio.Lock()

    async def ingest(self, payload: TelemetryPayload) -> None:
        """Validate and enqueue telemetry."""
        self._guards.validate_labels(payload.labels)
        self._guards.validate_metrics(payload.metrics)

        async with self._lock:
            self._queue.append(payload)
            self._last_ingest_at = datetime.utcnow()
            telemetry_ingested_total.labels(telemetry_type=payload.telemetry_type).inc()
            queue_depth_gauge.set(len(self._queue))
            if len(self._queue) > settings.telemetry.ingestion_batch_size * 2:
                logger.warning("Telemetry queue backlog detected", extra={"size": len(self._queue)})

    async def drain(self) -> List[TelemetryPayload]:
        """Drain up to batch size entries for evaluation."""
        batch: List[TelemetryPayload] = []
        async with self._lock:
            while self._queue and len(batch) < settings.telemetry.ingestion_batch_size:
                batch.append(self._queue.popleft())
            queue_depth_gauge.set(len(self._queue))
        return batch

    def last_ingest_age(self) -> float:
        """Return seconds since the last telemetry ingest, or infinity if none yet."""
        if not self._last_ingest_at:
            return float("inf")
        return (datetime.utcnow() - self._last_ingest_at).total_seconds()

