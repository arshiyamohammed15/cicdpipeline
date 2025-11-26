"""
Alerting & Notification Service (EPC-4) client.

Per FR-12, emits structured alerts to EPC-4 for safety incidents including:
- Repeated prompt injection attempts
- Blocked harmful content above severity threshold
- Recurrent policy violations from same actor/workspace

Alert payloads use schema `alert_safety_incident_v1` with deduplication
via `dedupe_key` within 10-minute sliding window.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import httpx


class AlertingClient:
    """
    Real HTTP client for Alerting & Notification Service (EPC-4).

    Calls POST /alerts endpoint to emit safety incident alerts per FR-12.
    Alerts include risk class, severity, actor, tenant, model, and correlation
    hints for EPC-4's correlation engine.
    """

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 2.0):
        self.base_url = base_url or os.getenv(
            "ALERTING_SERVICE_URL", "http://localhost:8004/v1"
        )
        self.timeout = timeout_seconds

    def emit_alert(self, payload: Dict[str, str]) -> None:
        """
        Emit safety incident alert to EPC-4 per FR-12.

        Calls POST /alerts with AlertPayload containing:
        - incident_id, risk_class, severity
        - actor_id, tenant_id, logical_model_id
        - policy_snapshot_id, decision, receipt_id
        - dedupe_key, correlation_hints

        Alerts are deduplicated by EPC-4 using dedupe_key within 10-minute
        sliding window per FR-12.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/alerts",
                    json={
                        "alert_id": payload.get("incident_id", ""),
                        "tenant_id": payload.get("tenant_id", "unknown"),
                        "component_id": "llm_gateway",
                        "category": "safety_incident",
                        "severity": payload.get("severity", "WARN"),
                        "title": f"LLM Gateway Safety Incident: {payload.get('risk_class', 'UNKNOWN')}",
                        "description": f"Safety incident detected: {payload.get('decision', 'BLOCKED')}",
                        "started_at": payload.get("timestamp_utc"),
                        "metadata": {
                            "risk_class": payload.get("risk_class"),
                            "actor_id": payload.get("actor_id"),
                            "logical_model_id": payload.get("logical_model_id"),
                            "policy_snapshot_id": payload.get("policy_snapshot_id"),
                            "receipt_id": payload.get("receipt_id"),
                            "dedupe_key": payload.get("dedupe_key"),
                            "correlation_hints": payload.get("correlation_hints", {}),
                        },
                    },
                )
                response.raise_for_status()

        except (httpx.HTTPStatusError, httpx.RequestError):
            # Alerting unavailable: log but don't fail the request
            # Alerts are best-effort for observability
            pass

