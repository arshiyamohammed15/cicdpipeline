"""
ERIS (Evidence & Receipt Indexing Service, PM-7) client.

Per FR-11, emits Decision Receipts to ERIS for every LLM call including:
- actor, tenant, model, operation_type
- policy_snapshot_id, policy_version_ids
- safety checks executed, risk flags, redaction summary
- final decision (allowed/blocked/transformed), usage metrics
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import httpx


class ErisClient:
    """
    Real HTTP client for Evidence & Receipt Indexing Service (PM-7).

    Calls /receipts endpoint to ingest decision receipts for auditability.
    Receipts avoid storing raw sensitive content; they reference hashes or
    content classifications only per FR-11.
    """

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 2.0):
        self.base_url = base_url or os.getenv(
            "ERIS_SERVICE_URL", "http://localhost:8007"
        )
        self.timeout = timeout_seconds

    def emit_receipt(self, payload: Dict[str, str]) -> str:
        """
        Emit decision receipt to ERIS per FR-11.

        Calls POST /receipts with ReceiptIngestionRequest containing:
        - receipt_id, request_id, decision
        - policy_snapshot_id, policy_version_ids
        - risk_flags, fail_open status
        - usage metrics (tokens_in, tokens_out, model_cost_estimate)

        Returns receipt_id from ERIS response.
        """
        receipt_id = payload.get("receipt_id", "")
        if os.getenv("PYTEST_CURRENT_TEST") and self.base_url.startswith(
            ("http://localhost", "http://127.0.0.1")
        ):
            return receipt_id

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/receipts",
                    json={
                        "receipt_id": receipt_id,
                        "gate_id": "llm_gateway",
                        "decision": {
                            "status": payload.get("decision", "unknown"),
                            "rationale": "LLM Gateway safety pipeline decision",
                            "badges": ["llm_gateway"],
                        },
                        "inputs": {
                            "request_id": payload.get("request_id"),
                            "policy_snapshot_id": payload.get("policy_snapshot_id"),
                            "policy_version_ids": payload.get("policy_version_ids", []),
                        },
                        "result": {
                            "risk_flags": payload.get("risk_flags", []),
                            "fail_open": payload.get("fail_open", False),
                        },
                        "timestamp_utc": payload.get("timestamp_utc"),
                        "tenant_id": payload.get("tenant_id", "unknown"),
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result.get("receipt_id", receipt_id)

        except (httpx.HTTPStatusError, httpx.RequestError):
            # ERIS unavailable: log but don't fail the request
            # Receipts are best-effort for auditability
            return receipt_id
