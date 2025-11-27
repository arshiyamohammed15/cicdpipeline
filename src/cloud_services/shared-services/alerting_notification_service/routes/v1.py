"""Versioned API router for Alerting & Notification Service."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..clients.policy_client import PolicyClient
from ..database.models import Alert, Incident, UserNotificationPreference
from ..dependencies import RequestContext, get_request_context, get_session
from ..models import (
    AlertPayload,
    AlertResponse,
    LifecycleRequest,
    SearchFilters,
    SnoozeRequest,
    UserPreferencePayload,
)
from ..repositories import NotificationRepository
from ..services.escalation_service import EscalationService
from ..services.ingestion_service import AlertIngestionService
from ..services.lifecycle_service import LifecycleService
from ..services.routing_service import RoutingService
from ..services.evidence_service import EvidenceService

router = APIRouter()
_evidence_service = EvidenceService()


async def _ensure_tenant_access(
    ctx: RequestContext,
    tenant_id: str,
    endpoint: str,
    method: str,
) -> None:
    if tenant_id == ctx.tenant_id:
        return
    if ctx.can_access(tenant_id):
        await _evidence_service.record_meta_access(
            actor=ctx.actor_id,
            actor_roles=ctx.roles,
            tenant_id=tenant_id,
            endpoint=endpoint,
            method=method,
        )
        return
    raise HTTPException(status_code=403, detail="Tenant access forbidden")


async def _build_alert_model(payload: AlertPayload) -> Alert:
    data = payload.model_dump()
    data.setdefault("last_seen_at", payload.started_at)
    data.setdefault("status", "open")
    return Alert(**data)


@router.post("/alerts", response_model=AlertResponse)
async def ingest_alert(
    payload: AlertPayload,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    await _ensure_tenant_access(ctx, payload.tenant_id, "/v1/alerts", "POST")
    alert_model = await _build_alert_model(payload)
    ingestion = AlertIngestionService(session)
    saved = await ingestion.ingest(alert_model)

    # Route alert and create initial notifications
    from ..services.fatigue_control import FatigueControlService
    from ..services.preference_service import UserPreferenceService

    notification_repo = NotificationRepository(session)
    preference_service = UserPreferenceService(session)
    fatigue_control = FatigueControlService(session)
    routing = RoutingService(
        notification_repo, preference_service=preference_service, fatigue_control=fatigue_control
    )
    notifications = await routing.route_alert(saved)

    # Trigger initial escalation step (step 1 with delay=0)
    escalation = EscalationService(session, notification_repo=notification_repo)
    escalation_notifications = await escalation.execute_escalation(saved, current_step=1)
    notifications.extend(escalation_notifications)

    return AlertResponse(alert_id=saved.alert_id, status=saved.status, incident_id=saved.incident_id)


@router.post("/alerts/bulk", response_model=List[AlertResponse])
async def ingest_alerts_bulk(
    payloads: List[AlertPayload],
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    responses = []
    for payload in payloads:
        responses.append(await ingest_alert(payload, session, ctx))
    return responses


@router.post("/alerts/{alert_id}/ack", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    request: LifecycleRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    lifecycle = LifecycleService(session)
    existing = await lifecycle.fetch_alert(alert_id)
    if not existing:
        raise HTTPException(status_code=404, detail="alert not found")
    await _ensure_tenant_access(ctx, existing.tenant_id, f"/v1/alerts/{alert_id}/ack", "POST")
    try:
        alert = await lifecycle.acknowledge(alert_id, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertResponse(alert_id=alert.alert_id, status=alert.status, incident_id=alert.incident_id)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    request: LifecycleRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    lifecycle = LifecycleService(session)
    existing = await lifecycle.fetch_alert(alert_id)
    if not existing:
        raise HTTPException(status_code=404, detail="alert not found")
    await _ensure_tenant_access(ctx, existing.tenant_id, f"/v1/alerts/{alert_id}/resolve", "POST")
    try:
        alert = await lifecycle.resolve(alert_id, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertResponse(alert_id=alert.alert_id, status=alert.status, incident_id=alert.incident_id)


@router.post("/alerts/{alert_id}/snooze", response_model=AlertResponse)
async def snooze_alert(
    alert_id: str,
    request: SnoozeRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    lifecycle = LifecycleService(session)
    existing = await lifecycle.fetch_alert(alert_id)
    if not existing:
        raise HTTPException(status_code=404, detail="alert not found")
    await _ensure_tenant_access(ctx, existing.tenant_id, f"/v1/alerts/{alert_id}/snooze", "POST")
    try:
        alert = await lifecycle.snooze(alert_id, duration_minutes=request.duration_minutes, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertResponse(alert_id=alert.alert_id, status=alert.status, incident_id=alert.incident_id)


@router.get("/alerts/{alert_id}", response_model=AlertPayload)
async def get_alert(
    alert_id: str,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    lifecycle = LifecycleService(session)
    # Check and auto-unsnooze if expired
    await lifecycle.check_and_unsnooze(alert_id)
    alert = await session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    await _ensure_tenant_access(ctx, alert.tenant_id, f"/v1/alerts/{alert_id}", "GET")
    return AlertPayload.model_validate(alert.model_dump())


@router.post("/alerts/search", response_model=List[AlertPayload])
async def search_alerts(
    filters: SearchFilters,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    statement = select(Alert)
    if filters.severity:
        statement = statement.where(Alert.severity == filters.severity)
    if filters.category:
        statement = statement.where(Alert.category == filters.category)
    tenant_filter = filters.tenant_id or ctx.tenant_id
    await _ensure_tenant_access(ctx, tenant_filter, "/v1/alerts/search", "POST")
    statement = statement.where(Alert.tenant_id == tenant_filter)
    if filters.status:
        statement = statement.where(Alert.status == filters.status)
    result = await session.exec(statement.order_by(Alert.started_at.desc()).limit(100))
    alerts = result.scalars().all()
    return [AlertPayload.model_validate(alert.model_dump()) for alert in alerts]


@router.get("/alerts/stream")
async def stream_alerts(
    tenant_id: Optional[str] = None,
    component_id: Optional[str] = None,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    event_types: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Stream alerts via HTTP SSE with optional filtering.
    
    Query Parameters:
        tenant_id: Filter by tenant ID (comma-separated for multiple)
        component_id: Filter by component ID (comma-separated for multiple)
        category: Filter by category (comma-separated for multiple)
        severity: Filter by severity (comma-separated for multiple)
        event_types: Filter by event types (comma-separated: alert.created, alert.updated, etc.)
    
    Returns:
        Server-Sent Events stream of alert events
    """
    from ..services.stream_service import StreamFilter, get_stream_service

    # Parse filter parameters
    tenant_ids = tenant_id.split(",") if tenant_id else None
    component_ids = component_id.split(",") if component_id else None
    categories = category.split(",") if category else None
    severities = severity.split(",") if severity else None
    event_type_list = event_types.split(",") if event_types else None

    if tenant_ids:
        for tid in tenant_ids:
            await _ensure_tenant_access(ctx, tid, "/v1/alerts/stream", "GET")
    else:
        tenant_ids = [ctx.tenant_id]

    filter_criteria = StreamFilter(
        tenant_ids=tenant_ids,
        component_ids=component_ids,
        categories=categories,
        severities=severities,
        event_types=event_type_list,
    )

    stream_service = get_stream_service()
    subscription_id = f"sub-{datetime.utcnow().timestamp()}"

    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in stream_service.subscribe(subscription_id, filter_criteria):
                # Format as SSE
                event_json = json.dumps(event)
                yield f"data: {event_json}\n\n"
        finally:
            await stream_service.unsubscribe(subscription_id)

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.get("/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    incident = await session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")
    await _ensure_tenant_access(ctx, incident.tenant_id, f"/v1/incidents/{incident_id}", "GET")
    return incident.model_dump()


