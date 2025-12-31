from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.shared_harness import assert_enforcement_receipt_fields

from alerting_notification_service.config import get_settings
from alerting_notification_service.dependencies import RequestContext
from alerting_notification_service.routes import v1 as alerting_routes
from cloud_services.llm_gateway.models import (  # type: ignore  # pylint: disable=import-error
    Actor,
    Budget,
    Decision,
    LLMRequest,
    OperationType,
    SafetyOverrides,
    Tenant,
)
from cloud_services.llm_gateway.services import (  # type: ignore  # pylint: disable=import-error
    build_default_service,
)
from integration_adapters.adapters.base import BaseAdapter
from integration_adapters.database.models import (
    Base,
    IntegrationConnection,
    IntegrationProvider,
    NormalisedAction,
)
from integration_adapters.services.adapter_registry import get_adapter_registry
from integration_adapters.services.integration_service import (
    IntegrationService,
    ToolOutputSchemaViolation,
    TOOL_OUTPUT_SCHEMA_VIOLATION,
)
from shared_libs.mcp_server_registry import (
    MCPClientFactory,
    MCPServerEntry,
    MCPServerRegistry,
    MCPVerifier,
    MCP_UNPINNED_SERVER,
)
from shared_libs.token_budget import TOK_BUDGET_OK, TOK_BUDGET_OUTPUT_EXCEEDED


class _ProviderSpy:
    def __init__(self) -> None:
        self.called = False

    def invoke(
        self,
        tenant_id: str,
        logical_model_id: str,
        prompt: str,
        operation_type: str,
        fallback: bool = False,
    ) -> dict[str, str]:
        self.called = True
        return {
            "model": f"provider/{logical_model_id}",
            "content": f"[provider/{logical_model_id}] response for {operation_type}",
        }


class _ProviderRetrySpy:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(
        self,
        tenant_id: str,
        logical_model_id: str,
        prompt: str,
        operation_type: str,
        fallback: bool = False,
    ) -> dict[str, str]:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("timeout")
        return {
            "model": f"provider/{logical_model_id}",
            "content": f"[provider/{logical_model_id}] response for {operation_type}",
        }


class _ErisSpy:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def emit_receipt(self, payload: dict) -> str:
        self.payloads.append(payload)
        return payload.get("receipt_id", "")


def _build_request(max_tokens: int) -> LLMRequest:
    return LLMRequest(
        request_id="req-platform-smoke",
        actor=Actor(
            actor_id="actor-1234",
            actor_type="human",
            roles=["developer"],
            capabilities=["llm.invoke"],
            scopes=["llm.chat"],
            session_assurance_level="high",
            workspace_id="workspace-1",
        ),
        tenant=Tenant(tenant_id="tenantA", region="us-east"),
        logical_model_id="default_chat",
        operation_type=OperationType.CHAT,
        intended_capability="analysis",
        sensitivity_level="medium",
        system_prompt_id="sys-default",
        user_prompt="Hello world",
        context_segments=[],
        policy_snapshot_id="policy-snap-1",
        policy_version_ids=["policy-v1"],
        budget=Budget(
            max_tokens=max_tokens,
            timeout_ms=1500,
            priority="normal",
            temperature=0.2,
        ),
        safety_overrides=SafetyOverrides(),
    )


class _StubBudgetClient:
    def check_budget(
        self,
        tenant_id: str,
        provider_id: str,
        connection_id: str,
        cost: float = 1.0,
    ):
        return True, None


class _StubKMSClient:
    def get_secret(self, auth_ref: str, tenant_id: str):
        return "secret-token"


class _StubERISClient:
    def __init__(self) -> None:
        self.receipts: list[dict] = []

    def emit_receipt(self, **kwargs) -> bool:
        self.receipts.append(kwargs)
        return True


class _StubMetrics:
    def increment_action_error(self, *args, **kwargs) -> None:
        return None

    def increment_action_executed(self, *args, **kwargs) -> None:
        return None


def _build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _seed_connection(session, tenant_id: str, provider_id: str):
    provider = IntegrationProvider(
        provider_id=provider_id,
        category="chat",
        name="Stub",
        status="GA",
        capabilities={},
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)

    connection = IntegrationConnection(
        tenant_id=tenant_id,
        provider_id=provider_id,
        display_name="Stub Connection",
        auth_ref="kms-secret",
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)
    return connection


