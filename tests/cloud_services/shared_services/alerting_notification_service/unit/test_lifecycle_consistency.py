from __future__ import annotations
"""Tests for FR-8: Lifecycle Consistency features."""

# Imports handled by conftest.py

from datetime import datetime, timedelta

import pytest

from alerting_notification_service.database.models import Alert, Incident
from alerting_notification_service.repositories import AlertRepository, IncidentRepository
from alerting_notification_service.services.escalation_service import EscalationService
from alerting_notification_service.services.lifecycle_service import LifecycleService


def _alert(alert_id: str, tenant: str = "tenant-lifecycle", incident_id: str | None = None) -> Alert:
    now = datetime.utcnow()
    return Alert(
        alert_id=alert_id,
        tenant_id=tenant,
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-lifecycle",
        severity="P1",
        priority="P1",
        category="reliability",
        summary=f"{alert_id} summary",
        description="lifecycle test",
        started_at=now,
        last_seen_at=now,
        dedup_key=f"{tenant}:{alert_id}",
        incident_id=incident_id,
        status="open",
    )


@pytest.mark.asyncio
async def test_snooze_sets_duration(session):
    """Test that snooze sets snoozed_until timestamp."""
    alert = _alert("snooze-duration")
    repo = AlertRepository(session)
    await repo.upsert_alert(alert)

    lifecycle = LifecycleService(session)
    snoozed = await lifecycle.snooze("snooze-duration", duration_minutes=30, actor="tester")

    assert snoozed.status == "snoozed"
    assert snoozed.snoozed_until is not None
    assert snoozed.snoozed_until > datetime.utcnow()
    assert snoozed.snoozed_until <= datetime.utcnow() + timedelta(minutes=31)  # Allow 1 min tolerance


@pytest.mark.asyncio
async def test_auto_unsnooze_when_expired(session):
    """Test that alerts auto-unsnooze when snooze duration expires."""
    alert = _alert("auto-unsnooze")
    alert.status = "snoozed"
    alert.snoozed_until = datetime.utcnow() - timedelta(minutes=1)  # Already expired
    repo = AlertRepository(session)
    await repo.upsert_alert(alert)

    lifecycle = LifecycleService(session)
    unsnoozed = await lifecycle.check_and_unsnooze("auto-unsnooze")

    assert unsnoozed is not None
    assert unsnoozed.status == "open"
    assert unsnoozed.snoozed_until is None


@pytest.mark.asyncio
async def test_auto_unsnooze_not_expired(session):
    """Test that alerts don't unsnooze if duration hasn't expired."""
    alert = _alert("snooze-active")
    alert.status = "snoozed"
    alert.snoozed_until = datetime.utcnow() + timedelta(minutes=30)  # Still active
    repo = AlertRepository(session)
    await repo.upsert_alert(alert)

    lifecycle = LifecycleService(session)
    result = await lifecycle.check_and_unsnooze("snooze-active")

    assert result is None  # Should not unsnooze


@pytest.mark.asyncio
async def test_incident_mitigation(session):
    """Test that incidents can be mitigated."""
    incident = Incident(
        incident_id="inc-mitigate",
        tenant_id="tenant-lifecycle",
        title="Test incident",
        severity="P1",
        opened_at=datetime.utcnow(),
        status="open",
        alert_ids=["alert-1", "alert-2"],
    )
    incident_repo = IncidentRepository(session)
    await incident_repo.create_or_update(incident)

    lifecycle = LifecycleService(session)
    mitigated = await lifecycle.mitigate_incident("inc-mitigate", actor="tester")

    assert mitigated.status == "mitigated"
    assert mitigated.mitigated_at is not None


