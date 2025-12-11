
# Imports handled by conftest.py
from datetime import datetime

import pytest
import warnings

pytestmark = pytest.mark.filterwarnings("ignore::ResourceWarning")
warnings.filterwarnings("ignore", category=ResourceWarning, module=r"anyio\.streams\.memory")

from alerting_notification_service.database.models import Alert, Incident, Notification
from alerting_notification_service.repositories import AlertRepository, IncidentRepository, NotificationRepository
from alerting_notification_service.clients import IAMClient, PolicyClient
from alerting_notification_service.services.escalation_service import EscalationService
from alerting_notification_service.services.lifecycle_service import LifecycleService
from alerting_notification_service.services.notification_service import NotificationDispatcher
from alerting_notification_service.services.routing_service import QuietHoursEvaluator, RoutingService


def _alert(alert_id: str, tenant: str = "tenant-route") -> Alert:
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
        summary=f"Alert {alert_id}",
        labels={},
        started_at=now,
        last_seen_at=now,
        dedup_key=f"{tenant}:{alert_id}",
        incident_id=f"inc-{alert_id}",
    )


@pytest.mark.asyncio
async def test_routing_and_notification_flow(session):
    repo = NotificationRepository(session)
    routing = RoutingService(repo)
    alert = _alert("alert-route", tenant="tenant-route")
    notifications = await routing.route_alert(alert)
    assert notifications
    # Policy-driven routing: P1 should use SMS channel from policy
    assert any(n.channel == "sms" for n in notifications)

    pending = await repo.pending_for_alert("alert-route")
    assert len(pending) > 0

    first_pending = pending[0]
    if isinstance(first_pending, str):
        first_pending = await repo.fetch(first_pending)
    await routing.record_delivery(first_pending, "sent")


@pytest.mark.asyncio
async def test_notification_dispatcher_channels():
    dispatcher = NotificationDispatcher()
    notification = Notification(
        notification_id="notif-email",
        tenant_id="tenant-route",
        alert_id="alert-email",
        target_id="tenant-route-oncall",
        channel="email",
    )
    assert await dispatcher.dispatch(notification) == "sent"

    sms_notification = Notification(
        notification_id="notif-sms",
        tenant_id="tenant-route",
        alert_id="alert-sms",
        target_id="tenant-route-oncall",
        channel="sms",
    )
    assert await dispatcher.dispatch(sms_notification) == "sent"

    webhook = Notification(
        notification_id="notif-webhook",
        tenant_id="tenant-route",
        alert_id="alert-webhook",
        target_id="tenant-route-oncall",
        channel="webhook",
    )
    assert await dispatcher.dispatch(webhook) == "sent"

    fallback = Notification(
        notification_id="notif-fallback",
        tenant_id="tenant-route",
        alert_id="alert-fallback",
        target_id="tenant-route-oncall",
        channel="voice",
    )
    assert await dispatcher.dispatch(fallback) == "sent"


@pytest.mark.asyncio
async def test_lifecycle_service_transitions(session):
    alert_repo = AlertRepository(session)
    incident_repo = IncidentRepository(session)

    incident = Incident(
        incident_id="inc-lifecycle",
        tenant_id="tenant-route",
        title="Transition",
        severity="P1",
        opened_at=datetime.utcnow(),
    )
    await incident_repo.create_or_update(incident)

    alert = _alert("lifecycle", tenant="tenant-route")
    await alert_repo.upsert_alert(alert)

    service = LifecycleService(session)
    acked = await service.acknowledge(alert.alert_id, actor="tester")
    assert acked.status == "acknowledged"

    resolved = await service.resolve(alert.alert_id, actor="tester")
    assert resolved.status == "resolved"
    updated_incident = await incident_repo.fetch(alert.incident_id)
    assert updated_incident.status == "resolved"
    assert updated_incident.resolved_at is not None
    snoozed = await service.snooze(alert.alert_id, duration_minutes=15)
    assert snoozed.status == "snoozed"

    with pytest.raises(ValueError):
        await service.acknowledge("missing-alert", actor="tester")
    with pytest.raises(ValueError):
        await service.resolve("missing-alert", actor="tester")
    with pytest.raises(ValueError):
        await service.snooze("missing-alert", duration_minutes=5)


def test_quiet_hours_wraparound():
    evaluator = QuietHoursEvaluator({"Fri": "22:00-06:00"})
    late = datetime.strptime("2025-11-21 23:30", "%Y-%m-%d %H:%M")
    assert evaluator.is_quiet(late)
    early = datetime.strptime("2025-11-21 07:00", "%Y-%m-%d %H:%M")
    assert not evaluator.is_quiet(early)


