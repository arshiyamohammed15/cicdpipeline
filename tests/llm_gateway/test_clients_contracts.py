from __future__ import annotations
"""
Contract-oriented tests for LLM Gateway external clients.

These tests do NOT call real services. They validate that:
- Each client targets the expected endpoint path
- Request payloads contain the expected fields and structure

This helps catch accidental drift from the contracts described in the PRDs.
"""


from typing import Any, Dict, List

import httpx
import pytest

from cloud_services.llm_gateway.clients import (  # type: ignore  # pylint: disable=import-error
    AlertingClient,
    BudgetClient,
    DataGovernanceClient,
    ErisClient,
    IAMClient,
    PolicyClient,
)
from cloud_services.llm_gateway.models import Actor  # type: ignore  # pylint: disable=import-error


class _CaptureClient:
    """Helper to capture outgoing HTTP requests for contract inspection."""

    def __init__(self, status_code: int = 200, json_body: Dict[str, Any] | None = None):
        self.status_code = status_code
        self.json_body = json_body or {}
        self.requests: List[Dict[str, Any]] = []

    def post(self, url: str, json: Dict[str, Any], **_: Any) -> httpx.Response:  # type: ignore[override]
        self.requests.append({"method": "POST", "url": url, "json": json})
        request = httpx.Request("POST", url, json=json)
        return httpx.Response(self.status_code, json=self.json_body, request=request)

    def get(self, url: str, params: Dict[str, Any] | None = None, **_: Any) -> httpx.Response:  # type: ignore[override]
        self.requests.append({"method": "GET", "url": url, "params": params or {}})
        request = httpx.Request("GET", url, params=params or {})
        return httpx.Response(self.status_code, json=self.json_body, request=request)


@pytest.fixture
def patch_httpx_client(monkeypatch: pytest.MonkeyPatch) -> _CaptureClient:
    """
    Monkeypatch httpx.Client to use a capture helper so we can inspect calls.
    """

    capture = _CaptureClient()

    class _ClientWrapper:
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            # Ignore constructor args; we only care about methods.
            pass

        def __enter__(self) -> _CaptureClient:
            return capture

        def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
            return None

    monkeypatch.setattr(httpx, "Client", _ClientWrapper)  # type: ignore[arg-type]
    return capture


def test_iam_client_sends_expected_claims(patch_httpx_client: _CaptureClient) -> None:
    client = IAMClient(base_url="http://iam.test/iam/v1", timeout_seconds=1.0)
    actor = Actor(
        actor_id="actor-123",
        actor_type="human",
        roles=["developer"],
        capabilities=["llm.invoke"],
        scopes=["llm.chat"],
        session_assurance_level="high",
        workspace_id="ws-1",
    )

    # We only care that the request is formed correctly, not the decision
    # outcome. Provide a fake ALLOW decision in the mock response.
    patch_httpx_client.json_body = {"decision": "ALLOW"}

    client.validate_actor(actor, scope="llm.chat")

    assert patch_httpx_client.requests, "IAMClient should have issued a POST"
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/decision")
    body = req["json"]
    assert body["subject"]["subject_id"] == "actor-123"
    assert "roles" in body["subject"]
    assert "capabilities" in body["subject"]
    assert body["action"] == "llm.chat"


def test_data_governance_client_calls_compliance(patch_httpx_client: _CaptureClient) -> None:
    client = DataGovernanceClient(base_url="http://dg.test/privacy/v1", timeout_seconds=0.1)

    redacted, counts = client.redact("User email test@example.com", tenant_id="tenantX")

    assert patch_httpx_client.requests, "DataGovernanceClient should have issued a POST"
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/compliance")
    body = req["json"]
    assert body["tenant_id"] == "tenantX"
    assert body["action"] == "redact"
    assert body["resource"]["resource_type"] == "llm_prompt"


def test_policy_client_calls_standards_endpoint(patch_httpx_client: _CaptureClient) -> None:
    client = PolicyClient(base_url="http://policy.test", latency_budget_ms=500, timeout_seconds=0.5)

    snapshot = client.fetch_snapshot("tenantA")

    assert patch_httpx_client.requests, "PolicyClient should have issued a GET"
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/standards")
    assert req["params"]["tenant_id"] == "tenantA"


def test_budget_client_calls_budgets_check(patch_httpx_client: _CaptureClient) -> None:
    client = BudgetClient(base_url="http://budget.test", timeout_seconds=0.5)

    # Provide a mock response that allows the request
    patch_httpx_client.json_body = {"allowed": True}

    client.assert_within_budget("tenantA", tokens=100, workspace_id="ws-1", actor_id="actor-1")

    assert patch_httpx_client.requests, "BudgetClient should have issued a POST"
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/budgets/check")
    body = req["json"]
    assert body["tenant_id"] == "tenantA"
    assert body["resource_type"] == "llm_tokens"
    assert body["allocated_to_id"] == "ws-1"


def test_eris_client_emits_receipt_payload(patch_httpx_client: _CaptureClient) -> None:
    client = ErisClient(base_url="http://eris.test", timeout_seconds=0.5)
    payload = {
        "receipt_id": "rcpt-1",
        "request_id": "req-1",
        "decision": "ALLOWED",
        "policy_snapshot_id": "snap-1",
        "policy_version_ids": ["pol-1"],
        "risk_flags": [],
        "fail_open": False,
        "tenant_id": "tenantA",
        "timestamp_utc": "2025-11-26T00:00:00Z",
    }

    client.emit_receipt(payload)

    assert patch_httpx_client.requests, "ErisClient should have issued a POST"
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/receipts")
    body = req["json"]
    assert body["receipt_id"] == "rcpt-1"
    assert body["gate_id"] == "llm_gateway"
    assert body["tenant_id"] == "tenantA"
    assert body["inputs"]["request_id"] == "req-1"


def test_alerting_client_emits_alert_payload(patch_httpx_client: _CaptureClient) -> None:
    client = AlertingClient(base_url="http://alerts.test/v1", timeout_seconds=0.5)
    payload = {
        "incident_id": "inc-1",
        "tenant_id": "tenantA",
        "actor_id": "actor-1",
        "risk_class": "R1",
        "severity": "CRITICAL",
        "logical_model_id": "default_chat",
        "policy_snapshot_id": "snap-1",
        "decision": "BLOCKED",
        "receipt_id": "rcpt-1",
        "dedupe_key": "tenantA:R1:abc",
        "correlation_hints": {"workspace_id": "ws-1"},
        "timestamp_utc": "2025-11-26T00:00:00Z",
    }

    client.emit_alert(payload)

    assert patch_httpx_client.requests, "AlertingClient should have issued a POST"
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/alerts")
    body = req["json"]
    assert body["tenant_id"] == "tenantA"
    assert body["category"] == "safety_incident"
    assert body["metadata"]["risk_class"] == "R1"
    assert body["metadata"]["dedupe_key"] == "tenantA:R1:abc"


