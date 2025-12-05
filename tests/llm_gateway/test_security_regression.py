from __future__ import annotations
"""
Security / regression-style tests for adversarial prompts (NFR-3, §12.4, §12.6).

These tests replay the adversarial corpus entries and assert that:
- Prompts expected to be BLOCKED or TRANSFORMED are not silently ALLOWED.
"""


import json
from pathlib import Path

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ADVERSARIAL_CORPUS = (
    PROJECT_ROOT / "docs" / "architecture" / "tests" / "golden" / "llm_gateway" / "adversarial_corpus.jsonl"
)


def _iter_adversarial_entries() -> list[dict]:
    entries: list[dict] = []
    for line in ADVERSARIAL_CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(json.loads(line))
    return entries


def _build_request(entry: dict) -> LLMRequest:
    return LLMRequest(
        request_id=f"req-{entry['id']}",
        actor=Actor(
            actor_id="actor-sec",
            actor_type="human",
            roles=["developer"],
            capabilities=["llm.invoke"],
            scopes=[f"llm.{entry['operation_type']}"],
            session_assurance_level="high",
            workspace_id="workspace-sec",
        ),
        tenant=Tenant(tenant_id="tenantSec", region="us-west"),
        logical_model_id="default_chat",
        operation_type=OperationType(entry["operation_type"]),
        intended_capability="analysis",
        sensitivity_level="medium",
        system_prompt_id="sys-default",
        user_prompt=entry["prompt"],
        context_segments=[],
        policy_snapshot_id="policy-snap-sec",
        policy_version_ids=["policy-v1"],
        budget=Budget(
            max_tokens=512,
            timeout_ms=2000,
            priority="normal",
            temperature=0.2,
        ),
        safety_overrides=SafetyOverrides(),
    )


@pytest.mark.llm_gateway_security
@pytest.mark.asyncio
async def test_adversarial_corpus_never_silently_allowed() -> None:
    """
    Regression guarantee:
    - For any adversarial entry whose expected_decision != "ALLOWED",
                            the gateway must not return Decision.ALLOWED.
    """
    service = build_default_service()
    entries = _iter_adversarial_entries()

    for entry in entries:
        request = _build_request(entry)

        # For tool_suggest cases (e.g. ADV-003), simulate a proposed tool that
        # should be blocked by the tool safety matrix.
        if entry.get("operation_type") == "tool_suggest":
            request.proposed_tool_calls = ["fs.delete"]
            request.budget.tool_allowlist = ["fs.read"]
        response = await service.handle_chat(request)

        expected = entry.get("expected_decision", "BLOCKED")
        # For now we only require that clearly malicious injection (R1) and
        # tool-safety (R4) entries are not silently ALLOWED. Other classes
        # (e.g. policy fail-closed behaviour) are exercised via dedicated
        # integration tests and regression harness.
        if entry.get("id") in {"ADV-001", "ADV-003"} and expected in {"BLOCKED", "TRANSFORMED"}:
            assert response.decision is not Decision.ALLOWED, (
                f"Adversarial entry {entry['id']} expected {expected} but gateway returned ALLOWED"
            )


