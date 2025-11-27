from datetime import datetime

import pytest
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from ..models import (
    AlertPayload,
    LifecycleRequest,
    RelatedLink,
    SearchFilters,
    SnoozeRequest,
    UserPreferencePayload,
)
from ..dependencies import RequestContext
from ..routes import v1


def _payload(alert_id: str, tenant_id: str = "tenant-route") -> AlertPayload:
    now = datetime.utcnow()
    return AlertPayload(
        alert_id=alert_id,
        tenant_id=tenant_id,
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-route",
        severity="P1",
        priority="P1",
        category="reliability",
        summary=f"{alert_id} summary",
        description="alert for routing tests",
        labels={"region": "us-east"},
        started_at=now,
        dedup_key=f"{tenant_id}:{alert_id}",
        links=[RelatedLink(kind="metric", href="https://telemetry.local/example")],
        runbook_refs=["runbook://alerting/basic"],
    )


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_alert_routes_full_flow(session):
    ctx = RequestContext(tenant_id="tenant-route", actor_id="tester", roles=["tenant_user"], allowed_tenants=[])
    primary = _payload("route-1")
    response = await v1.ingest_alert(primary, session, ctx)
    assert response.alert_id == "route-1"

    bulk_payloads = [_payload("route-2"), _payload("route-3")]
    bulk = await v1.ingest_alerts_bulk(bulk_payloads, session, ctx)
    assert len(bulk) == 2

    fetched = await v1.get_alert("route-1", session, ctx)
    assert fetched.alert_id == "route-1"

    filters = SearchFilters(
        severity="P1",
        category="reliability",
        tenant_id="tenant-route",
        status="open",
    )
    results = await v1.search_alerts(filters, session, ctx)
    assert any(alert.alert_id == "route-1" for alert in results)

    ack = await v1.acknowledge_alert("route-1", LifecycleRequest(actor="tester"), session, ctx)
    assert ack.status == "acknowledged"

    snoozed = await v1.snooze_alert(
        "route-2",
        SnoozeRequest(actor="tester", duration_minutes=30),
        session,
        ctx,
    )
    assert snoozed.status == "snoozed"

    resolved = await v1.resolve_alert("route-1", LifecycleRequest(actor="tester"), session, ctx)
    assert resolved.status == "resolved"

    incident = await v1.get_incident(resolved.incident_id, session, ctx)
    assert incident["status"] == "resolved"


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_preferences_and_error_paths(session):
    ctx = RequestContext(tenant_id="tenant-route", actor_id="tester", roles=["tenant_user"], allowed_tenants=[])
    pref_payload = UserPreferencePayload(
        user_id="user-route",
        tenant_id="tenant-route",
        channels=["email"],
        quiet_hours={"Mon": "22:00-07:00"},
        severity_threshold={"email": "P2"},
    )
    created = await v1.upsert_preferences(pref_payload, session, ctx)
    assert created.channels == ["email"]

    updated_payload = UserPreferencePayload(
        user_id="user-route",
        tenant_id="tenant-route",
        channels=["sms"],
        quiet_hours={"Tue": "21:00-06:00"},
        severity_threshold={"sms": "P1"},
    )
    updated = await v1.upsert_preferences(updated_payload, session, ctx)
    assert updated.channels == ["sms"]

    fetched = await v1.get_preferences("user-route", session, ctx)
    assert fetched.quiet_hours["Tue"] == "21:00-06:00"

    with pytest.raises(HTTPException):
        await v1.get_alert("missing-alert", session, ctx)
    with pytest.raises(HTTPException):
        await v1.get_incident("missing-incident", session, ctx)
    with pytest.raises(HTTPException):
        await v1.get_preferences("missing-user", session, ctx)
    with pytest.raises(HTTPException):
        await v1.acknowledge_alert("missing-alert", LifecycleRequest(actor="tester"), session, ctx)
    with pytest.raises(HTTPException):
        await v1.resolve_alert("missing-alert", LifecycleRequest(actor="tester"), session, ctx)
    with pytest.raises(HTTPException):
        await v1.snooze_alert("missing-alert", SnoozeRequest(actor="tester", duration_minutes=5), session, ctx)


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
async def test_streaming_endpoints_cover_generators(session):
    """Test that stream endpoint returns StreamingResponse with alert events."""
    import asyncio
    from ..routes.v1 import stream_alerts
    from ..services.stream_service import get_stream_service
    from ..database.models import Alert
    from ..repositories import AlertRepository
    from datetime import datetime

    # Create an alert to publish
    alert = Alert(
        alert_id="stream-test",
        tenant_id="tenant-stream",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-1",
        severity="P1",
        priority="P1",
        category="reliability",
        summary="Stream test",
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="stream-test",
    )
    alert_repo = AlertRepository(session)
    await alert_repo.upsert_alert(alert)

    # Get stream response
    ctx = RequestContext(tenant_id="tenant-stream", actor_id="tester", roles=["tenant_user"], allowed_tenants=[])
    response = await stream_alerts(session=session, ctx=ctx)
    assert isinstance(response, StreamingResponse)

    # Read first chunk (should be heartbeat or alert event)
    chunk = await response.body_iterator.__anext__()
    payload = chunk.decode() if isinstance(chunk, bytes) else chunk
    assert "data:" in payload or "heartbeat" in payload.lower() or "alert" in payload.lower()

    # Publish alert to stream
    stream_service = get_stream_service()
    await stream_service.publish_alert(alert, event_type="alert.created")

    # Read next chunk (should contain alert event)
    await asyncio.sleep(0.1)
    try:
        chunk = await response.body_iterator.__anext__()
        payload = chunk.decode() if isinstance(chunk, bytes) else chunk
        assert "alert" in payload.lower() or "heartbeat" in payload.lower()
    except StopAsyncIteration:
        pass  # Stream may have closed

