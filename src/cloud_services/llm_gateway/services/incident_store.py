"""
In-memory safety incident store used by `/v1/llm/safety/incidents`.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..models import Decision, RiskClass, SafetyIncident, Severity


class SafetyIncidentStore:
    """Stores incidents with dedupe key semantics."""

    def __init__(self) -> None:
        # Simple in-memory store keyed by dedupe key to implement the
        # 10‑minute style clustering described in the PRD. Time-window
        # semantics are left to EPC‑4; here we only ensure we do not emit
        # unbounded duplicate incident objects for the same risk cluster.
        self._incidents: List[SafetyIncident] = []
        self._by_dedupe_key: Dict[str, SafetyIncident] = {}

    def _build_dedupe_key(
        self, tenant_id: str, risk_class: RiskClass, context: str
    ) -> str:
        digest = hashlib.sha256(context.encode("utf-8")).hexdigest()
        return f"{tenant_id}:{risk_class}:{digest}"

    def record_incident(
        self,
        *,
        tenant_id: str,
        workspace_id: str,
        actor_id: str,
        risk_class: RiskClass,
        severity: Severity,
        decision: Decision,
        receipt_id: str,
        request_id: str,
        policy_snapshot_id: str,
        policy_version_ids: List[str],
        context: str,
    ) -> SafetyIncident:
        """Create or update a SafetyIncident with deduplication semantics.

        This mirrors the PRD requirement that EPC‑4 receive at most one alert
        per correlated cluster (`dedupe_key = tenant_id + risk_class +
        hashed_context`) within a time window.
        """
        dedupe_key = self._build_dedupe_key(tenant_id, risk_class, context)
        now = datetime.now(tz=timezone.utc)

        existing: Optional[SafetyIncident] = self._by_dedupe_key.get(dedupe_key)
        if existing is not None:
            # Append the new request to the existing cluster and bump severity
            # if the new event is higher severity.
            if request_id not in existing.related_request_ids:
                existing.related_request_ids.append(request_id)
            # Escalate stored severity if the new event is higher.
            if severity is Severity.CRITICAL and existing.severity is not Severity.CRITICAL:
                existing.severity = severity
                existing.alert_payload["severity"] = severity.value
            # Update correlation hints to help EPC‑4
            existing.correlation_hints.update(
                {
                    "last_request_id": request_id,
                    "last_decision": decision.value,
                }
            )
            existing.timestamp_utc = now
            return existing

        incident = SafetyIncident(
            incident_id=f"inc-{len(self._incidents)+1:06d}",
            schema_version="v1",
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            risk_class=risk_class,
            severity=severity,
            decision=decision,
            receipt_id=receipt_id,
            policy_snapshot_id=policy_snapshot_id,
            policy_version_ids=policy_version_ids,
            related_request_ids=[request_id],
            dedupe_key=dedupe_key,
            correlation_hints={
                "actor_id": actor_id,
                "tenant_id": tenant_id,
                "workspace_id": workspace_id,
                "risk_class": risk_class.value,
            },
            alert_payload={
                "schema_id": "alert_safety_incident_v1",
                "risk_class": risk_class.value,
                "severity": severity.value,
                "actor_id": actor_id,
                "tenant_id": tenant_id,
                "logical_model_id": None,
                "policy_snapshot_id": policy_snapshot_id,
                "decision": decision.value,
                "receipt_id": receipt_id,
                "dedupe_key": dedupe_key,
                "correlation_hints": {
                    "actor_id": actor_id,
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                },
            },
            timestamp_utc=now,
        )
        self._incidents.append(incident)
        self._by_dedupe_key[dedupe_key] = incident
        return incident

    def list_incidents(self) -> List[SafetyIncident]:
        return list(self._incidents)

