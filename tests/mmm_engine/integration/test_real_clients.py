from __future__ import annotations
"""
Integration tests for MMM Engine real service clients.

Per PRD Phase 4, tests all real HTTP clients with mock servers to validate:
- Correct endpoint paths and request payloads
- Response parsing and error handling
- Circuit breaker behavior
- Timeout handling
"""


import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from cloud_services.product_services.mmm_engine.integrations.iam_client import IAMClient
from cloud_services.product_services.mmm_engine.integrations.eris_client import ERISClient
from cloud_services.product_services.mmm_engine.integrations.llm_gateway_client import (
    LLMGatewayClient,
)
from cloud_services.product_services.mmm_engine.integrations.policy_client import (
    PolicyClient,
    PolicyCache,
    PolicyClientError,
)
from cloud_services.product_services.mmm_engine.integrations.data_governance_client import (
    DataGovernanceClient,
)
from cloud_services.product_services.mmm_engine.integrations.ubi_client import UBIClient


class _CaptureClient:
    """Helper to capture outgoing HTTP requests for contract inspection."""

    def __init__(self, status_code: int = 200, json_body: Dict[str, Any] | None = None):
        self.status_code = status_code
        self.json_body = json_body or {}
        self.requests: list[Dict[str, Any]] = []

    def post(self, url: str, json: Dict[str, Any] | None = None, **kwargs: Any) -> httpx.Response:
        self.requests.append({"method": "POST", "url": url, "json": json, **kwargs})
        request = httpx.Request("POST", url, json=json or {})
        return httpx.Response(self.status_code, json=self.json_body, request=request)

    def get(self, url: str, params: Dict[str, Any] | None = None, **kwargs: Any) -> httpx.Response:
        self.requests.append({"method": "GET", "url": url, "params": params or {}, **kwargs})
        request = httpx.Request("GET", url, params=params or {})
        return httpx.Response(self.status_code, json=self.json_body, request=request)

    def __enter__(self) -> _CaptureClient:
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class _CaptureAsyncClient:
    """Helper to capture async HTTP requests."""

    def __init__(self, status_code: int = 200, json_body: Dict[str, Any] | None = None):
        self.status_code = status_code
        self.json_body = json_body or {}
        self.requests: list[Dict[str, Any]] = []

    async def post(
        self, url: str, json: Dict[str, Any] | None = None, **kwargs: Any
    ) -> httpx.Response:
        self.requests.append({"method": "POST", "url": url, "json": json, **kwargs})
        request = httpx.Request("POST", url, json=json or {})
        return httpx.Response(self.status_code, json=self.json_body, request=request)

    async def get(
        self, url: str, params: Dict[str, Any] | None = None, **kwargs: Any
    ) -> httpx.Response:
        self.requests.append({"method": "GET", "url": url, "params": params or {}, **kwargs})
        request = httpx.Request("GET", url, params=params or {})
        return httpx.Response(self.status_code, json=self.json_body, request=request)

    async def __aenter__(self) -> _CaptureAsyncClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass


@pytest.fixture
def patch_httpx_client(monkeypatch: pytest.MonkeyPatch) -> _CaptureClient:
    """Monkeypatch httpx.Client to use a capture helper."""
    capture = _CaptureClient()

    class _ClientWrapper:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __enter__(self) -> _CaptureClient:
            return capture

        def __exit__(self, *args: Any) -> None:
            pass

    monkeypatch.setattr(httpx, "Client", _ClientWrapper)
    return capture


@pytest.fixture
def patch_httpx_async_client(monkeypatch: pytest.MonkeyPatch) -> _CaptureAsyncClient:
    """Monkeypatch httpx.AsyncClient to use a capture helper."""
    capture = _CaptureAsyncClient()

    class _AsyncClientWrapper:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        async def __aenter__(self) -> _CaptureAsyncClient:
            return capture

        async def __aexit__(self, *args: Any) -> None:
            pass

    monkeypatch.setattr(httpx, "AsyncClient", _AsyncClientWrapper)
    return capture


def test_iam_client_verify_token(patch_httpx_client: _CaptureClient) -> None:
    """Test IAM client token verification."""
    client = IAMClient(base_url="http://iam.test/v1", timeout_seconds=2.0)
    patch_httpx_client.json_body = {"valid": True, "claims": {"tenant_id": "test-tenant", "sub": "user@test"}}

    success, claims, error = client.verify_token("test-token")

    assert success is True
    assert claims is not None
    assert claims.get("tenant_id") == "test-tenant"
    assert error is None
    assert len(patch_httpx_client.requests) == 1
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/verify")
    assert req["json"]["token"] == "test-token"


