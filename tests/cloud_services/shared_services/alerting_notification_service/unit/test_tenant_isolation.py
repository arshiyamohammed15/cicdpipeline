
# Imports handled by conftest.py
from datetime import datetime

import pytest


def _alert_payload(alert_id: str, tenant_id: str = "tenant-integration") -> dict:
    now = datetime.utcnow().isoformat()
    return {
        "schema_version": "1.0.0",
        "alert_id": alert_id,
        "tenant_id": tenant_id,
        "source_module": "EPC-5",
        "plane": "Tenant",
        "environment": "prod",
        "component_id": "comp-iso",
        "severity": "P2",
        "priority": "P2",
        "category": "reliability",
        "summary": "Tenant isolation test",
        "description": "verifies tenant guards",
        "labels": {},
        "started_at": now,
        "last_seen_at": now,
        "dedup_key": f"{tenant_id}:{alert_id}",
    }


@pytest.mark.alerting_security
@pytest.mark.security
def test_missing_tenant_header_rejected(test_client):
    payload = _alert_payload("tenant-missing")
    headers = dict(test_client.headers)
    headers.pop("X-Tenant-ID", None)
    headers.pop("x-tenant-id", None)
    original = dict(test_client.headers)
    try:
        test_client.headers.clear()
        test_client.headers.update(headers)
        response = test_client.post("/v1/alerts", json=payload)
    finally:
        test_client.headers.clear()
        test_client.headers.update(original)
    assert response.status_code == 400


@pytest.mark.alerting_security
@pytest.mark.security
def test_cross_tenant_forbidden_without_allowance(test_client):
    payload = _alert_payload("tenant-forbid", tenant_id="tenant-other")
    # Strip global roles/allowance to mimic tenant-scoped caller
    original = dict(test_client.headers)
    try:
        test_client.headers.clear()
        test_client.headers.update({"X-Tenant-ID": "tenant-integration"})
        response = test_client.post("/v1/alerts", json=payload)
    finally:
        test_client.headers.clear()
        test_client.headers.update(original)
    assert response.status_code in (400, 403)


@pytest.mark.alerting_security
@pytest.mark.security
def test_cross_tenant_allowed_with_allowance(test_client):
    payload = _alert_payload("tenant-allowed", tenant_id="tenant-shared")
    headers = {**test_client.headers, "X-Allow-Tenants": "tenant-shared"}
    response = test_client.post("/v1/alerts", json=payload, headers=headers)
    assert response.status_code == 200

