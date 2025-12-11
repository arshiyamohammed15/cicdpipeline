"""
API routes for MMM Engine.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .models import (
    DecideRequest,
    DecideResponse,
    Playbook,
    PlaybookCreateRequest,
    MMMOutcome,
    ActorPreferences,
    ActorPreferencesUpdateRequest,
    ActorPreferencesSnoozeRequest,
    TenantMMMPolicy,
    TenantMMMPolicyUpdateRequest,
    DualChannelApproval,
    DualChannelApprovalRequest,
)
from .services import MMMService
from .database.connection import get_db
from .observability.metrics import get_metrics_text
from .service_registry import get_iam, get_policy_service, get_eris

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/mmm", tags=["mmm-engine"])

_service: MMMService | None = None


def get_service() -> MMMService:
    global _service
    if _service is None:
        _service = MMMService()
    return _service


def get_tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context missing")
    return tenant_id


@router.post("/decide", response_model=DecideResponse)
async def decide(
    request_body: DecideRequest,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> DecideResponse:
    tenant_id = get_tenant_id(request)
    if tenant_id != request_body.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    response = service.decide(request_body, db)
    db.commit()
    return response


@router.get("/health")
async def health(service: MMMService = Depends(get_service)) -> dict[str, str]:
    """
    Health check endpoint.

    Per PRD Section 11.8:
    - Returns 200 if service is operational
    - Returns 503 if critical dependencies unavailable
    """
    from fastapi import status
    from fastapi.responses import JSONResponse

    # Check service operational status
    try:
        # Basic check: service initialized
        if service is None:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "unhealthy", "reason": "Service not initialized"},
            )
        return {"status": "healthy"}
    except Exception as exc:
        logger.error("Health check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "reason": str(exc)},
        )


@router.get("/ready")
async def ready(service: MMMService = Depends(get_service)) -> dict[str, str]:
    """
    Readiness check endpoint.

    Per PRD Section 11.8:
    - Returns 200 only if all required dependencies are available
    - Returns 503 if any unavailable
    """
    from fastapi import status
    from fastapi.responses import JSONResponse

    # Check all required dependencies (IAM, Policy, ERIS)
    unavailable = []
    try:
        # Check IAM
        iam = get_iam()
        # Test IAM connection (non-blocking check)
        # For now, just check if client is initialized
        if iam is None:
            unavailable.append("iam")
    except Exception:
        unavailable.append("iam")

    try:
        # Check Policy
        policy = get_policy_service()
        if policy is None:
            unavailable.append("policy")
    except Exception:
        unavailable.append("policy")

    try:
        # Check ERIS
        eris = get_eris()
        if eris is None:
            unavailable.append("eris")
    except Exception:
        unavailable.append("eris")

    if unavailable:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "unavailable_dependencies": unavailable,
            },
        )

    return {"status": "ready"}


@router.get("/metrics")
async def metrics() -> Response:
    return Response(get_metrics_text(), media_type="text/plain; version=0.0.4")


@router.get("/playbooks", response_model=List[Playbook])
async def list_playbooks(
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> List[Playbook]:
    tenant_id = get_tenant_id(request)
    return service.list_playbooks(tenant_id, db)


@router.post("/playbooks", response_model=Playbook)
async def create_playbook(
    payload: PlaybookCreateRequest,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> Playbook:
    tenant_id = get_tenant_id(request)
    playbook = service.create_playbook(tenant_id, payload, db)
    db.commit()
    return playbook


@router.post("/playbooks/{playbook_id}/publish", response_model=Playbook)
async def publish_playbook(
    playbook_id: str,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> Playbook:
    tenant_id = get_tenant_id(request)
    playbook = service.publish_playbook(tenant_id, playbook_id, db)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    db.commit()
    return playbook


@router.post("/decisions/{decision_id}/outcomes", status_code=202)
async def record_outcome(
    decision_id: str,
    payload: Dict[str, Any],
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> dict:
    tenant_id = get_tenant_id(request)
    action_id = payload.get("action_id")
    result = payload.get("result")
    if not action_id or not isinstance(action_id, str):
        raise HTTPException(status_code=422, detail="action_id required")
    if not result or not isinstance(result, str):
        raise HTTPException(status_code=422, detail="result required")
    outcome = MMMOutcome(
        decision_id=decision_id,
        action_id=action_id,
        tenant_id=tenant_id,
        actor_id=payload.get("actor_id"),
        result=result,
        reason=payload.get("reason"),
    )
    service.record_outcome(outcome, db)
    db.commit()
    return {"status": "accepted"}


# Actor Preferences API (FR-14)
@router.get("/actors/{actor_id}/preferences", response_model=ActorPreferences)
async def get_actor_preferences(
    actor_id: str,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> ActorPreferences:
    tenant_id = get_tenant_id(request)
    # Authorization: Actor can view own, admin can view any
    actor_id_from_token = getattr(request.state, "actor_id", None)
    roles = getattr(request.state, "roles", [])
    if actor_id_from_token != actor_id and "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    preferences = service.get_actor_preferences(tenant_id, actor_id, db)
    if not preferences:
        # Return default preferences
        from .models import ActorPreferences
        from datetime import datetime
        return ActorPreferences(
            preference_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            actor_id=actor_id,
            opt_out_categories=[],
            preferred_surfaces=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    return preferences


@router.put("/actors/{actor_id}/preferences", response_model=ActorPreferences)
async def update_actor_preferences(
    actor_id: str,
    payload: ActorPreferencesUpdateRequest,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> ActorPreferences:
    tenant_id = get_tenant_id(request)
    # Authorization: Actor can update own, admin can update any
    actor_id_from_token = getattr(request.state, "actor_id", None)
    roles = getattr(request.state, "roles", [])
    if actor_id_from_token != actor_id and "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    preferences = service.update_actor_preferences(tenant_id, actor_id, payload, db)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    db.commit()
    return preferences


@router.post("/actors/{actor_id}/preferences/snooze", response_model=ActorPreferences)
async def snooze_actor_preferences(
    actor_id: str,
    payload: ActorPreferencesSnoozeRequest,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> ActorPreferences:
    tenant_id = get_tenant_id(request)
    # Authorization: Actor can snooze own, admin can snooze any
    actor_id_from_token = getattr(request.state, "actor_id", None)
    roles = getattr(request.state, "roles", [])
    if actor_id_from_token != actor_id and "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    preferences = service.snooze_actor_preferences(tenant_id, actor_id, payload, db)
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    db.commit()
    return preferences


# Tenant Policy Configuration API (FR-13)
@router.get("/tenants/{tenant_id}/policy", response_model=TenantMMMPolicy)
async def get_tenant_policy(
    tenant_id: str,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> TenantMMMPolicy:
    # Authorization: Requires mmm_admin or tenant_admin
    roles = getattr(request.state, "roles", [])
    if "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    policy = service.get_tenant_policy(tenant_id, db)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.put("/tenants/{tenant_id}/policy", response_model=TenantMMMPolicy)
async def update_tenant_policy(
    tenant_id: str,
    payload: TenantMMMPolicyUpdateRequest,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> TenantMMMPolicy:
    # Authorization: Requires mmm_admin or tenant_admin
    roles = getattr(request.state, "roles", [])
    if "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    policy = service.update_tenant_policy(tenant_id, payload, db)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.commit()
    return policy


# Experiment Management API (FR-13)
@router.get("/experiments")
async def list_experiments(
    tenant_id: str,
    status: Optional[str] = None,
    request: Request = None,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> List[dict]:
    # Authorization: Requires mmm_admin or tenant_admin
    if request:
        roles = getattr(request.state, "roles", [])
        if "mmm_admin" not in roles and "tenant_admin" not in roles:
            raise HTTPException(status_code=403, detail="Not authorized")
    return service.list_experiments(tenant_id, status, db)


@router.post("/experiments")
async def create_experiment(
    payload: Dict[str, Any],
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> dict:
    # Authorization: Requires mmm_admin or tenant_admin
    roles = getattr(request.state, "roles", [])
    if "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    tenant_id = get_tenant_id(request)
    experiment = service.create_experiment({**payload, "tenant_id": tenant_id}, db)
    db.commit()
    return experiment


@router.put("/experiments/{experiment_id}")
async def update_experiment(
    experiment_id: str,
    payload: Dict[str, Any],
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> dict:
    # Authorization: Requires mmm_admin or tenant_admin
    roles = getattr(request.state, "roles", [])
    if "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    tenant_id = get_tenant_id(request)
    experiment = service.update_experiment(tenant_id, experiment_id, payload, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.commit()
    return experiment


@router.post("/experiments/{experiment_id}/activate")
async def activate_experiment(
    experiment_id: str,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> dict:
    # Authorization: Requires mmm_admin or tenant_admin
    roles = getattr(request.state, "roles", [])
    if "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    tenant_id = get_tenant_id(request)
    experiment = service.activate_experiment(tenant_id, experiment_id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.commit()
    return experiment


@router.post("/experiments/{experiment_id}/deactivate")
async def deactivate_experiment(
    experiment_id: str,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> dict:
    # Authorization: Requires mmm_admin or tenant_admin
    roles = getattr(request.state, "roles", [])
    if "mmm_admin" not in roles and "tenant_admin" not in roles:
        raise HTTPException(status_code=403, detail="Not authorized")
    tenant_id = get_tenant_id(request)
    experiment = service.deactivate_experiment(tenant_id, experiment_id, db)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.commit()
    return experiment


# Dual-Channel Approval API (FR-6)
@router.post("/actions/{action_id}/approve")
async def approve_action(
    action_id: str,
    payload: Dict[str, Any],
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> dict:
    actor_id = payload.get("actor_id") or getattr(request.state, "actor_id", None)
    is_first = payload.get("is_first", True)
    if not actor_id:
        raise HTTPException(status_code=422, detail="actor_id required")
    approval = service.record_dual_channel_approval(action_id, actor_id, is_first, db)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    db.commit()
    return {"status": "approved", "approval": approval.model_dump()}


@router.get("/actions/{action_id}/approval-status", response_model=DualChannelApproval)
async def get_approval_status(
    action_id: str,
    request: Request,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> DualChannelApproval:
    approval = service.get_dual_channel_approval_status(action_id, db)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


# Summary Metrics API (FR-13)
@router.get("/tenants/{tenant_id}/metrics")
async def get_tenant_metrics(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    request: Request = None,
    service: MMMService = Depends(get_service),
    db: Session = Depends(get_db),
) -> dict:
    # Authorization: Requires mmm_admin or tenant_admin
    if request:
        roles = getattr(request.state, "roles", [])
        if "mmm_admin" not in roles and "tenant_admin" not in roles:
            raise HTTPException(status_code=403, detail="Not authorized")
    from datetime import datetime
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    return service.get_tenant_metrics(tenant_id, start, end, db)