def test_iam_client_validate_actor(patch_httpx_client: _CaptureClient) -> None:
    """Test IAM client actor validation."""
    client = IAMClient(base_url="http://iam.test/v1", timeout_seconds=2.0)
    patch_httpx_client.json_body = {"decision": "ALLOW"}

    # Should not raise
    client.validate_actor("actor-123", "human", "mmm.decide", "tenant-1")

    assert len(patch_httpx_client.requests) == 1
    req = patch_httpx_client.requests[0]
    assert req["url"].endswith("/decision")
    body = req["json"]
    assert body["subject"]["subject_id"] == "actor-123"
    assert body["action"] == "mmm.decide"


def test_iam_client_circuit_breaker() -> None:
    """Test IAM client circuit breaker behavior."""
    client = IAMClient(base_url="http://iam.test/v1", timeout_seconds=0.1)

    # Simulate failures to open circuit breaker
    with patch("httpx.Client") as mock_client:
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.post.side_effect = httpx.RequestError("Connection failed")
        mock_client.return_value = mock_instance

        # Trigger failures
        for _ in range(6):
            try:
                client.verify_token("test")
            except Exception:
                pass

        # Circuit should be open now
        success, _, error = client.verify_token("test")
        assert success is False
        assert "temporarily unavailable" in (error or "").lower()


@pytest.mark.asyncio
async def test_eris_client_emit_receipt(patch_httpx_async_client: _CaptureAsyncClient) -> None:
    """Test ERIS client receipt emission with retry logic."""
    client = ERISClient(base_url="http://eris.test", timeout_seconds=2.0)
    patch_httpx_async_client.json_body = {"receipt_id": "receipt-123"}

    receipt = {
        "receipt_id": "test-receipt",
        "gate_id": "mmm",
        "schema_version": "v1",
        "timestamp_utc": "2024-01-01T00:00:00Z",
    }

    receipt_id = await client.emit_receipt(receipt)

    assert receipt_id == "receipt-123"
    assert len(patch_httpx_async_client.requests) == 1
    req = patch_httpx_async_client.requests[0]
    assert req["url"].endswith("/v1/evidence/receipts")
    assert "signature" in req["json"]  # Receipt should be signed


@pytest.mark.asyncio
async def test_eris_client_retry_logic(patch_httpx_async_client: _CaptureAsyncClient) -> None:
    """Test ERIS client retry logic on server errors."""
    client = ERISClient(base_url="http://eris.test", timeout_seconds=2.0)

    # First two attempts fail with 500, third succeeds
    call_count = 0

    async def mock_post(*args: Any, **kwargs: Any) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(500, json={"error": "Internal server error"})
        return httpx.Response(200, json={"receipt_id": "receipt-123"})

    patch_httpx_async_client.post = mock_post

    receipt = {"receipt_id": "test", "gate_id": "mmm", "schema_version": "v1"}
    receipt_id = await client.emit_receipt(receipt, retry_attempts=3)

    assert receipt_id == "receipt-123"
    assert call_count == 3


@pytest.mark.asyncio
async def test_llm_gateway_client_generate(patch_httpx_async_client: _CaptureAsyncClient) -> None:
    """Test LLM Gateway client content generation."""
    client = LLMGatewayClient(base_url="http://llm-gateway.test", timeout_seconds=3.0)
    patch_httpx_async_client.json_body = {
        "response_id": "resp-123",
        "receipt_id": "receipt-123",
        "decision": {"status": "ALLOW"},
        "output": {"content": "Generated content"},
        "risk_flags": [],
    }

    result = await client.generate(
        prompt="Test prompt",
        tenant_id="tenant-1",
        actor_id="actor-1",
        actor_type="human",
    )

    assert result["content"] == "Generated content"
    assert result["safety"]["status"] == "pass"
    assert len(patch_httpx_async_client.requests) > 0
    req = patch_httpx_async_client.requests[0]
    assert "/v1/llm/generate" in req["url"] or "/api/v1/llm/chat" in req["url"]
    assert req["json"]["user_prompt"] == "Test prompt"


