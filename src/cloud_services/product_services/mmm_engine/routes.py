"""
API routes for MMM Engine.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from .models import (
    DecideRequest,
    DecideResponse,
    Playbook,
    PlaybookCreateRequest,
    MMMOutcome,
)
from .services import MMMService
from .database.connection import get_db
from .observability.metrics import get_metrics_text

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
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/ready")
async def ready() -> dict[str, str]:
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