@pytest.mark.asyncio
@pytest.mark.smoke
@pytest.mark.unit
async def test_budget_enforced_at_gateway_entrypoint(monkeypatch) -> None:
    from cloud_services.llm_gateway.services import llm_gateway_service

    budget_calls = {"count": 0}
    original_budget_manager = llm_gateway_service.BudgetManager

    def _budget_manager(estimated_input_tokens, estimated_output_tokens, spec):
        budget_calls["count"] += 1
        return original_budget_manager(estimated_input_tokens, estimated_output_tokens, spec)

    monkeypatch.setattr(llm_gateway_service, "BudgetManager", _budget_manager)
    service = build_default_service()
    provider = _ProviderSpy()
    eris_spy = _ErisSpy()

    service.provider_client = provider  # type: ignore[assignment]
    service.eris_client = eris_spy  # type: ignore[assignment]

    request = _build_request(max_tokens=4096)

    with pytest.raises(HTTPException) as excinfo:
        await service.handle_chat(request)

    assert excinfo.value.status_code == 429
    assert isinstance(excinfo.value.detail, dict)
    assert excinfo.value.detail["reason_code"] == TOK_BUDGET_OUTPUT_EXCEEDED
    assert provider.called is False

    assert eris_spy.payloads
    receipt = eris_spy.payloads[-1]
    assert_enforcement_receipt_fields(receipt, require_correlation=True)
    assert receipt["decision"] == "deny"
    assert receipt["reason_code"] == TOK_BUDGET_OUTPUT_EXCEEDED
    assert "user_prompt" not in receipt
    assert budget_calls["count"] == 1


@pytest.mark.asyncio
@pytest.mark.smoke
@pytest.mark.unit
async def test_recovery_retry_emits_receipt_fields(monkeypatch) -> None:
    from cloud_services.llm_gateway.services import llm_gateway_service

    recovery_calls = {"count": 0}
    original_recovery = llm_gateway_service.call_with_recovery_async

    async def _call_with_recovery_async(*args, **kwargs):
        recovery_calls["count"] += 1
        return await original_recovery(*args, **kwargs)

    monkeypatch.setattr(
        llm_gateway_service, "call_with_recovery_async", _call_with_recovery_async
    )
    service = build_default_service()
    provider = _ProviderRetrySpy()
    eris_spy = _ErisSpy()

    service.provider_client = provider  # type: ignore[assignment]
    service.eris_client = eris_spy  # type: ignore[assignment]

    request = _build_request(max_tokens=512)

    response = await service.handle_chat(request)

    assert response.decision is Decision.ALLOWED
    assert provider.calls == 2
    assert eris_spy.payloads

    receipt = eris_spy.payloads[-1]
    assert_enforcement_receipt_fields(receipt, require_correlation=True)
    assert receipt["reason_code"] == TOK_BUDGET_OK
    recovery = receipt["recovery"]["primary"]
    assert recovery["attempts_made"] == 2
    assert recovery["final_outcome"] == "success"
    assert recovery["last_error_code"] == "TimeoutError"
    assert recovery_calls["count"] == 1


@pytest.mark.asyncio
@pytest.mark.smoke
@pytest.mark.unit
async def test_sse_guard_terminates_stream_with_receipt(monkeypatch) -> None:
    from shared_libs.sse_guard import SSEGuard

    wrap_calls = {"count": 0}
    original_wrap = SSEGuard.wrap

    async def _wrap(self, events):
        wrap_calls["count"] += 1
        async for payload in original_wrap(self, events):
            yield payload

    monkeypatch.setattr(SSEGuard, "wrap", _wrap)
    monkeypatch.setenv("ALERT_STREAM_HEARTBEAT_SECONDS", "0.01")
    get_settings.cache_clear()
    settings = get_settings()
    settings.notifications.agent_stream_max_events = 1

    ctx = RequestContext(
        tenant_id="tenant-platform",
        actor_id="tester",
        roles=["global_admin"],
        allowed_tenants=["tenant-platform"],
        token_sub="tester",
    )

    receipts: list[dict] = []

    async def _capture_receipt(payload: dict) -> None:
        receipts.append(payload)

    monkeypatch.setattr(
        alerting_routes._evidence_service.eris,
        "emit_receipt",
        _capture_receipt,
    )

    response = await alerting_routes.stream_alerts(session=None, ctx=ctx)

    try:
        chunk = await asyncio.wait_for(response.body_iterator.__anext__(), timeout=1.0)
        payload = chunk.decode() if isinstance(chunk, bytes) else chunk
        assert "data:" in payload

        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(response.body_iterator.__anext__(), timeout=0.5)
    finally:
        aclose = getattr(response.body_iterator, "aclose", None)
        if callable(aclose):
            await aclose()
        get_settings.cache_clear()

    assert receipts
    receipt = next(item for item in receipts if item.get("type") == "sse_guard_terminated")
    assert_enforcement_receipt_fields(receipt, require_correlation=True)
    metadata = receipt.get("metadata", {})
    assert metadata.get("reason_code") == "SSE_MAX_EVENTS"
    assert metadata.get("limits", {}).get("max_events") == 1
    assert metadata.get("observed", {}).get("events") == 1
    assert wrap_calls["count"] == 1


