"""Repository helpers for manipulating alerting data."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .database.models import Alert, Incident, Notification


class AlertRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_alert(self, alert: Alert) -> Alert:
        existing = await self.session.get(Alert, alert.alert_id)
        if existing:
            data = alert.model_dump(exclude_unset=True)
            for field, value in data.items():
                # Special handling for dict fields to merge instead of replace
                if field == "labels" and isinstance(value, dict) and isinstance(getattr(existing, field, None), dict):
                    existing.labels.update(value)
                else:
                    setattr(existing, field, value)
            existing.last_seen_at = datetime.utcnow()
            saved = existing
        else:
            alert.last_seen_at = alert.last_seen_at or datetime.utcnow()
            self.session.add(alert)
            saved = alert
        await self.session.commit()
        await self.session.refresh(saved)
        return saved

    async def fetch_by_dedup(self, dedup_key: str) -> Optional[Alert]:
        result = await self.session.exec(select(Alert).where(Alert.dedup_key == dedup_key))
        return result.scalar_one_or_none()

    async def fetch(self, alert_id: str) -> Optional[Alert]:
        return await self.session.get(Alert, alert_id)


class IncidentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update(self, incident: Incident) -> Incident:
        existing = await self.session.get(Incident, incident.incident_id)
        if existing:
            data = incident.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(existing, field, value)
            saved = existing
        else:
            self.session.add(incident)
            saved = incident
        await self.session.commit()
        await self.session.refresh(saved)
        return saved

    async def fetch(self, incident_id: str) -> Optional[Incident]:
        return await self.session.get(Incident, incident_id)


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, notification: Notification) -> Notification:
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def pending_for_alert(self, alert_id: str) -> Iterable[Notification]:
        result = await self.session.exec(
            select(Notification).where(Notification.alert_id == alert_id, Notification.status == "pending")
        )
        return result.scalars().all()

    async def fetch(self, notification_id: str) -> Optional[Notification]:
        """Fetch a notification by ID."""
        return await self.session.get(Notification, notification_id)