@pytest.mark.asyncio
async def test_llm_gateway_client_safety_failure(patch_httpx_async_client: _CaptureAsyncClient) -> None:
    """Test LLM Gateway client handles safety check failures."""
    client = LLMGatewayClient(base_url="http://llm-gateway.test", timeout_seconds=3.0)
    patch_httpx_async_client.json_body = {
        "response_id": "resp-123",
        "decision": {"status": "BLOCK", "reasons": ["Safety violation"]},
        "risk_flags": [{"risk_class": "injection", "severity": "high"}],
    }

    with pytest.raises(RuntimeError, match="safety check failed"):
        await client.generate(
            prompt="Test prompt",
            tenant_id="tenant-1",
            actor_id="actor-1",
            actor_type="human",
        )


def test_policy_client_evaluate(patch_httpx_client: _CaptureClient) -> None:
    """Test Policy client evaluation."""
    client = PolicyClient(base_url="http://policy.test", timeout_seconds=0.5)
    patch_httpx_client.json_body = {
        "allowed": True,
        "policy_snapshot_id": "snapshot-123",
        "policy_version_ids": ["pol-v1"],
        "restrictions": [],
    }

    result = client.evaluate("tenant-1", {"context": "test"})

    assert result["allowed"] is True
    assert result["policy_snapshot_id"] == "snapshot-123"
    assert len(patch_httpx_client.requests) > 0


def test_policy_cache_fail_open(patch_httpx_client: _CaptureClient) -> None:
    """Test Policy cache fail-open behavior."""
    client = PolicyClient(base_url="http://policy.test", timeout_seconds=0.5)
    cache = PolicyCache(client, max_staleness_seconds=60, fail_open_window_seconds=300)

    # First call succeeds
    patch_httpx_client.json_body = {
        "allowed": True,
        "policy_snapshot_id": "snapshot-123",
        "policy_version_ids": ["pol-v1"],
        "restrictions": [],
    }
    snapshot1 = cache.get_snapshot("tenant-1")

    # Second call fails, but cache should use stale snapshot
    patch_httpx_client.json_body = {}
    patch_httpx_client.status_code = 500

    # Simulate time passing but within fail-open window
    import time
    with patch("time.time", return_value=time.time() + 120):  # 2 minutes later
        snapshot2 = cache.get_snapshot("tenant-1", allow_fail_open=True)

    assert snapshot2.policy_stale is True
    assert snapshot2.snapshot_id == snapshot1.snapshot_id


def test_data_governance_client_get_tenant_config(patch_httpx_client: _CaptureClient) -> None:
    """Test Data Governance client tenant config retrieval."""
    client = DataGovernanceClient(base_url="http://dg.test", timeout_seconds=0.5)
    patch_httpx_client.json_body = {
        "quiet_hours": {"start": 22, "end": 6},
        "retention_days": 90,
        "privacy_tags": ["pii"],
        "data_residency": "us-east-1",
    }

    config = client.get_tenant_config("tenant-1")

    assert config["quiet_hours"]["start"] == 22
    assert config["retention_days"] == 90
    assert len(patch_httpx_client.requests) == 1
    req = patch_httpx_client.requests[0]
    assert "/v1/data-governance/tenants/tenant-1/config" in req["url"]


def test_data_governance_client_redact(patch_httpx_client: _CaptureClient) -> None:
    """Test Data Governance client content redaction."""
    client = DataGovernanceClient(base_url="http://dg.test", timeout_seconds=0.5)
    patch_httpx_client.json_body = {
        "redacted_content": "[REDACTED]",
        "redaction_summary": {"entity_counts": {"email": 1, "phone": 0}},
    }

    content, counts = client.redact("test@example.com", "tenant-1")

    assert content == "[REDACTED]"
    assert counts.get("email") == 1
    assert len(patch_httpx_client.requests) == 1


def test_ubi_client_get_recent_signals(patch_httpx_client: _CaptureClient) -> None:
    """Test UBI client recent signals retrieval."""
    client = UBIClient(base_url="http://ubi.test", timeout_seconds=1.0)
    patch_httpx_client.json_body = {
        "signals": [
            {
                "signal_id": "sig-1",
                "tenant_id": "tenant-1",
                "actor_id": "actor-1",
                "dimension": "flow",
                "severity": "WARN",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ]
    }

    signals = client.get_recent_signals("tenant-1", "actor-1", limit=10)

    assert len(signals) == 1
    assert signals[0]["signal_id"] == "sig-1"
    assert len(patch_httpx_client.requests) == 1
    req = patch_httpx_client.requests[0]
    assert "/v1/ubi/signals/recent" in req["url"]
    assert req["params"]["tenant_id"] == "tenant-1"
    assert req["params"]["actor_id"] == "actor-1"
    assert req["params"]["limit"] == 10

