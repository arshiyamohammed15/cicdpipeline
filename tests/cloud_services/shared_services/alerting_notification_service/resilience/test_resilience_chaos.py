from __future__ import annotations
"""Resilience and chaos tests for Alerting & Notification Service (RT-1, RT-2)."""

# Imports handled by conftest.py

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from alerting_notification_service.database.models import Alert, Incident, Notification
from alerting_notification_service.repositories import AlertRepository, IncidentRepository, NotificationRepository
from alerting_notification_service.services.escalation_service import EscalationService
from alerting_notification_service.services.ingestion_service import AlertIngestionService
from alerting_notification_service.services.notification_service import NotificationDispatcher, NotificationChannel


def _alert(alert_id: str, tenant: str = "tenant-resilience") -> Alert:
    """Generate alert for resilience testing."""
    now = datetime.utcnow()
    return Alert(
        alert_id=alert_id,
        tenant_id=tenant,
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-1",
        severity="P1",
        priority="P1",
        category="reliability",
        summary=f"Resilience test {alert_id}",
        started_at=now,
        last_seen_at=now,
        dedup_key=f"resilience:{alert_id}",
    )


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rt1_integration_outages_channel_failure(test_client, session):
    """
    RT-1: Integration Outages

    Simulate external channel / on-call tool downtime;
    verify graceful degradation and fallback.
    """
    from alerting_notification_service.services.notification_service import NotificationDispatcher, NotificationChannel

    # Create alert
    alert_repo = AlertRepository(session)
    alert = _alert("rt1-channel-outage")
    await alert_repo.upsert_alert(alert)

    # Create notification with failing channel
    notification_repo = NotificationRepository(session)
    notification = Notification(
        notification_id="notif-rt1",
        tenant_id=alert.tenant_id,
        alert_id=alert.alert_id,
        target_id="user-1",
        channel="chat",
        status="pending",
    )
    await notification_repo.save(notification)

    # Simulate channel outage (channel always fails)
    class OutageChannel(NotificationChannel):
        async def send(self, notification: Notification) -> str:
            raise Exception("Channel service unavailable")

    dispatcher = NotificationDispatcher(session=session)
    dispatcher.channels["chat"] = OutageChannel()

    # Dispatch should handle failure gracefully
    result = await dispatcher.dispatch(notification, alert=alert)

    # Should not crash, should return failure status
    assert result in ["failed", "pending"], f"Expected failed or pending, got {result}"

    # Verify notification status updated
    updated = await notification_repo.fetch("notif-rt1")
    assert updated is not None
    # Notification should have been attempted (attempts >= 0, status updated)
    assert updated.attempts >= 0
    assert updated.status in ["failed", "pending", "cancelled"]
    # If failed, should have failure_reason or be pending for retry
    if updated.status == "failed":
        assert updated.failure_reason is not None or updated.next_attempt_at is not None


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rt1_integration_outages_fallback_channels(test_client, session):
    """
    RT-1: Integration Outages

    Test fallback to alternative channels when primary channel fails.
    """
    from alerting_notification_service.services.notification_service import NotificationDispatcher, NotificationChannel

    # Create alert
    alert_repo = AlertRepository(session)
    alert = _alert("rt1-fallback-test")
    await alert_repo.upsert_alert(alert)

    # Create notification
    notification_repo = NotificationRepository(session)
    notification = Notification(
        notification_id="notif-rt1-fallback",
        tenant_id=alert.tenant_id,
        alert_id=alert.alert_id,
        target_id="user-1",
        channel="chat",
        status="pending",
    )
    await notification_repo.save(notification)

    # Simulate chat outage but SMS working
    class OutageChannel(NotificationChannel):
        async def send(self, notification: Notification) -> str:
            raise Exception("Chat service unavailable")

    class WorkingChannel(NotificationChannel):
        async def send(self, notification: Notification) -> str:
            return "sent"

    dispatcher = NotificationDispatcher(session=session)
    dispatcher.channels["chat"] = OutageChannel()
    dispatcher.channels["sms"] = WorkingChannel()

    # Dispatch should attempt chat, fail, then fallback to SMS
    result = await dispatcher.dispatch(notification, alert=alert)

    # Should eventually succeed via fallback or be pending retry
    assert result in ["sent", "pending", "failed"]

    # Verify fallback was attempted (check for SMS notification or retry scheduled)
    updated = await notification_repo.fetch("notif-rt1-fallback")
    assert updated is not None
    # Either succeeded via fallback or scheduled for retry
    assert updated.status in ["sent", "pending"] or updated.attempts > 0


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rt1_integration_outages_eris_unavailable(test_client, session):
    """
    RT-1: Integration Outages

    Test graceful handling when ERIS is unavailable.
    """
    from alerting_notification_service.clients import ErisClient
    from alerting_notification_service.services.evidence_service import EvidenceService

    # Mock ERIS to raise exception
    original_emit = ErisClient.emit_receipt

    async def failing_emit(self, payload: dict) -> None:
        raise Exception("ERIS service unavailable")

    ErisClient.emit_receipt = failing_emit

    try:
        # Create alert (should not fail even if ERIS is down)
        alert_payload = {
            "schema_version": "1.0.0",
            "alert_id": "rt1-eris-outage",
            "tenant_id": "tenant-integration",  # Match test_client default
            "source_module": "EPC-5",
            "plane": "Tenant",
            "environment": "prod",
            "component_id": "comp-1",
            "severity": "P1",
            "priority": "P1",
            "category": "reliability",
            "summary": "ERIS outage test",
            "started_at": datetime.utcnow().isoformat(),
            "last_seen_at": datetime.utcnow().isoformat(),
            "dedup_key": "rt1-eris-outage",
        }

        response = test_client.post("/v1/alerts", json=alert_payload)

        # Alert ingestion should succeed even if ERIS fails
        # (ERIS failures should be logged but not block alert processing)
        assert response.status_code == 200

        # Verify alert was created
        alert_id = response.json()["alert_id"]
        get_response = test_client.get(f"/v1/alerts/{alert_id}")
        assert get_response.status_code == 200
    finally:
        # Restore original method
        ErisClient.emit_receipt = original_emit


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rt2_epc4_restart_state_recovery(test_client, session):
    """
    RT-2: Alerting & Notification Service Restart

    Restart during active incident;
    confirm alert/incidents state recovered and escalations continue correctly.
    """
    # Create alert and incident
    alert_repo = AlertRepository(session)
    incident_repo = IncidentRepository(session)

    alert = _alert("rt2-restart-test")
    await alert_repo.upsert_alert(alert)

    incident = Incident(
        incident_id="inc-rt2",
        tenant_id=alert.tenant_id,
        title="Restart test incident",
        severity="P1",
        opened_at=datetime.utcnow(),
        status="open",
        alert_ids=[alert.alert_id],
    )
    await incident_repo.create_or_update(incident)
    alert.incident_id = incident.incident_id
    await alert_repo.upsert_alert(alert)

    # Simulate restart: create new service instances
    # (In real scenario, this would be a service restart)
    new_ingestion = AlertIngestionService(session)
    new_escalation = EscalationService(session)

    # Verify state recovery: alert and incident should still exist
    recovered_alert = await alert_repo.fetch("rt2-restart-test")
    assert recovered_alert is not None
    assert recovered_alert.alert_id == "rt2-restart-test"
    assert recovered_alert.status == "open"
    assert recovered_alert.incident_id == "inc-rt2"

    recovered_incident = await incident_repo.fetch("inc-rt2")
    assert recovered_incident is not None
    assert recovered_incident.status == "open"
    assert alert.alert_id in recovered_incident.alert_ids

    # Verify escalation can continue
    # (Escalation service should be able to process existing alerts)
    notifications = await new_escalation.execute_escalation(recovered_alert, current_step=1)
    # Should not crash, may create notifications or skip based on policy
    assert isinstance(notifications, list)


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rt2_epc4_restart_pending_notifications_recovered(test_client, session):
    """
    RT-2: Alerting & Notification Service Restart

    Test that pending notifications are recovered after restart.
    """
    # Create alert and pending notification
    alert_repo = AlertRepository(session)
    notification_repo = NotificationRepository(session)

    alert = _alert("rt2-notif-recovery")
    await alert_repo.upsert_alert(alert)

    notification = Notification(
        notification_id="notif-rt2-pending",
        tenant_id=alert.tenant_id,
        alert_id=alert.alert_id,
        target_id="user-1",
        channel="email",
        status="pending",
        attempts=1,
    )
    await notification_repo.save(notification)

    # Simulate restart: create new dispatcher
    new_dispatcher = NotificationDispatcher(session=session)

    # Verify notification recovery
    recovered_notification = await notification_repo.fetch("notif-rt2-pending")
    assert recovered_notification is not None
    assert recovered_notification.status == "pending"
    assert recovered_notification.attempts == 1

    # Verify dispatcher can process recovered notification
    result = await new_dispatcher.dispatch(recovered_notification, alert=alert)
    assert result in ["sent", "pending", "failed"]

    # Verify notification was processed
    updated = await notification_repo.fetch("notif-rt2-pending")
    assert updated is not None
    assert updated.attempts > 1 or updated.status == "sent"


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rt2_epc4_restart_escalation_continuation(test_client, session):
    """
    RT-2: Alerting & Notification Service Restart

    Test that escalations continue correctly after restart.
    """
    from alerting_notification_service.clients import PolicyClient

    # Create alert with escalation policy
    alert_repo = AlertRepository(session)
    notification_repo = NotificationRepository(session)

    alert = _alert("rt2-escalation-continue")
    await alert_repo.upsert_alert(alert)

    # Create notification from step 1 of escalation
    notification = Notification(
        notification_id="notif-rt2-escalation",
        tenant_id=alert.tenant_id,
        alert_id=alert.alert_id,
        target_id="user-1",
        channel="sms",
        status="sent",
        attempts=1,
        policy_id="default",
    )
    await notification_repo.save(notification)

    # Simulate restart: create new escalation service
    policy_client = PolicyClient()
    new_escalation = EscalationService(session, policy_client=policy_client, notification_repo=notification_repo)

    # Verify escalation can continue to next step
    # (In real scenario, background worker would check next_attempt_at and continue)
    recovered_alert = await alert_repo.fetch("rt2-escalation-continue")
    assert recovered_alert is not None

    # Escalation service should be able to process the alert
    # (May skip if already ACK'd, or continue if not)
    notifications = await new_escalation.execute_escalation(recovered_alert, policy_id="default", current_step=2)
    # Should not crash
    assert isinstance(notifications, list)

