"""Safe-to-Act HTTP endpoint."""

from fastapi import APIRouter, Depends

from ..models import SafeToActRequest, SafeToActResponse
from ..security import ensure_tenant_access, require_scope
from ..service_container import (
    get_db_session,
    get_rollup_service,
    get_safe_to_act_service,
    get_telemetry_service,
)
from ..services.rollup_service import RollupService
from ..services.safe_to_act_service import SafeToActService
from ..services.telemetry_ingestion_service import TelemetryIngestionService

router = APIRouter()


def _rollup(session=Depends(get_db_session)) -> RollupService:
    return get_rollup_service(session)


def _telemetry() -> TelemetryIngestionService:
    return get_telemetry_service()


def _safe_service(
    rollup: RollupService = Depends(_rollup),
    telemetry: TelemetryIngestionService = Depends(_telemetry),
) -> SafeToActService:
    return get_safe_to_act_service(rollup, telemetry)


@router.post(
    "/check_safe_to_act",
    response_model=SafeToActResponse,
    summary="Evaluate Safe-to-Act decision",
)
async def check_safe_to_act(
    request: SafeToActRequest,
    service: SafeToActService = Depends(_safe_service),
    claims=Depends(require_scope),
):
    """Implements Safe-to-Act API with deterministic degraded fallback."""
    ensure_tenant_access(claims, request.tenant_id)
    return await service.evaluate(request)

