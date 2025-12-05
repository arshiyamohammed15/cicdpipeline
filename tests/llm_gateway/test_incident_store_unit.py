from __future__ import annotations
"""
Unit tests for SafetyIncidentStore deduplication and alert payloads.
"""


from cloud_services.llm_gateway.services import SafetyIncidentStore  # type: ignore  # pylint: disable=import-error
from cloud_services.llm_gateway.models import (  # type: ignore  # pylint: disable=import-error
    Decision,
    RiskClass,
    Severity,
)


def test_incident_deduplication_same_context() -> None:
    store = SafetyIncidentStore()

    first = store.record_incident(
        tenant_id="tenantA",
        workspace_id="ws-1",
        actor_id="actor-1",
        risk_class=RiskClass.R1,
        severity=Severity.WARN,
        decision=Decision.BLOCKED,
        receipt_id="rcpt-1",
        request_id="req-1",
        policy_snapshot_id="snap-1",
        policy_version_ids=["pol-1"],
        context="prompt with injection",
    )

    second = store.record_incident(
        tenant_id="tenantA",
        workspace_id="ws-1",
        actor_id="actor-1",
        risk_class=RiskClass.R1,
        severity=Severity.CRITICAL,
        decision=Decision.BLOCKED,
        receipt_id="rcpt-2",
        request_id="req-2",
        policy_snapshot_id="snap-1",
        policy_version_ids=["pol-1"],
        context="prompt with injection",
    )

    # Same object (deduped), severity escalated, multiple related requests
    assert first.incident_id == second.incident_id
    assert second.severity is Severity.CRITICAL
    assert "req-1" in second.related_request_ids and "req-2" in second.related_request_ids

    incidents = store.list_incidents()
    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.alert_payload["schema_id"] == "alert_safety_incident_v1"
    assert inc.alert_payload["risk_class"] == RiskClass.R1.value
    assert inc.alert_payload["severity"] == Severity.CRITICAL.value


