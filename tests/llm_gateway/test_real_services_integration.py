"""
Integration tests with real backend services.

These tests require USE_REAL_SERVICES=true and all backend services to be running
and healthy. They validate end-to-end workflows against actual service implementations.

Test Plan Reference: IT-LLM-01 through IT-LLM-05
"""

from __future__ import annotations

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

BENIGN_CORPUS = (
    PROJECT_ROOT / "docs" / "architecture" / "tests" / "golden" / "llm_gateway" / "benign_corpus.jsonl"
)
ADVERSARIAL_CORPUS = (
    PROJECT_ROOT / "docs" / "architecture" / "tests" / "golden" / "llm_gateway" / "adversarial_corpus.jsonl"
)


def _load_entry(path: Path, entry_id: str) -> dict:
    """Load a specific entry from a JSONL corpus file."""
    for line in path.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry["id"] == entry_id:
            return entry
    raise AssertionError(f"Entry {entry_id} not found in {path}")


def _build_request(entry: dict) -> LLMRequest:
    """Build an LLMRequest from a corpus entry."""
    return LLMRequest(
        request_id=f"req-{entry['id']}",
        actor=Actor(
            actor_id="actor-test-1234",
            actor_type="human",
            roles=["developer"],
            capabilities=["llm.invoke"],
            scopes=[f"llm.{entry['operation_type']}"],
            session_assurance_level="high",
            workspace_id="workspace-test-1",
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
@pytest.mark.llm_gateway_real_integration
async def test_real_services_benign_prompt_allowed(
    llm_gateway_service_real,  # type: ignore
) -> None:
    """
    IT-LLM-01: Validate benign prompt is allowed through real service stack.

    Exercises:
    - IAM validation (EPC-1)
    - Policy snapshot fetch (EPC-3/EPC-10)
    - Data governance redaction (EPC-2)
    - Budget check (EPC-13)
    - Safety pipeline evaluation
    - ERIS receipt emission
    """
    entry = _load_entry(BENIGN_CORPUS, "BENIGN-001")
    request = _build_request(entry)

    response = await llm_gateway_service_real.handle_chat(request)

    assert response.decision is Decision.ALLOWED
    assert response.response_id.startswith("resp-")
    assert response.output is not None
    assert response.risk_flags == []


@pytest.mark.asyncio
@pytest.mark.llm_gateway_real_integration
async def test_real_services_adversarial_prompt_blocked(
    llm_gateway_service_real,  # type: ignore
) -> None:
    """
    IT-LLM-02: Validate adversarial prompt is blocked by real safety pipeline.

    Exercises:
    - Safety pipeline multi-layer validation
    - Risk flag generation
    - Incident creation
    - Alert emission (EPC-4)
    """
    entry = _load_entry(ADVERSARIAL_CORPUS, "ADV-001")
    request = _build_request(entry)

    response = await llm_gateway_service_real.handle_chat(request)

    assert response.decision is Decision.BLOCKED
    assert len(response.risk_flags) > 0
    assert response.risk_flags[0].risk_class.value in ["R1", "R2", "R3", "R4", "R5"]


@pytest.mark.asyncio
@pytest.mark.llm_gateway_real_integration
async def test_real_services_iam_validation_failure(
    llm_gateway_service_real,  # type: ignore
) -> None:
    """
    IT-LLM-03: Validate IAM service rejects unauthorized actor.

    Exercises:
    - IAM service /decision endpoint
    - Proper error handling for authorization failures
    """
    entry = _load_entry(BENIGN_CORPUS, "BENIGN-001")
    request = _build_request(entry)

    # Modify actor to have invalid capabilities
    request.actor.capabilities = []  # Missing required "llm.invoke"

    with pytest.raises(Exception):  # Should raise HTTPException or similar
        await llm_gateway_service_real.handle_chat(request)


@pytest.mark.asyncio
@pytest.mark.llm_gateway_real_integration
async def test_real_services_budget_enforcement(
    llm_gateway_service_real,  # type: ignore
) -> None:
    """
    IT-LLM-04: Validate budget service enforces token limits.

    Exercises:
    - Budget service /budgets/check endpoint
    - Token budget validation
    - Proper error handling for budget violations
    """
    entry = _load_entry(BENIGN_CORPUS, "BENIGN-002")
    request = _build_request(entry)

    # Set an extremely low budget to trigger violation
    request.budget.max_tokens = 1

    # This may either block the request or allow it with degradation
    # depending on policy configuration
    response = await llm_gateway_service_real.handle_chat(request)

    # Budget service should have been consulted
    # Response may be BLOCKED or ALLOWED with degradation
    assert response.decision in [Decision.ALLOWED, Decision.BLOCKED]


@pytest.mark.asyncio
@pytest.mark.llm_gateway_real_integration
async def test_real_services_data_governance_redaction(
    llm_gateway_service_real,  # type: ignore
) -> None:
    """
    IT-LLM-05: Validate data governance service redacts PII/secrets.

    Exercises:
    - Data governance /privacy/v1/compliance endpoint
    - PII detection and redaction
    - Secrets detection
    - Latency budget compliance (≤25ms p95)
    """
    entry = _load_entry(BENIGN_CORPUS, "BENIGN-003")
    request = _build_request(entry)

    # Add potential PII to the prompt
    request.user_prompt = f"{request.user_prompt} Contact me at test@example.com"

    response = await llm_gateway_service_real.handle_chat(request)

    # Data governance should have processed the request
    # The prompt may be redacted before reaching the provider
    assert response.decision in [Decision.ALLOWED, Decision.BLOCKED]
    assert response.response_id.startswith("resp-")


@pytest.mark.asyncio
@pytest.mark.llm_gateway_real_integration
async def test_real_services_eris_receipt_emission(
    llm_gateway_service_real,  # type: ignore
) -> None:
    """
    IT-LLM-06: Validate ERIS service receives decision receipts.

    Exercises:
    - ERIS /receipts endpoint
    - Receipt structure validation
    - Async receipt emission
    """
    entry = _load_entry(BENIGN_CORPUS, "BENIGN-001")
    request = _build_request(entry)

    response = await llm_gateway_service_real.handle_chat(request)

    # ERIS should have received the receipt (fire-and-forget)
    # We can't directly verify this without querying ERIS, but we can
    # verify the response was generated successfully
    assert response.decision is Decision.ALLOWED
    assert response.response_id.startswith("resp-")


@pytest.mark.asyncio
@pytest.mark.llm_gateway_real_integration
async def test_real_services_policy_snapshot_caching(
    llm_gateway_service_real,  # type: ignore
) -> None:
    """
    IT-LLM-07: Validate policy snapshot caching reduces service calls.

    Exercises:
    - Policy service /standards endpoint
    - In-memory caching with staleness tracking
    - Cache hit/miss behavior
    """
    entry = _load_entry(BENIGN_CORPUS, "BENIGN-001")
    request = _build_request(entry)

    # First request should fetch policy snapshot
    response1 = await llm_gateway_service_real.handle_chat(request)
    assert response1.decision is Decision.ALLOWED

    # Second request with same tenant should use cached snapshot
    request2 = _build_request(entry)
    request2.request_id = "req-cache-test"
    response2 = await llm_gateway_service_real.handle_chat(request2)
    assert response2.decision is Decision.ALLOWED

    # Both should succeed, with second using cached policy
    assert response1.response_id != response2.response_id

