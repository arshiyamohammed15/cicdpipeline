from datetime import datetime, timedelta

import pytest

from ..database.models import Alert
from ..services.ingestion_service import AlertIngestionService


def _alert(alert_id: str, dedup_key: str, started_at: datetime | None = None) -> Alert:
    now = started_at or datetime.utcnow()
    return Alert(
        alert_id=alert_id,
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-1",
        severity="P1",
        priority="P1",
        category="reliability",
        summary="test alert",
        description="unit test",
        labels={},
        started_at=now,
        last_seen_at=now,
        dedup_key=dedup_key,
    )


@pytest.mark.asyncio
async def test_alert_deduplication(session):
    service = AlertIngestionService(session)
    original = _alert("alert-1", "comp-1:P1")
    saved = await service.ingest(original)

    duplicate = _alert("alert-2", "comp-1:P1")
    duplicate.summary = "updated"
    latest = await service.ingest(duplicate)

    assert latest.alert_id == saved.alert_id
    assert latest.summary == "updated"


@pytest.mark.asyncio
async def test_new_incident_when_window_expired(session, monkeypatch):
    service = AlertIngestionService(session)
    first = _alert("alert-3", "comp-2:P2")
    saved = await service.ingest(first)

    expired = _alert("alert-4", "comp-2:P2", started_at=datetime.utcnow() + timedelta(hours=1))
    latest = await service.ingest(expired)

    assert latest.alert_id == "alert-4"
    assert latest.incident_id != saved.incident_id

