"""FastAPI routes for the SIN stub service."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, Field, ValidationError

from .models import SignalEnvelope, ProducerRegistration, IngestStatus
from .services import SignalIngestionService
from .producer_registry import ProducerRegistryError
from .observability import HealthChecker

router = APIRouter(prefix="/v1")


class SignalIngestRequest(BaseModel):
    signals: List[Dict[str, Any]] = Field(..., min_length=1, max_length=1000)


def require_auth(authorization: str = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="unauthorized")
    return authorization


def _verify_token(iam, token: str) -> Optional[Dict[str, Any]]:
    verifier = getattr(iam, "verify", None)
    if callable(verifier):
        return verifier(token)
    return {"tenant_id": None, "producer_id": None}


def get_context(request: Request):
    app_state = request.app.state
    ingestion_service: SignalIngestionService = app_state.ingestion_service  # type: ignore[attr-defined]
    producer_registry = app_state.producer_registry  # type: ignore[attr-defined]
    iam = app_state.iam  # type: ignore[attr-defined]
    schema_registry = app_state.schema_registry  # type: ignore[attr-defined]
    health_checker: HealthChecker = app_state.health_checker  # type: ignore[attr-defined]
    dlq_handler = app_state.dlq_handler  # type: ignore[attr-defined]
    return {
        "ingestion_service": ingestion_service,
        "producer_registry": producer_registry,
        "iam": iam,
        "schema_registry": schema_registry,
        "health_checker": health_checker,
        "dlq_handler": dlq_handler,
    }


@router.get("/health")
async def health(ctx=Depends(get_context)):
    checker = ctx["health_checker"]
    if hasattr(checker, "health"):
        return checker.health()
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def ready(ctx=Depends(get_context)):
    return {"ready": True, "checks": {"dependencies": "ok"}, "timestamp": datetime.utcnow().isoformat()}


@router.post("/producers/register", status_code=201)
async def register_producer(
    payload: Dict[str, Any],
    ctx=Depends(get_context),
    authorization: str = Depends(require_auth),
):
    claims = _verify_token(ctx["iam"], authorization)
    if claims is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    producer_data = payload.get("producer")
    if not producer_data:
        raise HTTPException(status_code=422, detail="producer payload missing")
    producer = ProducerRegistration.model_validate(producer_data)
    try:
        ctx["producer_registry"].register_producer(producer, claims.get("tenant_id"))
    except ProducerRegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"producer_id": producer.producer_id, "status": "registered"}


@router.get("/producers")
async def list_producers(ctx=Depends(get_context)):
    producers = ctx["producer_registry"].list_producers()
    return {"producers": [p.model_dump() for p in producers]}


@router.get("/producers/{producer_id}")
async def get_producer(
    producer_id: str,
    ctx=Depends(get_context),
    authorization: str = Depends(require_auth),
):
    claims = _verify_token(ctx["iam"], authorization)
    if claims is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    try:
        producer, owner_tenant = ctx["producer_registry"].get_producer_entry(producer_id)
    except ProducerRegistryError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    if owner_tenant and claims.get("tenant_id") and owner_tenant != claims["tenant_id"]:
        raise HTTPException(status_code=403, detail="forbidden")
    return {"producer": producer.model_dump()}


@router.put("/producers/{producer_id}")
async def update_producer(
    producer_id: str,
    payload: Dict[str, Any],
    ctx=Depends(get_context),
    authorization: str = Depends(require_auth),
):
    claims = _verify_token(ctx["iam"], authorization)
    if claims is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    producer_data = payload.get("producer")
    if not producer_data:
        raise HTTPException(status_code=422, detail="producer payload missing")
    producer = ProducerRegistration.model_validate(producer_data)
    if producer.producer_id != producer_id:
        producer.producer_id = producer_id
    try:
        ctx["producer_registry"].update_producer(producer, claims.get("tenant_id"))
    except ProducerRegistryError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"producer_id": producer.producer_id, "status": "updated"}


@router.get("/signals/dlq")
async def inspect_dlq(
    tenant_id: Optional[str] = None,
    producer_id: Optional[str] = None,
    signal_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    ctx=Depends(get_context),
    authorization: str = Depends(require_auth),
):
    claims = _verify_token(ctx["iam"], authorization)
    if claims is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    if tenant_id and claims.get("tenant_id") and claims["tenant_id"] != tenant_id:
        raise HTTPException(status_code=403, detail="forbidden")
    entries = ctx["dlq_handler"].inspect(tenant_id, producer_id, signal_type)
    total = len(entries)
    paged = entries[offset : offset + limit if limit else None]
    return {"entries": paged, "total": total}


@router.post("/signals/ingest")
async def ingest_signals(
    request: SignalIngestRequest,
    ctx=Depends(get_context),
    authorization: str = Depends(require_auth),
):
    claims = _verify_token(ctx["iam"], authorization)
    if claims is None:
        raise HTTPException(status_code=401, detail="unauthorized")

    try:
        signals = [SignalEnvelope.model_validate(s) for s in request.signals]
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    summary = {"accepted": 0, "rejected": 0, "dlq": 0, "total": len(signals)}
    prefiltered_results: List[Dict[str, Any]] = []
    allowed_signals: List[SignalEnvelope] = []

    for sig in signals:
        token_tenant = claims.get("tenant_id")
        if token_tenant and sig.tenant_id != token_tenant:
            prefiltered_results.append(
                {
                    "signal_id": sig.signal_id,
                    "status": IngestStatus.REJECTED,
                    "reason": "tenant mismatch",
                    "error_code": "TENANT_ISOLATION",
                }
            )
            summary["rejected"] += 1
            continue
        try:
            owner_tenant = ctx["producer_registry"].tenant_for(sig.producer_id)
            if owner_tenant and token_tenant and owner_tenant != token_tenant:
                prefiltered_results.append(
                    {
                        "signal_id": sig.signal_id,
                        "status": IngestStatus.REJECTED,
                        "reason": "producer owned by different tenant",
                        "error_code": "TENANT_ISOLATION",
                    }
                )
                summary["rejected"] += 1
                continue
        except ProducerRegistryError:
            # allow validation to handle missing producer
            pass
        allowed_signals.append(sig)

    ingested_results: List[Dict[str, Any]] = []
    if allowed_signals:
        ingested_results, svc_summary = await ctx["ingestion_service"].ingest(allowed_signals)
        summary["accepted"] += svc_summary.get("accepted", 0)
        summary["rejected"] += svc_summary.get("rejected", 0)
        summary["dlq"] += svc_summary.get("dlq", 0)

    results = prefiltered_results + ingested_results
    return {"results": results, "summary": summary}
