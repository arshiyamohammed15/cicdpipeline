"""Health status & telemetry endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from ..database import models as db_models
from ..models import (
    HealthSnapshot,
    PlaneHealthView,
    SafeToActResponse,
    TelemetryPayload,
    TenantHealthView,
    SLOStatus,
)
from ..security import ensure_cross_plane_access, ensure_tenant_access, require_scope
from ..service_container import (
    get_db_session,
    get_audit_service,
    get_evaluation_service,
    get_rollup_service,
    get_slo_service,
    get_telemetry_service,
)
from ..services.telemetry_ingestion_service import TelemetryIngestionService
from ..services.evaluation_service import HealthEvaluationService
from ..services.rollup_service import RollupService
from ..services.slo_service import SLOService
from ..services.audit_service import AuditService

router = APIRouter()


def _telemetry_service() -> TelemetryIngestionService:
    return get_telemetry_service()


def _rollup_service(session=Depends(get_db_session)) -> RollupService:
    return get_rollup_service(session)


def _slo_service(session=Depends(get_db_session)) -> SLOService:
    return get_slo_service(session)


def _audit_service() -> AuditService:
    return get_audit_service()


def _db(session=Depends(get_db_session)):
    return session


@router.post(
    "/telemetry",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest telemetry payload (metrics/probe/heartbeat)",
)
async def ingest_telemetry(
    payload: TelemetryPayload,
    telemetry: TelemetryIngestionService = Depends(_telemetry_service),
    session=Depends(_db),
    sync: bool = Query(False, description="Force synchronous evaluation (testing only)"),
    claims=Depends(require_scope),
):
    """Test harness endpoint for telemetry ingestion (actual deployments use CCP-4 pipelines)."""
    ensure_tenant_access(claims, payload.tenant_id)
    await telemetry.ingest(payload)
    if sync:
        evaluator = get_evaluation_service(session)
        batch = await telemetry.drain()
        if batch:
            await evaluator.evaluate_batch(batch)
    return {"accepted": 1}


@router.get(
    "/components/{component_id}/status",
    response_model=HealthSnapshot,
    summary="Latest component health",
)
def get_component_status(component_id: str, session=Depends(_db), claims=Depends(require_scope)):
    """Return most recent snapshot for a component."""
    stmt = (
        select(db_models.HealthSnapshot)
        .where(db_models.HealthSnapshot.component_id == component_id)
        .order_by(db_models.HealthSnapshot.evaluated_at.desc())
    )
    result = session.scalars(stmt).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No health snapshots")

    return HealthSnapshot(
        snapshot_id=result.snapshot_id,
        component_id=result.component_id,
        tenant_id=result.tenant_id,
        plane=result.plane,
        environment=result.environment,
        state=result.state,  # type: ignore[arg-type]
        reason_code=result.reason_code,
        metrics_summary=result.metrics_summary,
        slo_state=result.slo_state,  # type: ignore[arg-type]
        policy_version=result.policy_version,
        evaluated_at=result.evaluated_at,
    )


@router.get(
    "/tenants/{tenant_id}",
    response_model=TenantHealthView,
    summary="Tenant health roll-up",
)
async def get_tenant_health(
    tenant_id: str,
    rollup: RollupService = Depends(_rollup_service),
    audit: AuditService = Depends(_audit_service),
    claims=Depends(require_scope),
):
    """Return cross-plane state for a tenant."""
    ensure_tenant_access(claims, tenant_id)
    view = rollup.tenant_view(tenant_id)
    await audit.record_access({"actor": "api", "tenant_id": tenant_id}, resource=f"tenant:{tenant_id}", action="read_health")
    return view


@router.get(
    "/planes/{plane}/{environment}",
    response_model=PlaneHealthView,
    summary="Plane health roll-up",
)
async def get_plane_health(
    plane: str,
    environment: str,
    rollup: RollupService = Depends(_rollup_service),
    audit: AuditService = Depends(_audit_service),
    claims=Depends(require_scope),
):
    """Return aggregated plane state."""
    ensure_cross_plane_access(claims)
    view = rollup.plane_view(plane, environment)
    await audit.record_access({"actor": "api"}, resource=f"plane:{plane}:{environment}", action="read_health")
    return view


@router.get(
    "/components/{component_id}/slo",
    response_model=SLOStatus,
    summary="Retrieve latest SLO status for a component",
)
def get_component_slo(
    component_id: str,
    service: SLOService = Depends(_slo_service),
    claims=Depends(require_scope),
):
    """Expose SLO posture per FR-6."""
    slo = service.latest_slo(component_id)
    if not slo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SLO data not available")
    return slo