def test_quiet_hours_standard_window_and_missing_day():
    evaluator = QuietHoursEvaluator({"Mon": "09:00-17:00"})
    inside = datetime.strptime("2025-11-24 10:00", "%Y-%m-%d %H:%M")
    assert evaluator.is_quiet(inside)
    outside_day = datetime.strptime("2025-11-25 10:00", "%Y-%m-%d %H:%M")
    assert not evaluator.is_quiet(outside_day)


@pytest.mark.asyncio
async def test_routing_uses_policy_client(session, tmp_path, monkeypatch):
    import json
    from pathlib import Path

    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {
            "defaults": {
                "targets": ["{tenant_id}-custom"],
                "channels": ["email"],
                "channel_overrides": {"P0": ["sms", "voice"]},
            },
            "tenant_overrides": {},
        },
        "escalation": {"policies": {}},
        "fatigue": {},
    }
    policy_path = Path(tmp_path / "test_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    policy_client = PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    repo = NotificationRepository(session)
    routing = RoutingService(repo, policy_client=policy_client)

    alert = _alert("policy-test", tenant="tenant-custom")
    alert.severity = "P0"
    notifications = await routing.route_alert(alert)

    # P0 should use SMS and voice channels from policy
    channels = [n.channel for n in notifications]
    assert "sms" in channels
    assert "voice" in channels
    # Targets should be expanded from template
    assert any("tenant-custom-custom" in n.target_id for n in notifications)


@pytest.mark.asyncio
async def test_escalation_service_executes_policy(session, tmp_path, monkeypatch):
    import json
    from pathlib import Path

    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {
            "defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]},
            "tenant_overrides": {},
        },
        "escalation": {
            "policies": {
                "default": {
                    "policy_id": "default",
                    "steps": [
                        {"order": 1, "delay_seconds": 0, "channels": ["sms"], "target_group_id": "oncall-primary"},
                        {"order": 2, "delay_seconds": 300, "channels": ["voice"], "target_group_id": "oncall-secondary"},
                    ],
                }
            }
        },
        "fatigue": {},
    }
    policy_path = Path(tmp_path / "test_escalation_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    policy_client = PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    repo = NotificationRepository(session)
    escalation = EscalationService(session, policy_client=policy_client, notification_repo=repo)

    alert = _alert("escalation-test", tenant="tenant-escalate")
    notifications = await escalation.execute_escalation(alert, policy_id="default", current_step=1)

    # Step 1 should create SMS notifications
    assert len(notifications) > 0
    assert all(n.channel == "sms" for n in notifications)
    assert all(n.policy_id == "default" for n in notifications)


@pytest.mark.asyncio
async def test_escalation_skips_when_alert_acknowledged(session, tmp_path, monkeypatch):
    import json
    from pathlib import Path

    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {
            "defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]},
            "tenant_overrides": {},
        },
        "escalation": {
            "policies": {
                "default": {
                    "policy_id": "default",
                    "continue_after_ack": False,
                    "steps": [{"order": 1, "delay_seconds": 0, "channels": ["sms"]}],
                }
            }
        },
        "fatigue": {},
    }
    policy_path = Path(tmp_path / "test_escalation_ack_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    policy_client = PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    repo = NotificationRepository(session)
    escalation = EscalationService(session, policy_client=policy_client, notification_repo=repo)

    alert = _alert("escalation-ack", tenant="tenant-ack")
    alert.status = "acknowledged"
    notifications = await escalation.execute_escalation(alert, policy_id="default", current_step=1)

    # Escalation should be skipped when alert is ACK'd and policy says to stop
    assert len(notifications) == 0


@pytest.mark.asyncio
async def test_escalation_continues_after_ack_when_policy_allows(session, tmp_path, monkeypatch):
    import json
    from pathlib import Path

    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {
            "defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]},
            "tenant_overrides": {},
        },
        "escalation": {
            "policies": {
                "default": {
                    "policy_id": "default",
                    "continue_after_ack": True,
                    "steps": [{"order": 1, "delay_seconds": 0, "channels": ["sms"]}],
                }
            }
        },
        "fatigue": {},
    }
    policy_path = Path(tmp_path / "test_escalation_continue_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    policy_client = PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    repo = NotificationRepository(session)
    escalation = EscalationService(session, policy_client=policy_client, notification_repo=repo)

    alert = _alert("escalation-continue", tenant="tenant-continue")
    alert.status = "acknowledged"
    notifications = await escalation.execute_escalation(alert, policy_id="default", current_step=1)

    # Escalation should continue when policy allows it
    assert len(notifications) > 0


@pytest.mark.asyncio
async def test_iam_client_expands_targets():
    iam = IAMClient()
    targets = ["user-1", "group:ops-team", "tenant-a-oncall"]
    expanded = await iam.expand_targets(targets)
    # Stub implementation returns targets as-is
    assert len(expanded) == 3
    assert "user-1" in expanded
    assert "group:ops-team" in expanded
    assert "tenant-a-oncall" in expanded

