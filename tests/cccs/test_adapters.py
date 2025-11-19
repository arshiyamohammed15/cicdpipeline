"""
Tests for EPC/PM adapter mocks and integration.

Covers adapter behavior, failure handling, and integration with services.
"""

import pytest
from datetime import datetime, timezone
from src.shared_libs.cccs.adapters.epc1_adapter import EPC1AdapterConfig
from src.shared_libs.cccs.adapters.epc3_adapter import EPC3AdapterConfig
from src.shared_libs.cccs.adapters.epc13_adapter import EPC13AdapterConfig
from src.shared_libs.cccs.adapters.epc11_adapter import EPC11AdapterConfig
from src.shared_libs.cccs.adapters.pm7_adapter import PM7AdapterConfig
from src.shared_libs.cccs.exceptions import BudgetExceededError
from src.shared_libs.cccs.types import ActorContext
from tests.cccs.mocks import (
    MockEPC1Adapter,
    MockEPC3Adapter,
    MockEPC13Adapter,
    MockEPC11Adapter,
    MockPM7Adapter,
)


def test_epc1_adapter_resolve_actor():
    """Test EPC-1 adapter resolves actor correctly."""
    config = EPC1AdapterConfig(base_url="http://localhost:8001")
    adapter = MockEPC1Adapter(config)

    context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    import asyncio

    actor = asyncio.run(adapter.resolve_actor(context))
    assert actor.actor_id == "actor-u1"
    assert actor.provenance_signature == "sig-u1"
    assert actor.normalization_version == "v1"


def test_epc1_adapter_failure_handling():
    """Test EPC-1 adapter handles failures."""
    config = EPC1AdapterConfig(base_url="http://localhost:8001")
    adapter = MockEPC1Adapter(config)
    adapter._fail_verify = True

    context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    import asyncio

    with pytest.raises(Exception, match="EPC-1 verification failed"):
        asyncio.run(adapter.resolve_actor(context))


def test_epc3_adapter_signature_validation():
    """Test EPC-3 adapter validates signatures."""
    config = EPC3AdapterConfig(base_url="http://localhost:8003")
    adapter = MockEPC3Adapter(config)

    payload = {"module_id": "m01", "version": "1.0.0", "rules": []}
    import asyncio

    # Valid signature
    assert asyncio.run(adapter.validate_snapshot_signature(payload, "valid-sig")) is True

    # Invalid signature
    assert asyncio.run(adapter.validate_snapshot_signature(payload, "invalid")) is False


def test_epc3_adapter_policy_evaluation():
    """Test EPC-3 adapter evaluates policies."""
    config = EPC3AdapterConfig(base_url="http://localhost:8003")
    adapter = MockEPC3Adapter(config)

    payload = {
        "module_id": "m01",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "allow-low-risk",
                "priority": 1,
                "conditions": {"risk": {"op": "lte", "value": 3}},
                "decision": "allow",
                "rationale": "low_risk",
            }
        ],
    }

    import asyncio

    snapshot = asyncio.run(adapter.load_snapshot(payload, "valid-sig"))
    decision = asyncio.run(adapter.evaluate_policy("m01", {"risk": 2}))
    assert decision.decision == "allow"
    assert decision.rationale == "low_risk"


def test_epc13_adapter_budget_check():
    """Test EPC-13 adapter checks budgets."""
    config = EPC13AdapterConfig(base_url="http://localhost:8013")
    adapter = MockEPC13Adapter(config)

    import asyncio

    # First check should succeed
    decision1 = asyncio.run(adapter.check_budget("action1", 50.0))
    assert decision1.allowed is True
    assert decision1.remaining == 50.0

    # Second check should succeed
    decision2 = asyncio.run(adapter.check_budget("action1", 30.0))
    assert decision2.allowed is True
    assert decision2.remaining == 20.0

    # Third check should fail (exceeds remaining)
    with pytest.raises(BudgetExceededError):
        asyncio.run(adapter.check_budget("action1", 30.0))


def test_epc13_adapter_default_deny():
    """Test EPC-13 adapter denies by default when unavailable."""
    config = EPC13AdapterConfig(
        base_url="http://localhost:8013", default_deny_on_unavailable=True
    )
    adapter = MockEPC13Adapter(config)
    adapter._fail_check = True

    import asyncio

    with pytest.raises(BudgetExceededError, match="EPC-13 unavailable"):
        asyncio.run(adapter.check_budget("action1", 10.0))


def test_epc11_adapter_signing():
    """Test EPC-11 adapter signs receipts."""
    config = EPC11AdapterConfig(base_url="http://localhost:8011", key_id="key-1")
    adapter = MockEPC11Adapter(config)

    payload = {"receipt_id": "r1", "data": "test"}
    import asyncio

    signature = asyncio.run(adapter.sign_receipt(payload))
    assert signature.startswith("ed25519:")

    # Verify signature
    valid = asyncio.run(adapter.verify_signature(payload, signature))
    assert valid is True

    # Invalid signature
    valid = asyncio.run(adapter.verify_signature(payload, "invalid-sig"))
    assert valid is False


def test_pm7_adapter_indexing(tmp_path):
    """Test PM-7 adapter indexes receipts."""
    config = PM7AdapterConfig(base_url="http://localhost:8007")
    adapter = MockPM7Adapter(config)

    receipt = {"receipt_id": "r1", "data": "test"}
    import asyncio

    result = asyncio.run(adapter.index_receipt(receipt))
    assert result["receipt_id"] == "r1"
    assert "merkle_root" in result
    assert len(adapter._indexed_receipts) == 1


def test_pm7_adapter_merkle_proof(tmp_path):
    """Test PM-7 adapter generates Merkle proofs."""
    config = PM7AdapterConfig(base_url="http://localhost:8007")
    adapter = MockPM7Adapter(config)

    import asyncio

    proof = asyncio.run(adapter.generate_merkle_proof("r1", "batch-1"))
    assert proof["receipt_id"] == "r1"
    assert "path" in proof
    assert "root" in proof
    assert "leaf_hash" in proof

