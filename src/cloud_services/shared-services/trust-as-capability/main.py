from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

SERVICE_NAME = "trust-as-capability"


class TrustContext(BaseModel):
    workspace_trust: Optional[bool] = None


class TrustRequest(BaseModel):
    subject_id: Optional[str] = None
    context: Optional[TrustContext] = None
    signals: Optional[List[Dict[str, Any]]] = None


class TrustResponse(BaseModel):
    trust_level: str
    reasons: List[str]
    decision_id: str


TrustRequest.model_rebuild()
TrustResponse.model_rebuild()

app = FastAPI(title=SERVICE_NAME)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.post("/trust/evaluate", response_model=TrustResponse)
async def evaluate_trust(request: TrustRequest) -> TrustResponse:
    if not request.subject_id:
        raise HTTPException(status_code=400, detail="subject_id is required")

    reasons: List[str] = []
    trust_level = "unknown"

    if request.context and request.context.workspace_trust is False:
        trust_level = "untrusted"
        reasons.append("WORKSPACE_UNTRUSTED")
    else:
        reasons.append("NO_ATTESTATION_EVIDENCE")

    return TrustResponse(
        trust_level=trust_level,
        reasons=reasons,
        decision_id=str(uuid4()),
    )
