from __future__ import annotations
"""
Security / regression-style tests for adversarial prompts (NFR-3, §12.4, §12.6).

These tests replay the adversarial corpus entries and assert that:
- Prompts expected to be BLOCKED or TRANSFORMED are not silently ALLOWED.
"""


import json
import os
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
FULL_CORPUS_ENV = "LLM_GATEWAY_SECURITY_FULL_CORPUS"
ENTRY_IDS_ENV = "LLM_GATEWAY_SECURITY_ENTRY_IDS"
PARALLEL_ENV = "LLM_GATEWAY_SECURITY_PARALLEL"
CONCURRENCY_ENV = "LLM_GATEWAY_SECURITY_CONCURRENCY"
CHECK_ENTRY_IDS = {"ADV-001", "ADV-003"}
DEFAULT_FAST_IDS = set(CHECK_ENTRY_IDS)


def _parse_bool_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _selected_entry_ids() -> set[str] | None:
    if _parse_bool_env(FULL_CORPUS_ENV):
        return None

    raw_ids = os.getenv(ENTRY_IDS_ENV, "")
    if raw_ids.strip():
        ids = {item.strip() for item in raw_ids.split(",") if item.strip()}
        if ids:
            return ids

    return set(DEFAULT_FAST_IDS)


def _iter_adversarial_entries() -> list[dict]:
    entries: list[dict] = []
    for line in ADVERSARIAL_CORPUS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(json.loads(line))
    selected_ids = _selected_entry_ids()
    if selected_ids is None:
        return entries

    filtered = [entry for entry in entries if entry.get("id") in selected_ids]
    if not filtered:
        raise AssertionError(
            f"No adversarial corpus entries matched {selected_ids}. "
            f"Set {FULL_CORPUS_ENV}=true to run the full corpus."
        )
    return filtered


def _prepare_request(entry: dict) -> LLMRequest:
    request = _build_request(entry)
    if entry.get("operation_type") == "tool_suggest":
        request.proposed_tool_calls = ["fs.delete"]
        request.budget.tool_allowlist = ["fs.read"]
    return request


def _assert_expected_not_allowed(entry: dict, response) -> None:
    expected = entry.get("expected_decision", "BLOCKED")
    if entry.get("id") in CHECK_ENTRY_IDS and expected in {"BLOCKED", "TRANSFORMED"}:
        assert response.decision is not Decision.ALLOWED, (
            f"Adversarial entry {entry['id']} expected {expected} but gateway returned ALLOWED"
        )


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
    - For default fast runs, validate the high-risk corpus subset.
    - Set LLM_GATEWAY_SECURITY_FULL_CORPUS=true to run the full corpus.
    - Set LLM_GATEWAY_SECURITY_ENTRY_IDS to run a specific subset.
    - Set LLM_GATEWAY_SECURITY_PARALLEL=true to evaluate entries concurrently.
    """
    service = build_default_service()
    entries = _iter_adversarial_entries()

    if _parse_bool_env(PARALLEL_ENV) and len(entries) > 1:
        import asyncio

        raw_limit = os.getenv(CONCURRENCY_ENV, "8")
        try:
            concurrency = max(1, int(raw_limit))
        except ValueError:
            concurrency = 8

        semaphore = asyncio.Semaphore(concurrency)

        async def _run_entry(entry: dict):
            async with semaphore:
                request = _prepare_request(entry)
                response = await service.handle_chat(request)
                return entry, response

        tasks = [asyncio.create_task(_run_entry(entry)) for entry in entries]
        for task in asyncio.as_completed(tasks):
            entry, response = await task
            _assert_expected_not_allowed(entry, response)
        return

    for entry in entries:
        request = _prepare_request(entry)
        response = await service.handle_chat(request)
        _assert_expected_not_allowed(entry, response)


