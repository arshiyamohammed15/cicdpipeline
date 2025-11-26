"""Lifecycle operations for alerts and incidents."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from ..database.models import Alert, Incident
from ..repositories import AlertRepository, IncidentRepository
from .evidence_service import EvidenceService
from .stream_service import get_stream_service


class LifecycleService:
    def __init__(self, session: AsyncSession):
        self.alert_repo = AlertRepository(session)
        self.incident_repo = IncidentRepository(session)
        self.stream_service = get_stream_service()
        self.evidence = EvidenceService()

    async def fetch_alert(self, alert_id: str) -> Alert | None:
        return await self.alert_repo.fetch(alert_id)

    async def acknowledge(self, alert_id: str, actor: str) -> Alert:
        alert = await self.alert_repo.fetch(alert_id)
        if not alert:
            raise ValueError("alert not found")
        alert.status = "acknowledged"
        saved = await self.alert_repo.upsert_alert(alert)
        await self.stream_service.publish_alert(saved, event_type="alert.acknowledged", metadata={"actor": actor})
        await self.evidence.record_event(
            event_type="alert_acknowledged",
            tenant_id=saved.tenant_id,
            actor=actor,
            alert_id=saved.alert_id,
        )
        return saved

    async def resolve(self, alert_id: str, actor: str) -> Alert:
        alert = await self.alert_repo.fetch(alert_id)
        if not alert:
            raise ValueError("alert not found")
        alert.status = "resolved"
        alert.ended_at = datetime.utcnow()
        resolved = await self.alert_repo.upsert_alert(alert)
        await self.stream_service.publish_alert(resolved, event_type="alert.resolved", metadata={"actor": actor})
        await self.evidence.record_event(
            event_type="alert_resolved",
            tenant_id=resolved.tenant_id,
            actor=actor,
            alert_id=resolved.alert_id,
        )
        if alert.incident_id:
            incident = await self.incident_repo.fetch(alert.incident_id)
            if incident:
                incident.status = "resolved"
                incident.resolved_at = datetime.utcnow()
                await self.incident_repo.create_or_update(incident)
        return resolved

    async def snooze(self, alert_id: str, duration_minutes: int, actor: Optional[str] = None) -> Alert:
        alert = await self.alert_repo.fetch(alert_id)
        if not alert:
            raise ValueError("alert not found")
        alert.status = "snoozed"
        alert.snoozed_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        saved = await self.alert_repo.upsert_alert(alert)
        await self.stream_service.publish_alert(
            saved, event_type="alert.snoozed", metadata={"duration_minutes": duration_minutes, "actor": actor}
        )
        await self.evidence.record_event(
            event_type="alert_snoozed",
            tenant_id=saved.tenant_id,
            actor=actor,
            alert_id=saved.alert_id,
            metadata={"duration_minutes": duration_minutes},
        )
        return saved

    async def check_and_unsnooze(self, alert_id: str) -> Optional[Alert]:
        """Check if alert snooze has expired and auto-unsnooze if needed."""
        alert = await self.alert_repo.fetch(alert_id)
        if not alert or alert.status != "snoozed":
            return None
        if alert.snoozed_until and alert.snoozed_until <= datetime.utcnow():
            alert.status = "open"
            alert.snoozed_until = None
            saved = await self.alert_repo.upsert_alert(alert)
            await self.stream_service.publish_alert(saved, event_type="alert.unsnoozed", metadata={})
            await self.evidence.record_event(
                event_type="alert_unsnoozed",
                tenant_id=saved.tenant_id,
                actor="system",
                alert_id=saved.alert_id,
            )
            return saved
        return None

    async def mitigate_incident(self, incident_id: str, actor: str) -> Incident:
        """Mark incident as mitigated (partial resolution)."""
        incident = await self.incident_repo.fetch(incident_id)
        if not incident:
            raise ValueError("incident not found")
        incident.status = "mitigated"
        incident.mitigated_at = datetime.utcnow()
        saved = await self.incident_repo.create_or_update(incident)
        await self.evidence.record_event(
            event_type="incident_mitigated",
            tenant_id=saved.tenant_id,
            actor=actor,
            alert_id=None,
            metadata={"incident_id": incident_id},
        )
        return saved

    async def snooze_incident(self, incident_id: str, duration_minutes: int, actor: Optional[str] = None) -> Incident:
        """Snooze an incident, which snoozes all associated alerts."""
        incident = await self.incident_repo.fetch(incident_id)
        if not incident:
            raise ValueError("incident not found")
        
        # Snooze all alerts in the incident
        for alert_id in incident.alert_ids:
            try:
                await self.snooze(alert_id, duration_minutes, actor=actor)
            except ValueError:
                # Alert may not exist, skip it
                pass
        
        await self.evidence.record_event(
            event_type="incident_snoozed",
            tenant_id=incident.tenant_id,
            actor=actor,
            alert_id=None,
            metadata={"incident_id": incident_id, "duration_minutes": duration_minutes},
        )
        return incident
