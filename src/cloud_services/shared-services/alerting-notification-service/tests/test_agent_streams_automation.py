"""Tests for agent streams and automation hooks."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from alerting_notification_service.database.models import Alert
from alerting_notification_service.repositories import AlertRepository
from alerting_notification_service.services.automation_service import AutomationService
from alerting_notification_service.services.stream_service import AlertStreamService, StreamFilter, get_stream_service


def _alert(alert_id: str, tenant: str = "tenant-stream", automation_hooks: list[str] | None = None) -> Alert:
    now = datetime.utcnow()
    return Alert(
        alert_id=alert_id,
        tenant_id=tenant,
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-stream",
        severity="P1",
        priority="P1",
        category="reliability",
        summary=f"Alert {alert_id}",
        labels={},
        started_at=now,
        last_seen_at=now,
        dedup_key=f"{tenant}:{alert_id}",
        automation_hooks=automation_hooks or [],
    )


@pytest.mark.asyncio
async def test_stream_service_publish_and_subscribe():
    """Test that stream service publishes alerts to subscribers."""
    service = AlertStreamService()
    subscription_id = "test-sub-1"

    # Start subscription
    events = []
    subscription_task = asyncio.create_task(
        _collect_events(service.subscribe(subscription_id), events, max_events=2)
    )

    # Give subscription time to start
    await asyncio.sleep(0.1)

    # Publish alert
    alert = _alert("stream-test-1")
    await service.publish_alert(alert, event_type="alert.created")

    # Wait for event
    await asyncio.sleep(0.1)

    # Unsubscribe
    await service.unsubscribe(subscription_id)
    await subscription_task

    assert len(events) >= 1
    assert events[0]["event_type"] == "alert.created"
    assert events[0]["alert"]["alert_id"] == "stream-test-1"


async def _collect_events(stream, events: list, max_events: int = 10):
    """Helper to collect events from stream."""
    count = 0
    async for event in stream:
        if event.get("event_type") != "heartbeat":
            events.append(event)
            count += 1
            if count >= max_events:
                break


@pytest.mark.asyncio
async def test_stream_filter_tenant():
    """Test that stream filter filters by tenant."""
    service = AlertStreamService()
    subscription_id = "test-filter-tenant"

    filter_criteria = StreamFilter(tenant_ids=["tenant-a"])
    events = []
    subscription_task = asyncio.create_task(
        _collect_events(service.subscribe(subscription_id, filter_criteria), events, max_events=2)
    )

    await asyncio.sleep(0.1)

    # Publish alerts for different tenants
    alert_a = _alert("alert-a", tenant="tenant-a")
    alert_b = _alert("alert-b", tenant="tenant-b")
    await service.publish_alert(alert_a, event_type="alert.created")
    await service.publish_alert(alert_b, event_type="alert.created")

    await asyncio.sleep(0.1)
    await service.unsubscribe(subscription_id)
    await subscription_task

    # Should only receive tenant-a alert
    tenant_ids = {e["alert"]["tenant_id"] for e in events if e.get("event_type") != "heartbeat"}
    assert "tenant-a" in tenant_ids
    assert "tenant-b" not in tenant_ids


@pytest.mark.asyncio
async def test_stream_filter_severity():
    """Test that stream filter filters by severity."""
    service = AlertStreamService()
    subscription_id = "test-filter-severity"

    filter_criteria = StreamFilter(severities=["P0", "P1"])
    events = []
    subscription_task = asyncio.create_task(
        _collect_events(service.subscribe(subscription_id, filter_criteria), events, max_events=3)
    )

    await asyncio.sleep(0.1)

    # Publish alerts with different severities
    alert_p0 = _alert("alert-p0")
    alert_p0.severity = "P0"
    alert_p1 = _alert("alert-p1")
    alert_p1.severity = "P1"
    alert_p2 = _alert("alert-p2")
    alert_p2.severity = "P2"

    await service.publish_alert(alert_p0, event_type="alert.created")
    await service.publish_alert(alert_p1, event_type="alert.created")
    await service.publish_alert(alert_p2, event_type="alert.created")

    await asyncio.sleep(0.1)
    await service.unsubscribe(subscription_id)
    await subscription_task

    # Should only receive P0 and P1 alerts
    severities = {e["alert"]["severity"] for e in events if e.get("event_type") != "heartbeat"}
    assert "P0" in severities
    assert "P1" in severities
    assert "P2" not in severities


@pytest.mark.asyncio
async def test_stream_filter_event_types():
    """Test that stream filter filters by event type."""
    service = AlertStreamService()
    subscription_id = "test-filter-events"

    filter_criteria = StreamFilter(event_types=["alert.created"])
    events = []
    subscription_task = asyncio.create_task(
        _collect_events(service.subscribe(subscription_id, filter_criteria), events, max_events=3)
    )

    await asyncio.sleep(0.1)

    alert = _alert("alert-events")
    await service.publish_alert(alert, event_type="alert.created")
    await service.publish_alert(alert, event_type="alert.acknowledged")
    await service.publish_alert(alert, event_type="alert.resolved")

    await asyncio.sleep(0.1)
    await service.unsubscribe(subscription_id)
    await subscription_task

    # Should only receive alert.created events
    event_types = {e["event_type"] for e in events if e.get("event_type") != "heartbeat"}
    assert "alert.created" in event_types
    assert "alert.acknowledged" not in event_types
    assert "alert.resolved" not in event_types


@pytest.mark.asyncio
async def test_automation_service_triggers_hooks(session: AsyncSession):
    """Test that automation service triggers hooks."""
    alert = _alert("automation-test", automation_hooks=["http://automation.local/hook1", "hook://local/remediate"])
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    automation = AutomationService(session)
    results = await automation.trigger_automation_hooks(alert)

    assert len(results) == 2
    # Both hooks should be attempted
    hook_urls = {r["hook_url"] for r in results}
    assert "http://automation.local/hook1" in hook_urls
    assert "hook://local/remediate" in hook_urls


@pytest.mark.asyncio
async def test_automation_service_no_hooks(session: AsyncSession):
    """Test that automation service handles alerts without hooks."""
    alert = _alert("no-hooks")
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    automation = AutomationService(session)
    results = await automation.trigger_automation_hooks(alert)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_stream_service_format_alert_event():
    """Test that alert events are formatted correctly."""
    service = AlertStreamService()
    alert = _alert("format-test")
    alert.automation_hooks = ["hook://test"]
    alert.runbook_refs = ["runbook://test"]
    alert.links = [{"type": "trace", "url": "https://trace.local/123"}]

    event = service._format_alert_event(alert, "alert.created")

    assert event["event_type"] == "alert.created"
    assert "timestamp" in event
    assert "alert" in event
    assert event["alert"]["alert_id"] == "format-test"
    assert event["alert"]["automation_hooks"] == ["hook://test"]
    assert event["alert"]["runbook_refs"] == ["runbook://test"]
    assert event["alert"]["links"] == [{"type": "trace", "url": "https://trace.local/123"}]


@pytest.mark.asyncio
async def test_get_stream_service_singleton():
    """Test that get_stream_service returns singleton."""
    service1 = get_stream_service()
    service2 = get_stream_service()
    assert service1 is service2


@pytest.mark.asyncio
async def test_stream_filter_labels():
    """Test that stream filter filters by labels."""
    service = AlertStreamService()
    subscription_id = "test-filter-labels"

    filter_criteria = StreamFilter(labels={"team": "platform"})
    events = []
    subscription_task = asyncio.create_task(
        _collect_events(service.subscribe(subscription_id, filter_criteria), events, max_events=2)
    )

    await asyncio.sleep(0.1)

    # Publish alerts with different labels
    alert_match = _alert("alert-match")
    alert_match.labels = {"team": "platform", "env": "prod"}
    alert_no_match = _alert("alert-no-match")
    alert_no_match.labels = {"team": "backend", "env": "prod"}

    await service.publish_alert(alert_match, event_type="alert.created")
    await service.publish_alert(alert_no_match, event_type="alert.created")

    await asyncio.sleep(0.1)
    await service.unsubscribe(subscription_id)
    await subscription_task

    # Should only receive alert with matching label
    alert_ids = {e["alert"]["alert_id"] for e in events if e.get("event_type") != "heartbeat"}
    assert "alert-match" in alert_ids
    assert "alert-no-match" not in alert_ids