@router.post("/incidents/{incident_id}/mitigate")
async def mitigate_incident(
    incident_id: str,
    request: LifecycleRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    lifecycle = LifecycleService(session)
    incident = await session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")
    await _ensure_tenant_access(ctx, incident.tenant_id, f"/v1/incidents/{incident_id}/mitigate", "POST")
    try:
        mitigated = await lifecycle.mitigate_incident(incident_id, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return mitigated.model_dump()


@router.post("/incidents/{incident_id}/snooze")
async def snooze_incident(
    incident_id: str,
    request: SnoozeRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    lifecycle = LifecycleService(session)
    incident = await session.get(Incident, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="incident not found")
    await _ensure_tenant_access(ctx, incident.tenant_id, f"/v1/incidents/{incident_id}/snooze", "POST")
    try:
        snoozed = await lifecycle.snooze_incident(incident_id, duration_minutes=request.duration_minutes, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return snoozed.model_dump()


@router.post("/preferences", response_model=UserPreferencePayload)
async def upsert_preferences(
    payload: UserPreferencePayload,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    await _ensure_tenant_access(ctx, payload.tenant_id, "/v1/preferences", "POST")
    pref = await session.get(UserNotificationPreference, payload.user_id)
    if pref:
        for field, value in payload.model_dump().items():
            setattr(pref, field, value)
    else:
        pref = UserNotificationPreference(**payload.model_dump())
        session.add(pref)
    await session.commit()
    await session.refresh(pref)
    return UserPreferencePayload.model_validate(pref.model_dump())


@router.get("/preferences/{user_id}", response_model=UserPreferencePayload)
async def get_preferences(
    user_id: str,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    pref = await session.get(UserNotificationPreference, user_id)
    if not pref:
        raise HTTPException(status_code=404, detail="preference not found")
    await _ensure_tenant_access(ctx, pref.tenant_id, f"/v1/preferences/{user_id}", "GET")
    return UserPreferencePayload.model_validate(pref.model_dump())


@router.post("/alerts/{alert_id}/tag/noisy")
async def tag_alert_noisy(
    alert_id: str,
    request: LifecycleRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    from ..services.fatigue_control import FatigueControlService

    fatigue = FatigueControlService(session)
    alert = await fatigue.alert_repo.fetch(alert_id)  # type: ignore[attr-defined]
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    await _ensure_tenant_access(ctx, alert.tenant_id, f"/v1/alerts/{alert_id}/tag/noisy", "POST")
    try:
        alert = await fatigue.tag_alert_as_noisy(alert_id, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertResponse(alert_id=alert.alert_id, status=alert.status, incident_id=alert.incident_id)


@router.post("/alerts/{alert_id}/tag/false-positive")
async def tag_alert_false_positive(
    alert_id: str,
    request: LifecycleRequest,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    from ..services.fatigue_control import FatigueControlService

    fatigue = FatigueControlService(session)
    alert = await fatigue.alert_repo.fetch(alert_id)  # type: ignore[attr-defined]
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    await _ensure_tenant_access(ctx, alert.tenant_id, f"/v1/alerts/{alert_id}/tag/false-positive", "POST")
    try:
        alert = await fatigue.tag_alert_as_false_positive(alert_id, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertResponse(alert_id=alert.alert_id, status=alert.status, incident_id=alert.incident_id)


@router.get("/alerts/noisy/report")
async def get_noisy_alerts_report(
    tenant_id: Optional[str] = None,
    limit: int = 100,
    days: int = 30,
    session: AsyncSession = Depends(get_session),
    ctx: RequestContext = Depends(get_request_context),
):
    from ..services.fatigue_control import FatigueControlService

    target_tenant = tenant_id or ctx.tenant_id
    await _ensure_tenant_access(ctx, target_tenant, "/v1/alerts/noisy/report", "GET")
    fatigue = FatigueControlService(session)
    report = await fatigue.export_noisy_alerts_report(tenant_id=target_tenant, limit=limit, days=days)
    return report


@router.post("/admin/policy/refresh")
async def refresh_policy(
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Refresh policy bundle from Configuration & Policy Management API.
    
    Requires global_admin role or appropriate permissions.
    """
    # Check permissions (only admins can refresh policy)
    if "global_admin" not in ctx.roles and "admin" not in ctx.roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions to refresh policy")
    
    policy_client = PolicyClient()
    try:
        bundle = await policy_client.refresh_bundle()
        return {
            "status": "success",
            "message": "Policy bundle refreshed",
            "schema_version": bundle.get("schema_version"),
            "refreshed_at": datetime.utcnow().isoformat(),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to refresh policy: {str(exc)}")

