"""
Background telemetry ingestion worker.

Continuously drains the telemetry queue and evaluates payload batches so that
Safe-to-Act decisions rely on fresh health snapshots even when ingestion flows
arrive via OTEL pipelines instead of the test harness endpoint.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from ..config import load_settings
from ..database.session import SessionLocal
from .evaluation_service import HealthEvaluationService
from .event_bus_service import EventBusService
from .slo_service import SLOService
from .telemetry_ingestion_service import TelemetryIngestionService
from ..dependencies import PolicyClient

logger = logging.getLogger(__name__)
settings = load_settings()


class TelemetryWorker:
    """Background worker that drains telemetry queues on a fixed cadence."""

    def __init__(
        self,
        telemetry_service: TelemetryIngestionService,
        policy_client: PolicyClient,
        event_bus: EventBusService,
    ) -> None:
        self._telemetry_service = telemetry_service
        self._policy_client = policy_client
        self._event_bus = event_bus
        self._stop_event: Optional[asyncio.Event] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the worker loop if not already running."""
        if self._task:
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(self._run(), name="health-reliability-monitoring-telemetry-worker")
        logger.info(
            "Started telemetry worker",
            extra={"interval_ms": settings.telemetry.ingestion_interval_ms},
        )

    async def stop(self) -> None:
        """Signal the worker to stop and await completion."""
        if not self._task or not self._stop_event:
            return
        self._stop_event.set()
        await self._task
        self._task = None
        self._stop_event = None
        logger.info("Stopped telemetry worker")

    async def _run(self) -> None:
        interval = max(settings.telemetry.ingestion_interval_ms / 1000, 0.1)
        assert self._stop_event is not None

        while not self._stop_event.is_set():
            batch = await self._telemetry_service.drain()
            if batch:
                session = SessionLocal()
                try:
                    slo_service = SLOService(session, self._policy_client)
                    evaluator = HealthEvaluationService(
                        session,
                        self._policy_client,
                        slo_service=slo_service,
                        event_bus=self._event_bus,
                    )
                    await evaluator.evaluate_batch(batch)
                    session.commit()
                except Exception:
                    session.rollback()
                    logger.exception("Failed to evaluate telemetry batch")
                finally:
                    session.close()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=interval)
            except asyncio.TimeoutError:
                continue

