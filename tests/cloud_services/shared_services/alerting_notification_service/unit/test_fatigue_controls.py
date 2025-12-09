from __future__ import annotations
"""Tests for alert fatigue controls: rate limiting, maintenance windows, suppression."""

# Imports handled by conftest.py

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from alerting_notification_service.clients import PolicyClient
from alerting_notification_service.database.models import Alert, Incident, Notification
from alerting_notification_service.repositories import AlertRepository, IncidentRepository, NotificationRepository
from alerting_notification_service.services.fatigue_control import FatigueControlService, MaintenanceWindowService, RateLimiter


def _alert(alert_id: str, tenant: str = "tenant-test", severity: str = "P1", incident_id: Optional[str] = None) -> Alert:
    now = datetime.utcnow()
    return Alert(
        alert_id=alert_id,
        tenant_id=tenant,
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-1",
        severity=severity,
        priority=severity,
        category="reliability",
        summary=f"Alert {alert_id}",
        labels={},
        started_at=now,
        last_seen_at=now,
        dedup_key=f"{tenant}:{alert_id}",
        incident_id=incident_id,
    )


@pytest.mark.asyncio
@pytest.mark.alerting_regression
@pytest.mark.integration
async def test_rate_limiter_alert_limit(session: AsyncSession, tmp_path):
    """Test that rate limiter enforces per-alert limits."""
    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {
            "rate_limits": {
                "per_alert": {"max_notifications": 3, "window_minutes": 60},
                "per_user": {"max_notifications": 20, "window_minutes": 60},
            },
            "maintenance": [],
            "suppression": {},
        },
        "retry": {"defaults": {}},
        "fallback": {"defaults": {}},
    }
    policy_path = Path(tmp_path / "rate_limit_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    alert = _alert("rate-limit-test")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    notif_repo = NotificationRepository(session)
    limiter = RateLimiter(session, PolicyClient(policy_path=policy_path, cache_ttl_seconds=1))

    # Create 2 notifications (within limit of 3)
    for i in range(2):
        notification = Notification(
            notification_id=f"notif-{i}",
            tenant_id="tenant-test",
            alert_id="rate-limit-test",
            target_id="user-1",
            channel="email",
            status="sent",
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )
        await notif_repo.save(notification)

    # Should still be within limit (2 < 3)
    assert await limiter.check_alert_rate_limit("rate-limit-test") is True

    # Add one more to reach limit (3)
    notification = Notification(
        notification_id="notif-2",
        tenant_id="tenant-test",
        alert_id="rate-limit-test",
        target_id="user-1",
        channel="email",
        status="sent",
    )
    await notif_repo.save(notification)

    # Should exceed limit (3 >= 3)
    assert await limiter.check_alert_rate_limit("rate-limit-test") is False


@pytest.mark.asyncio
async def test_rate_limiter_user_limit(session: AsyncSession, tmp_path):
    """Test that rate limiter enforces per-user limits."""
    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {
            "rate_limits": {
                "per_alert": {"max_notifications": 5, "window_minutes": 60},
                "per_user": {"max_notifications": 5, "window_minutes": 60},
            },
            "maintenance": [],
            "suppression": {},
        },
        "retry": {"defaults": {}},
        "fallback": {"defaults": {}},
    }
    policy_path = Path(tmp_path / "user_rate_limit_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    notif_repo = NotificationRepository(session)
    limiter = RateLimiter(session, PolicyClient(policy_path=policy_path, cache_ttl_seconds=1))

    # Create 4 notifications for user (within limit of 5)
    for i in range(4):
        notification = Notification(
            notification_id=f"user-notif-{i}",
            tenant_id="tenant-test",
            alert_id=f"alert-{i}",
            target_id="user-limited",
            channel="email",
            status="sent",
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )
        await notif_repo.save(notification)

    # Should still be within limit (4 < 5)
    assert await limiter.check_user_rate_limit("user-limited") is True

    # Add one more to reach limit (5)
    notification = Notification(
        notification_id="user-notif-4",
        tenant_id="tenant-test",
        alert_id="alert-4",
        target_id="user-limited",
        channel="email",
        status="sent",
    )
    await notif_repo.save(notification)

    # Should exceed limit (5 >= 5)
    assert await limiter.check_user_rate_limit("user-limited") is False


@pytest.mark.asyncio
async def test_maintenance_window_service(tmp_path):
    """Test maintenance window detection."""
    now = datetime.utcnow()
    start_time = (now - timedelta(hours=1)).isoformat()
    end_time = (now + timedelta(hours=1)).isoformat()

    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {
            "rate_limits": {},
            "maintenance": [
                {
                    "component_id": "comp-maintenance",
                    "start": start_time,
                    "end": end_time,
                },
                {
                    "tenant_id": "tenant-maintenance",
                    "start": start_time,
                    "end": end_time,
                },
            ],
            "suppression": {},
        },
        "retry": {"defaults": {}},
        "fallback": {"defaults": {}},
    }
    policy_path = Path(tmp_path / "maintenance_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    service = MaintenanceWindowService(PolicyClient(policy_path=policy_path, cache_ttl_seconds=1))

    # Component in maintenance
    assert service.is_in_maintenance(component_id="comp-maintenance") is True
    assert service.is_in_maintenance(component_id="comp-other") is False

    # Tenant in maintenance
    assert service.is_in_maintenance(tenant_id="tenant-maintenance") is True
    assert service.is_in_maintenance(tenant_id="tenant-other") is False


@pytest.mark.asyncio
async def test_fatigue_control_suppression(session: AsyncSession, tmp_path):
    """Test that fatigue control suppresses notifications appropriately."""
    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {
            "rate_limits": {
                "per_alert": {"max_notifications": 2, "window_minutes": 60},
                "per_user": {"max_notifications": 10, "window_minutes": 60},
            },
            "maintenance": [],
            "suppression": {
                "suppress_followup_during_incident": True,
                "suppress_window_minutes": 15,
            },
        },
        "retry": {"defaults": {}},
        "fallback": {"defaults": {}},
    }
    policy_path = Path(tmp_path / "fatigue_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    # Create incident
    incident = Incident(
        incident_id="inc-suppress",
        tenant_id="tenant-test",
        title="Test Incident",
        severity="P1",
        opened_at=datetime.utcnow(),
        status="open",
    )
    incident_repo = IncidentRepository(session)
    await incident_repo.create_or_update(incident)

    # Create first alert in incident
    alert1 = _alert("alert-1", incident_id="inc-suppress")
    alert1.started_at = datetime.utcnow() - timedelta(minutes=10)
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert1)

    # Create follow-up alert
    alert2 = _alert("alert-2", incident_id="inc-suppress")
    alert2.started_at = datetime.utcnow()

    fatigue = FatigueControlService(session, PolicyClient(policy_path=policy_path, cache_ttl_seconds=1))
    should_suppress, reason = await fatigue.should_suppress_notification(alert2, "user-1")

    # Should suppress follow-up alert
    assert should_suppress is True
    assert reason == "incident_followup_suppressed"


