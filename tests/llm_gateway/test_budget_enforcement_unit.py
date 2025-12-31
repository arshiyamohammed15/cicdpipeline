from __future__ import annotations

import pytest
from fastapi import HTTPException

from cloud_services.llm_gateway.models import (  # type: ignore  # pylint: disable=import-error
    Actor,
    Budget,
    Decision,
    LLMRequest,
    OperationType,
    SafetyOverrides,
    Tenant,
)
from cloud_services.llm_gateway.services import build_default_service  # type: ignore  # pylint: disable=import-error
from shared_libs.token_budget import TOK_BUDGET_OUTPUT_EXCEEDED
from tests.shared_harness import assert_enforcement_receipt_fields


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


class _ErisSpy:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def emit_receipt(self, payload: dict) -> str:
        self.payloads.append(payload)
        return payload.get("receipt_id", "")


def _build_request(max_tokens: int) -> LLMRequest:
    return LLMRequest(
        request_id="req-budget-001",
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
            timeout_ms=2000,
            priority="normal",
            temperature=0.2,
        ),
        safety_overrides=SafetyOverrides(),
    )


@pytest.mark.asyncio
@pytest.mark.llm_gateway_unit
async def test_budget_deny_blocks_provider_call() -> None:
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
    assert_enforcement_receipt_fields(eris_spy.payloads[-1])


@pytest.mark.asyncio
@pytest.mark.llm_gateway_unit
async def test_budget_allow_calls_provider() -> None:
    service = build_default_service()
    provider = _ProviderSpy()
    service.provider_client = provider  # type: ignore[assignment]

    request = _build_request(max_tokens=512)

    response = await service.handle_chat(request)

    assert provider.called is True
    assert response.decision is Decision.ALLOWED
