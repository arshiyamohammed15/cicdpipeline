"""Alert ingestion workflow services."""
from __future__ import annotations

import time
from contextlib import nullcontext
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

try:  # pragma: no cover
    from opentelemetry import trace
except ImportError:  # pragma: no cover
    trace = None

from ..clients import PolicyClient
from ..config import get_settings
from ..database.models import Alert, Incident
from ..observability.metrics import ALERT_INGEST_COUNTER, DEDUP_LATENCY
from ..repositories import AlertRepository, IncidentRepository
from .automation_service import AutomationService
from .correlation_service import CorrelationService
from .enrichment_service import EnrichmentService
from .evidence_service import EvidenceService
from .stream_service import get_stream_service

settings = get_settings()
tracer = trace.get_tracer(__name__) if trace else None


class AlertIngestionService:
    def __init__(self, session: AsyncSession):
        self.alert_repo = AlertRepository(session)
        self.incident_repo = IncidentRepository(session)
        self.session = session
        self.policy_client = PolicyClient()
        self.enrichment = EnrichmentService()
        self.correlation = CorrelationService(session)
        self.automation = AutomationService(session)
        self.stream_service = get_stream_service()
        self.evidence = EvidenceService()

    @staticmethod
    def _window_expires(last_seen_at: datetime, window_minutes: int) -> bool:
        window = timedelta(minutes=window_minutes)
        return datetime.utcnow() - last_seen_at > window

    async def ingest(self, alert: Alert, correlation_key: Optional[str] = None) -> Alert:
        start = time.perf_counter()
        span_context = (
            tracer.start_as_current_span("alert_ingest") if tracer else nullcontext()  # type: ignore[attr-defined]
        )
        with span_context as span:
            if span and trace:  # pragma: no cover
                span.set_attribute("tenant_id", alert.tenant_id)
                span.set_attribute("severity", alert.severity)
            alert = await self.enrichment.enrich(alert)
        existing = await self.alert_repo.fetch_by_dedup(alert.dedup_key)
        dedup_window = self.policy_client.get_dedup_window(alert.category, alert.severity)
        if existing and not self._window_expires(existing.last_seen_at, dedup_window):
            existing.summary = alert.summary
            existing.description = alert.description
            existing.severity = alert.severity
            existing.last_seen_at = datetime.utcnow()
            saved = await self.alert_repo.upsert_alert(existing)
        else:
            incident_id = correlation_key or alert.incident_id
            if not incident_id:
                incident_id = await self.correlation.correlate(alert)
            incident = Incident(
                incident_id=incident_id,
                schema_version=alert.schema_version,
                tenant_id=alert.tenant_id,
                plane=getattr(alert, "plane", None),
                component_id=alert.component_id,
                title=f"Auto incident for {alert.summary}",
                description=alert.description,
                severity=alert.severity,
                opened_at=datetime.utcnow(),
                alert_ids=[alert.alert_id],
                correlation_keys=[alert.dedup_key],
                dependency_refs=alert.component_metadata.get("dependencies", []),
            )
            await self.incident_repo.create_or_update(incident)
            alert.incident_id = incident_id
            alert.last_seen_at = datetime.utcnow()
            saved = await self.alert_repo.upsert_alert(alert)

        ALERT_INGEST_COUNTER.labels(severity=saved.severity).inc()
        DEDUP_LATENCY.observe(time.perf_counter() - start)
        await self.evidence.record_event(
            event_type="alert_ingested",
            tenant_id=saved.tenant_id,
            actor=None,
            alert_id=saved.alert_id,
            metadata={"severity": saved.severity},
        )

        # Publish to stream (only for new alerts, not deduplicated ones)
        if not existing or self._window_expires(existing.last_seen_at, dedup_window):
            await self.stream_service.publish_alert(saved, event_type="alert.created")

        # Trigger automation hooks if present
        if saved.automation_hooks:
            await self.automation.trigger_automation_hooks(saved)

        return saved
