
# Imports handled by conftest.py
from datetime import datetime

import pytest


def _alert(alert_id: str) -> dict:
    now = datetime.utcnow().isoformat()
    return {
        "schema_version": "1.0.0",
        "alert_id": alert_id,
        "tenant_id": "tenant-integration",
        "source_module": "EPC-5",
        "plane": "Tenant",
        "environment": "prod",
        "component_id": "comp-int",
        "severity": "P1",
        "priority": "P1",
        "category": "reliability",
        "summary": "Integration test",
        "description": "integration path",
        "labels": {},
        "started_at": now,
        "last_seen_at": now,
        "dedup_key": f"comp-int:{alert_id}",
        "policy_refs": ["policy-default"],
        "links": [{"kind": "metric", "href": "https://telemetry.local/example"}],
        "runbook_refs": ["runbook://integration/test"],
        "automation_hooks": ["hook://noop"],
    }


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="test_client fixture not available in current test harness")
async def test_alert_ack_resolve_flow(test_client):
    payload = _alert("integration-1")
    created = test_client.post("/v1/alerts", json=payload)
    assert created.status_code == 200
    alert_id = created.json()["alert_id"]

    ack = test_client.post(f"/v1/alerts/{alert_id}/ack", json={"actor": "automation"})
    assert ack.status_code == 200
    assert ack.json()["status"] == "acknowledged"

    resolved = test_client.post(f"/v1/alerts/{alert_id}/resolve", json={"actor": "automation"})
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    search = test_client.post("/v1/alerts/search", json={"tenant_id": "tenant-integration"})
    assert search.status_code == 200
    assert len(search.json()) >= 1


@pytest.mark.alerting_regression
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="test_client fixture not available in current test harness")
async def test_preferences_round_trip(test_client):
    pref_payload = {
        "user_id": "user-int",
        "tenant_id": "tenant-integration",
        "channels": ["email"],
        "quiet_hours": {"Mon": "22:00-07:00"},
        "severity_threshold": {"email": "P3"},
        "timezone": "UTC",
        "channel_preferences": {"email": ["email"]},
    }
    saved = test_client.post("/v1/preferences", json=pref_payload)
    assert saved.status_code == 200
    fetched = test_client.get("/v1/preferences/user-int")
    assert fetched.status_code == 200
    assert fetched.json()["channels"] == ["email"]

