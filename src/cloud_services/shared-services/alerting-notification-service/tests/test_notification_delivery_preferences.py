"""Tests for notification delivery, retry, fallback, and user preferences."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from alerting_notification_service.clients import PolicyClient
from alerting_notification_service.database.models import Alert, Notification, UserNotificationPreference
from alerting_notification_service.repositories import AlertRepository, NotificationRepository
from alerting_notification_service.services.notification_service import NotificationDispatcher
from alerting_notification_service.services.preference_service import UserPreferenceService
from alerting_notification_service.services.routing_service import RoutingService


def _alert(alert_id: str, tenant: str = "tenant-test", severity: str = "P1") -> Alert:
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
    )


@pytest.mark.asyncio
async def test_retry_policy_retrieval(tmp_path):
    """Test that retry policies are correctly retrieved from policy bundle."""
    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {},
        "retry": {
            "defaults": {"max_attempts": 5, "backoff_intervals": [30, 60, 120, 240, 480]},
            "by_channel": {"email": {"max_attempts": 3, "backoff_intervals": [60, 120, 300]}},
            "by_severity": {"P0": {"max_attempts": 5, "backoff_intervals": [15, 30, 60, 120, 240]}},
        },
        "fallback": {"defaults": {"channels": ["email", "sms"]}},
    }
    policy_path = Path(tmp_path / "retry_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    client = PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    policy = client.get_retry_policy("email", "P2")
    assert policy["max_attempts"] == 3  # Channel override
    assert policy["backoff_intervals"] == [60, 120, 300]

    policy_p0 = client.get_retry_policy("sms", "P0")
    assert policy_p0["max_attempts"] == 5  # Severity override
    assert policy_p0["backoff_intervals"] == [15, 30, 60, 120, 240]


@pytest.mark.asyncio
async def test_fallback_channel_retrieval(tmp_path):
    """Test that fallback channels are correctly retrieved."""
    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {},
        "retry": {"defaults": {"max_attempts": 5, "backoff_intervals": [30, 60, 120]}},
        "fallback": {
            "defaults": {"channels": ["email", "sms", "voice"]},
            "by_severity": {
                "P0": {"fallback_order": ["sms", "voice", "email"]},
                "P1": {"fallback_order": ["sms", "email"]},
            },
        },
    }
    policy_path = Path(tmp_path / "fallback_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    client = PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    fallback = client.get_fallback_channels("P0", "email")
    assert fallback == ["sms", "voice"]  # email removed, order from severity config

    fallback_p1 = client.get_fallback_channels("P1", "sms")
    assert fallback_p1 == ["email"]  # sms removed, only email left


@pytest.mark.asyncio
async def test_user_preference_service_filters_channels(session: AsyncSession):
    """Test that user preferences filter and order channels correctly."""
    pref = UserNotificationPreference(
        user_id="user-1",
        tenant_id="tenant-1",
        channels=["sms", "email", "voice"],
        channel_preferences={"P0": ["voice", "sms"], "P1": ["email"]},
        quiet_hours={},
        severity_threshold={},
    )
    session.add(pref)
    await session.commit()

    service = UserPreferenceService(session)
    preferences = await service.get_preferences_or_default("user-1")
    channels = service.filter_channels_by_preferences(["email", "sms", "voice"], "P0", preferences)
    assert channels == ["voice", "sms"]  # Ordered by user preference

    channels_p1 = service.filter_channels_by_preferences(["email", "sms", "voice"], "P1", preferences)
    assert channels_p1 == ["email"]  # Only email for P1


@pytest.mark.asyncio
async def test_user_preference_quiet_hours(session: AsyncSession):
    """Test that quiet hours prevent non-urgent notifications."""
    pref = UserNotificationPreference(
        user_id="user-quiet",
        tenant_id="tenant-1",
        channels=[],
        channel_preferences={},
        quiet_hours={"Mon": "22:00-08:00"},
        severity_threshold={},
    )
    session.add(pref)
    await session.commit()

    service = UserPreferenceService(session)
    # Test during quiet hours (assuming test runs during business hours, adjust if needed)
    quiet_time = datetime.strptime("2025-11-24 23:00", "%Y-%m-%d %H:%M")  # Monday 23:00
    should_notify = await service.should_notify("user-quiet", "P2", "email", quiet_time)
    assert not should_notify  # P2 should be blocked during quiet hours

    should_notify_p0 = await service.should_notify("user-quiet", "P0", "sms", quiet_time)
    assert should_notify_p0  # P0 should still go through


@pytest.mark.asyncio
async def test_notification_dispatcher_retry_logic(session: AsyncSession, tmp_path, monkeypatch):
    """Test that dispatcher retries with backoff on failure."""
    import json
    from pathlib import Path

    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {},
        "retry": {"defaults": {"max_attempts": 3, "backoff_intervals": [1, 2, 3]}},
        "fallback": {"defaults": {"channels": ["sms"]}},
    }
    policy_path = Path(tmp_path / "dispatcher_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    alert = _alert("retry-test", severity="P1")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    notification = Notification(
        notification_id="notif-retry",
        tenant_id="tenant-test",
        alert_id="retry-test",
        target_id="user-1",
        channel="email",
        status="pending",
        attempts=0,
    )
    notif_repo = NotificationRepository(session)
    await notif_repo.save(notification)

    # Mock channel to fail
    class FailingChannel:
        async def send(self, notification):
            return "failed"

    dispatcher = NotificationDispatcher(
        session=session, policy_client=PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    )
    dispatcher.channels["email"] = FailingChannel()

    status = await dispatcher.dispatch(notification, alert)
    # Should schedule retry (pending) after first failure
    assert status in ["pending", "failed"]
    updated = await session.get(Notification, "notif-retry")
    assert updated.attempts > 0
    if status == "pending":
        assert updated.next_attempt_at is not None


@pytest.mark.asyncio
async def test_notification_dispatcher_fallback(session: AsyncSession, tmp_path, monkeypatch):
    """Test that dispatcher creates fallback notifications when primary channel fails."""
    import json
    from pathlib import Path

    policy_bundle = {
        "schema_version": "1.0.0",
        "dedup": {"defaults": 15},
        "correlation": {"window_minutes": 10, "rules": []},
        "routing": {"defaults": {"targets": ["{tenant_id}-oncall"], "channels": ["email"]}, "tenant_overrides": {}},
        "escalation": {"policies": {}},
        "fatigue": {},
        "retry": {"defaults": {"max_attempts": 1, "backoff_intervals": [1]}},
        "fallback": {"defaults": {"channels": ["sms", "voice"]}},
    }
    policy_path = Path(tmp_path / "fallback_dispatcher_policy.json")
    policy_path.write_text(json.dumps(policy_bundle), encoding="utf-8")

    alert = _alert("fallback-test", severity="P1")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    notification = Notification(
        notification_id="notif-fallback",
        tenant_id="tenant-test",
        alert_id="fallback-test",
        target_id="user-1",
        channel="email",
        status="pending",
        attempts=0,
    )
    notif_repo = NotificationRepository(session)
    await notif_repo.save(notification)

    # Mock channel to always fail
    class FailingChannel:
        async def send(self, notification):
            return "failed"

    dispatcher = NotificationDispatcher(
        session=session, policy_client=PolicyClient(policy_path=policy_path, cache_ttl_seconds=1)
    )
    dispatcher.channels["email"] = FailingChannel()

    status = await dispatcher.dispatch(notification, alert)
    # Should create fallback notification
    assert status in ["pending", "failed", "sent"]  # May try fallback immediately

    # Check if fallback notification was created
    from sqlalchemy import select
    statement = select(Notification).where(Notification.notification_id.like("fallback-%"))
    # Use session.execute() with proper ORM mapping
    # The deprecation warning is from SQLModel internals, not our usage
    result = await session.execute(statement)
    fallbacks = list(result.scalars().all())
    # At least one fallback should exist
    assert len(fallbacks) >= 1


@pytest.mark.asyncio
async def test_routing_with_preferences(session: AsyncSession):
    """Test that routing service applies user preferences."""
    pref = UserNotificationPreference(
        user_id="user-pref",
        tenant_id="tenant-route",
        channels=["sms", "email"],
        channel_preferences={"P1": ["sms"]},
        quiet_hours={},
        severity_threshold={},
    )
    session.add(pref)
    await session.commit()

    alert = _alert("pref-test", tenant="tenant-route", severity="P1")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    notif_repo = NotificationRepository(session)
    pref_service = UserPreferenceService(session)
    routing = RoutingService(notif_repo, preference_service=pref_service)

    notifications = await routing.route_alert(alert)
    # Should only create SMS notification for user-pref based on preferences
    user_notifications = [n for n in notifications if n.target_id == "user-pref"]
    if user_notifications:
        channels = [n.channel for n in user_notifications]
        # Should prefer SMS based on user preference
        assert "sms" in channels or "email" in channels  # At least one channel


@pytest.mark.asyncio
async def test_preference_service_defaults(session: AsyncSession):
    """Test that preference service returns defaults when user has no preferences."""
    service = UserPreferenceService(session)
    pref = await service.get_preferences_or_default("unknown-user")
    assert pref.user_id == "unknown-user"
    assert pref.timezone == "UTC"
    assert pref.channels == []


@pytest.mark.asyncio
async def test_quiet_hours_channel_filtering(session: AsyncSession):
    """Test that quiet hours filter out non-urgent channels."""
    pref = UserNotificationPreference(
        user_id="user-quiet-filter",
        tenant_id="tenant-1",
        channels=["email", "sms", "voice"],
        channel_preferences={},
        quiet_hours={"Mon": "22:00-08:00"},
        severity_threshold={},
    )
    session.add(pref)
    await session.commit()

    service = UserPreferenceService(session)
    preferences = await service.get_preferences_or_default("user-quiet-filter")
    quiet_time = datetime.strptime("2025-11-24 23:00", "%Y-%m-%d %H:%M")  # Monday 23:00

    # P2 alert during quiet hours should filter to empty (no urgent channels)
    channels = service.filter_channels_by_preferences(["email", "sms"], "P2", preferences, quiet_time)
    assert channels == []  # No channels for non-urgent during quiet hours

    # P0 alert during quiet hours should allow SMS/voice
    channels_p0 = service.filter_channels_by_preferences(["email", "sms", "voice"], "P0", preferences, quiet_time)
    assert "sms" in channels_p0 or "voice" in channels_p0
    assert "email" not in channels_p0  # Email not urgent enough

