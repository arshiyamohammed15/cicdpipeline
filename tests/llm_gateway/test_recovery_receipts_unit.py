from __future__ import annotations

import pytest

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


class _ErisSpy:
    def __init__(self) -> None:
        self.payloads: list[dict] = []

    def emit_receipt(self, payload: dict) -> str:
        self.payloads.append(payload)
        return payload.get("receipt_id", "")


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
        *args,
        **kwargs,
    ) -> dict[str, str]:
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("timeout")
        return {
            "model": f"provider/{logical_model_id}",
            "content": f"[provider/{logical_model_id}] response for {operation_type}",
        }


def _build_request(max_tokens: int) -> LLMRequest:
    return LLMRequest(
        request_id="req-recovery-001",
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
async def test_receipt_includes_recovery_fields() -> None:
    service = build_default_service()
    provider = _ProviderRetrySpy()
    eris_spy = _ErisSpy()

    service.provider_client = provider  # type: ignore[assignment]
    service.eris_client = eris_spy  # type: ignore[assignment]

    request = _build_request(max_tokens=512)

    response = await service.handle_chat(request)

    assert response.decision is Decision.ALLOWED
    assert eris_spy.payloads, "Expected at least one receipt payload"

    receipt = eris_spy.payloads[-1]
    recovery = receipt["recovery"]["primary"]
    assert recovery["attempts_made"] == 2
    assert recovery["final_outcome"] == "success"
    assert recovery["recovery_applied"] is True
    assert recovery["last_error_code"] == "TimeoutError"
    assert recovery["timeout_applied_ms"] == 1500
    assert "user_prompt" not in receipt