@pytest.mark.smoke
@pytest.mark.unit
def test_tool_output_validation_blocks_invalid_payload(monkeypatch) -> None:
    session = _build_session()
    tenant_id = "tenant-tool"
    provider_id = "platform-smoke-invalid"
    connection = _seed_connection(session, tenant_id, provider_id)

    class InvalidAdapter(BaseAdapter):
        def process_webhook(self, payload, headers):
            return {}

        def poll_events(self, cursor=None):
            return [], cursor

        def execute_action(self, action):
            return {"status": "ok"}

        def verify_connection(self):
            return True

        def get_capabilities(self):
            return {"outbound_actions_supported": True}

    registry = get_adapter_registry()
    registry.register_adapter(provider_id, InvalidAdapter)

    eris_client = _StubERISClient()
    service = IntegrationService(
        session=session,
        kms_client=_StubKMSClient(),
        budget_client=_StubBudgetClient(),
        pm3_client=None,
        eris_client=eris_client,
    )
    service.metrics = _StubMetrics()
    validate_calls = {"count": 0}
    original_validate = service._tool_output_validator.validate

    def _validate(tool_id, payload):
        validate_calls["count"] += 1
        return original_validate(tool_id, payload)

    monkeypatch.setattr(service._tool_output_validator, "validate", _validate)

    action_data = {
        "provider_id": provider_id,
        "connection_id": str(connection.connection_id),
        "canonical_type": "post_chat_message",
        "target": {"channel_id": "C123"},
        "payload": {"text": "hello"},
        "idempotency_key": "idem-platform",
        "correlation_id": "corr-1",
    }

    with pytest.raises(ToolOutputSchemaViolation) as excinfo:
        service.execute_action(tenant_id, action_data)

    assert excinfo.value.reason_code == TOOL_OUTPUT_SCHEMA_VIOLATION
    stored_action = (
        session.query(NormalisedAction)
        .filter(NormalisedAction.idempotency_key == "idem-platform")
        .first()
    )
    assert stored_action is not None
    assert stored_action.status == "failed"
    assert stored_action.payload == {"error": "tool output schema violation"}

    assert eris_client.receipts
    receipt = eris_client.receipts[-1]
    assert_enforcement_receipt_fields(receipt, require_correlation=True)
    result = receipt.get("result", {})
    assert result.get("reason_code") == TOOL_OUTPUT_SCHEMA_VIOLATION
    assert result.get("tool_id") == f"{provider_id}.post_chat_message"
    assert "payload" not in result
    assert validate_calls["count"] == 1


@pytest.mark.smoke
@pytest.mark.unit
def test_mcp_unpinned_server_blocked_at_factory(monkeypatch) -> None:
    receipts: list[dict[str, str]] = []
    verify_calls = {"count": 0}

    def _emit_receipt(payload: dict[str, str]) -> None:
        receipts.append(payload)

    registry = MCPServerRegistry(
        servers=(
            MCPServerEntry(
                server_id="mcp.unpinned",
                display_name="Unpinned MCP",
                endpoint="https://mcp.example/api",
                enabled=True,
                pinned_version=None,
                pinned_digest=None,
            ),
        )
    )
    verifier = MCPVerifier(receipt_emitter=_emit_receipt)
    original_verify = verifier.verify

    def _verify(entry, identity=None):
        verify_calls["count"] += 1
        return original_verify(entry, identity)

    monkeypatch.setattr(verifier, "verify", _verify)
    factory = MCPClientFactory(registry, verifier)

    result = factory.create_client("mcp.unpinned")

    assert result.handle is None
    assert result.error is not None
    assert result.error.reason_code == MCP_UNPINNED_SERVER
    assert receipts
    receipt = receipts[0]
    assert_enforcement_receipt_fields(receipt)
    assert receipt["reason_code"] == MCP_UNPINNED_SERVER
    assert verify_calls["count"] == 1
