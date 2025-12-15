from __future__ import annotations
"""
Unit tests for LLM Gateway service logic using the golden corpora.
"""


import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]

from cloud_services.llm_gateway.models import (  # type: ignore  # pylint: disable=import-error
    Actor,
    Budget,
    Decision,
    LLMRequest,
    OperationType,
    SafetyOverrides,
    Tenant,
)
from cloud_services.llm_gateway.clients import (  # type: ignore  # pylint: disable=import-error
    ProviderUnavailableError,
)
from cloud_services.llm_gateway.services import build_default_service  # type: ignore  # pylint: disable=import-error

BENIGN_CORPUS = (
    PROJECT_ROOT / "docs" / "architecture" / "tests" / "golden" / "llm_gateway" / "benign_corpus.jsonl"
)
ADVERSARIAL_CORPUS = (
    PROJECT_ROOT / "docs" / "architecture" / "tests" / "golden" / "llm_gateway" / "adversarial_corpus.jsonl"
)


def _load_entry(path: Path, entry_id: str) -> dict:
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry["id"] == entry_id:
            return entry
    raise AssertionError(f"Entry {entry_id} not found in {path}")


def _build_request(entry: dict) -> LLMRequest:
    return LLMRequest(
        request_id=f"req-{entry['id']}",
        actor=Actor(
            actor_id="actor-1234",
            actor_type="human",
            roles=["developer"],
            capabilities=["llm.invoke"],
            scopes=[f"llm.{entry['operation_type']}"],
            session_assurance_level="high",
            workspace_id="workspace-1",
        ),
        tenant=Tenant(tenant_id="tenantA", region="us-east"),
        logical_model_id="default_chat",
        operation_type=OperationType(entry["operation_type"]),
        intended_capability="analysis",
        sensitivity_level="medium",
        system_prompt_id="sys-default",
        user_prompt=entry["prompt"],
        context_segments=[],
        policy_snapshot_id="policy-snap-1",
        policy_version_ids=["policy-v1"],
        budget=Budget(
            max_tokens=2048,
            timeout_ms=2000,
            priority="normal",
            temperature=0.2,
        ),
        safety_overrides=SafetyOverrides(),
    )


@pytest.mark.asyncio
@pytest.mark.llm_gateway_unit
async def test_prompt_injection_is_blocked() -> None:
    service = build_default_service()
    entry = _load_entry(ADVERSARIAL_CORPUS, "ADV-001")
    request = _build_request(entry)

    response = await service.handle_chat(request)

    assert response.decision is Decision.BLOCKED
    assert response.risk_flags[0].risk_class.value == "R1"


@pytest.mark.asyncio
@pytest.mark.llm_gateway_unit
async def test_benign_prompt_is_allowed() -> None:
    service = build_default_service()
    entry = _load_entry(BENIGN_CORPUS, "BENIGN-001")
    request = _build_request(entry)

    response = await service.handle_chat(request)

    assert response.decision is Decision.ALLOWED
    assert response.output is not None
    # Provider content should come from the routed provider client
    assert response.output.content.startswith("[provider/")
    # Meta-prompt enforcement: ensure meta prefix derived from system_prompt_id + tenant
    assert "[META:sys-default][TENANT:tenantA]" in response.output.content


@pytest.mark.asyncio
@pytest.mark.llm_gateway_unit
async def test_embedding_fallback_uses_embedding_route() -> None:
    service = build_default_service()

    class _FailingThenFallbackProvider:
        def __init__(self) -> None:
            self.calls = []

        def invoke(
            self,
            tenant_id: str,
            logical_model_id: str,
            prompt: str,
            operation_type: str,
            fallback: bool = False,
        ):
            self.calls.append((logical_model_id, fallback))
            if not fallback:
                raise ProviderUnavailableError("primary down")
            return {
                "model": f"provider/{logical_model_id}",
                "content": f"[{logical_model_id}] response for {operation_type}",
            }

    service.provider_client = _FailingThenFallbackProvider()  # type: ignore[assignment]

    request = LLMRequest(
        request_id="req-embed-001",
        actor=Actor(
            actor_id="actor-embed",
            actor_type="human",
            roles=["developer"],
            capabilities=["llm.invoke"],
            scopes=["llm.embedding"],
            session_assurance_level="high",
            workspace_id="workspace-embed",
        ),
        tenant=Tenant(tenant_id="tenantA", region="us-east"),
        logical_model_id="default_embedding",
        operation_type=OperationType.EMBEDDING,
        intended_capability="embedding",
        sensitivity_level="medium",
        system_prompt_id="sys-embed",
        user_prompt="vectorize this text",
        context_segments=[],
        policy_snapshot_id="policy-snap-1",
        policy_version_ids=["policy-v1"],
        budget=Budget(
            max_tokens=2048,
            timeout_ms=2000,
            priority="normal",
            temperature=0.2,
        ),
        safety_overrides=SafetyOverrides(),
    )

    response = await service.handle_embedding(request)

    assert response.decision is Decision.ALLOWED
    assert response.degradation_stage == "REROUTED"
    assert response.fallback_chain and response.fallback_chain[-1]["logical_model_id"] == "fallback_embedding"
    assert response.output is not None
    assert "fallback_embedding" in response.output.content