@pytest.mark.asyncio
async def test_incident_snooze_snoozes_all_alerts(session):
    """Test that snoozing an incident snoozes all associated alerts."""
    alert1 = _alert("alert-1", incident_id="inc-snooze")
    alert2 = _alert("alert-2", incident_id="inc-snooze")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert1)
    await alert_repo.upsert_alert(alert2)

    incident = Incident(
        incident_id="inc-snooze",
        tenant_id="tenant-lifecycle",
        title="Test incident",
        severity="P1",
        opened_at=datetime.utcnow(),
        status="open",
        alert_ids=["alert-1", "alert-2"],
    )
    incident_repo = IncidentRepository(session)
    await incident_repo.create_or_update(incident)

    lifecycle = LifecycleService(session)
    await lifecycle.snooze_incident("inc-snooze", duration_minutes=60, actor="tester")

    # Check that both alerts are snoozed
    alert1_updated = await alert_repo.fetch("alert-1")
    alert2_updated = await alert_repo.fetch("alert-2")

    assert alert1_updated.status == "snoozed"
    assert alert1_updated.snoozed_until is not None
    assert alert2_updated.status == "snoozed"
    assert alert2_updated.snoozed_until is not None


@pytest.mark.asyncio
async def test_escalation_skips_when_incident_mitigated(session, tmp_path, monkeypatch):
    """Test that escalation is skipped when incident is mitigated."""
    from pathlib import Path
    from alerting_notification_service.clients import PolicyClient
    from alerting_notification_service.repositories import NotificationRepository

    # Create alert with mitigated incident
    alert = _alert("escalation-mitigated", incident_id="inc-mitigated")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    incident = Incident(
        incident_id="inc-mitigated",
        tenant_id="tenant-lifecycle",
        title="Mitigated incident",
        severity="P1",
        opened_at=datetime.utcnow(),
        status="mitigated",
        mitigated_at=datetime.utcnow(),
        alert_ids=["escalation-mitigated"],
    )
    incident_repo = IncidentRepository(session)
    await incident_repo.create_or_update(incident)

    # Create policy that would normally escalate
    policy_bundle = {
        "routing": {"default": {"targets": ["user-1"], "channels": ["email"]}},
        "escalation": {
            "policies": {
                "default": {
                    "steps": [{"delay_minutes": 0, "targets": ["user-1"], "channels": ["email"]}],
                    "continue_after_ack": False,
                }
            }
        },
    }
    policy_path = Path(tmp_path / "test_mitigation_policy.json")
    import json
    policy_path.write_text(json.dumps(policy_bundle))
    monkeypatch.setenv("ALERTING_POLICY_PATH", str(policy_path))

    policy_client = PolicyClient()
    repo = NotificationRepository(session)
    escalation = EscalationService(session, policy_client=policy_client, notification_repo=repo)

    notifications = await escalation.execute_escalation(alert, policy_id="default", current_step=1)

    # Escalation should be skipped because incident is mitigated
    assert len(notifications) == 0


@pytest.mark.asyncio
async def test_escalation_respects_snooze_duration(session, tmp_path, monkeypatch):
    """Test that escalation respects snooze status."""
    from pathlib import Path
    from alerting_notification_service.clients import PolicyClient
    from alerting_notification_service.repositories import NotificationRepository

    alert = _alert("escalation-snoozed")
    alert.status = "snoozed"
    alert.snoozed_until = datetime.utcnow() + timedelta(minutes=30)
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    policy_bundle = {
        "routing": {"default": {"targets": ["user-1"], "channels": ["email"]}},
        "escalation": {
            "policies": {
                "default": {
                    "steps": [{"delay_minutes": 0, "targets": ["user-1"], "channels": ["email"]}],
                }
            }
        },
    }
    policy_path = Path(tmp_path / "test_snooze_escalation_policy.json")
    import json
    policy_path.write_text(json.dumps(policy_bundle))
    monkeypatch.setenv("ALERTING_POLICY_PATH", str(policy_path))

    policy_client = PolicyClient()
    repo = NotificationRepository(session)
    escalation = EscalationService(session, policy_client=policy_client, notification_repo=repo)

    notifications = await escalation.execute_escalation(alert, policy_id="default", current_step=1)

    # Escalation should be skipped because alert is snoozed
    assert len(notifications) == 0