@pytest.mark.asyncio
async def test_fatigue_control_rate_limit_suppression(session: AsyncSession, tmp_path):
    """Test that fatigue control suppresses when rate limits are exceeded."""
    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {
            "rate_limits": {
                "per_alert": {"max_notifications": 2, "window_minutes": 60},
                "per_user": {"max_notifications": 2, "window_minutes": 60},
            },
            "maintenance": [],
            "suppression": {},
        },
        "retry": {"defaults": {}},
        "fallback": {"defaults": {}},
    }
    policy_path = Path(tmp_path / "rate_limit_fatigue_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    alert = _alert("rate-limit-alert")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    notif_repo = NotificationRepository(session)
    # Create notifications to exceed limit
    for i in range(3):
        notification = Notification(
            notification_id=f"notif-rate-{i}",
            tenant_id="tenant-test",
            alert_id="rate-limit-alert",
            target_id="user-1",
            channel="email",
            status="sent",
            created_at=datetime.utcnow() - timedelta(minutes=30),
        )
        await notif_repo.save(notification)

    fatigue = FatigueControlService(session, PolicyClient(policy_path=policy_path, cache_ttl_seconds=1))
    should_suppress, reason = await fatigue.should_suppress_notification(alert, "user-1")

    assert should_suppress is True
    assert reason == "alert_rate_limit_exceeded"


@pytest.mark.asyncio
async def test_tag_alert_as_noisy(session: AsyncSession):
    """Test tagging alert as noisy."""
    alert = _alert("noisy-alert")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    fatigue = FatigueControlService(session)
    tagged = await fatigue.tag_alert_as_noisy("noisy-alert", actor="tester")

    assert tagged.labels.get("noisy") == "true"
    assert "noisy_tagged_at" in tagged.labels
    assert tagged.labels.get("noisy_tagged_by") == "tester"


@pytest.mark.asyncio
async def test_tag_alert_as_false_positive(session: AsyncSession):
    """Test tagging alert as false positive."""
    alert = _alert("fp-alert")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    fatigue = FatigueControlService(session)
    tagged = await fatigue.tag_alert_as_false_positive("fp-alert", actor="reviewer")

    assert tagged.labels.get("false_positive") == "true"
    assert "false_positive_tagged_at" in tagged.labels
    assert tagged.labels.get("false_positive_tagged_by") == "reviewer"


@pytest.mark.asyncio
async def test_get_noisy_alerts(session: AsyncSession):
    """Test getting noisy alerts for review."""
    alert_repo = AlertRepository(session)
    notif_repo = NotificationRepository(session)

    # Create alerts with different notification counts
    for i in range(5):
        alert = _alert(f"alert-{i}")
        alert.started_at = datetime.utcnow() - timedelta(days=1)
        await alert_repo.upsert_alert(alert)

        # Create notifications for some alerts
        if i < 3:
            for j in range(i + 1):  # 0, 1, 2 notifications
                notification = Notification(
                    notification_id=f"notif-{i}-{j}",
                    tenant_id="tenant-test",
                    alert_id=f"alert-{i}",
                    target_id="user-1",
                    channel="email",
                    status="sent",
                    created_at=datetime.utcnow() - timedelta(hours=12),
                )
                await notif_repo.save(notification)

    fatigue = FatigueControlService(session)
    noisy = await fatigue.get_noisy_alerts(limit=10, days=7)

    # Should include the alerts we created
    assert len(noisy) >= 3
    created_ids = {"alert-0", "alert-1", "alert-2"}
    returned_ids = {a.alert_id for a in noisy}
    assert created_ids.issubset(returned_ids)


@pytest.mark.asyncio
async def test_export_noisy_alerts_report(session: AsyncSession):
    """Test exporting noisy alerts report."""
    alert_repo = AlertRepository(session)
    notif_repo = NotificationRepository(session)

    alert = _alert("report-alert")
    alert.started_at = datetime.utcnow() - timedelta(days=1)
    await alert_repo.upsert_alert(alert)

    # Create some notifications
    for i in range(3):
        notification = Notification(
            notification_id=f"report-notif-{i}",
            tenant_id="tenant-test",
            alert_id="report-alert",
            target_id="user-1",
            channel="email",
            status="sent",
            created_at=datetime.utcnow() - timedelta(hours=12),
        )
        await notif_repo.save(notification)

    fatigue = FatigueControlService(session)
    report = await fatigue.export_noisy_alerts_report(limit=10, days=7)

    assert "generated_at" in report
    assert "total_alerts" in report
    assert "alerts" in report
    assert len(report["alerts"]) > 0
    assert any(a["alert_id"] == "report-alert" for a in report["alerts"])
    assert report["alerts"][0]["notification_count"] >= 3

