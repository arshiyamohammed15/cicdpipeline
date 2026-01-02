from __future__ import annotations

from typing import Any, Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request

SERVICE_NAME = "api-gateway-webhooks"

app = FastAPI(title=SERVICE_NAME)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.post("/webhooks/{provider}", status_code=202)
async def ingest_webhook(provider: str, request: Request) -> Dict[str, Any]:
    signature = request.headers.get("x-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="missing signature header")

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    envelope_id = str(uuid4())
    envelope = {
        "envelope_id": envelope_id,
        "provider": provider,
        "headers": {"x-signature": signature},
        "payload": payload,
    }
    return {"accepted": True, "envelope_id": envelope["envelope_id"]}
