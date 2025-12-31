from __future__ import annotations

import json

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


def _build_request(max_tokens: int) -> LLMRequest:
    return LLMRequest(
        request_id="req-policy-budget",
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


@pytest.mark.asyncio
@pytest.mark.llm_gateway_unit
async def test_policy_config_overrides_token_budget(monkeypatch, tmp_path) -> None:
    allow_policy = {
        "token_budgets": {
            "max_input_tokens": 1000,
            "max_output_tokens": 1000,
            "max_total_tokens": 2000,
        },
        "recovery": {"max_attempts": 2, "base_delay_ms": 50, "max_delay_ms": 200},
    }
    deny_policy = {
        "token_budgets": {
            "max_input_tokens": 1000,
            "max_output_tokens": 1,
            "max_total_tokens": 2000,
        },
        "recovery": {"max_attempts": 2, "base_delay_ms": 50, "max_delay_ms": 200},
    }

    allow_path = tmp_path / "policy_allow.json"
    allow_path.write_text(json.dumps(allow_policy), encoding="utf-8")
    deny_path = tmp_path / "policy_deny.json"
    deny_path.write_text(json.dumps(deny_policy), encoding="utf-8")

    request = _build_request(max_tokens=512)

    monkeypatch.setenv("LLM_GATEWAY_POLICY_PATH", str(allow_path))
    service = build_default_service()
    provider = _ProviderSpy()
    service.provider_client = provider  # type: ignore[assignment]

    response = await service.handle_chat(request)

    assert provider.called is True
    assert response.decision is Decision.ALLOWED

    monkeypatch.setenv("LLM_GATEWAY_POLICY_PATH", str(deny_path))
    service = build_default_service()
    provider = _ProviderSpy()
    service.provider_client = provider  # type: ignore[assignment]

    with pytest.raises(HTTPException) as excinfo:
        await service.handle_chat(request)

    assert excinfo.value.detail["reason_code"] == TOK_BUDGET_OUTPUT_EXCEEDED
    assert provider.called is False
