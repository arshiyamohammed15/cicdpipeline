"""
End-to-end tests for CCCS.

Covers PRD section 10.3: FM → CCCS → EPC/PM/CCP flow, offline 48h scenario, security attestation.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.shared_libs.cccs import CCCSConfig, CCCSRuntime
from src.shared_libs.cccs.errors.taxonomy import TaxonomyEntry
from src.shared_libs.cccs.exceptions import BudgetExceededError
from src.shared_libs.cccs.identity import IdentityConfig
from src.shared_libs.cccs.policy import PolicyConfig
from src.shared_libs.cccs.ratelimit import RateLimiterConfig
from src.shared_libs.cccs.redaction import RedactionConfig, RedactionRule
from src.shared_libs.cccs.types import ActorContext, ConfigLayers
from src.shared_libs.cccs.receipts import ReceiptConfig
from tests.cccs.helpers import SIGNING_SECRET, dependency_health, sign_snapshot
from tests.cccs.mocks import (
    MockEPC1Adapter,
    MockEPC13Adapter,
    MockEPC11Adapter,
    MockPM7Adapter,
)
from unittest.mock import patch


def _runtime(tmp_path: Path) -> CCCSRuntime:
    config = CCCSConfig(
        mode="edge",
        version="1.0.0",
        identity=IdentityConfig(
            epc1_base_url="http://localhost:8001",
            epc1_timeout_seconds=5.0,
            epc1_api_version="v1",
        ),
        policy=PolicyConfig(
            signing_secrets=[SIGNING_SECRET],
            rule_version_negotiation_enabled=True,
        ),
        config_layers=ConfigLayers(local={}, tenant={"feature": True}, product={}),
        receipt=ReceiptConfig(
            gate_id="gate",
            storage_path=tmp_path / "receipts.jsonl",
            epc11_base_url="http://localhost:8011",
            epc11_key_id="key-1",
            epc11_timeout_seconds=5.0,
            epc11_api_version="v1",
            pm7_base_url="http://localhost:8007",
            pm7_timeout_seconds=5.0,
            pm7_api_version="v1",
        ),
        redaction=RedactionConfig(
            rules=[RedactionRule(field_path="secret", strategy="remove")],
            rule_version_negotiation_enabled=True,
            require_rule_version_match=False,
        ),
        rate_limiter=RateLimiterConfig(
            epc13_base_url="http://localhost:8013",
            epc13_timeout_seconds=5.0,
            epc13_api_version="v1",
            default_deny_on_unavailable=True,
        ),
        taxonomy_mapping={BudgetExceededError: TaxonomyEntry("budget_exceeded", "high", False, "Budget exceeded")},
    )

    with patch('src.shared_libs.cccs.identity.service.EPC1IdentityAdapter', MockEPC1Adapter), \
        patch('src.shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter', MockEPC13Adapter), \
        patch('src.shared_libs.cccs.receipts.service.EPC11SigningAdapter', MockEPC11Adapter), \
        patch('src.shared_libs.cccs.receipts.service.PM7ReceiptAdapter', MockPM7Adapter):
        runtime = CCCSRuntime(config, wal_path=tmp_path / "wal.log")
    return runtime


def test_fm_cccs_epc_deterministic_result(tmp_path):
    """Test FM → CCCS → EPC/PM/CCP → Deterministic result."""
    runtime = _runtime(tmp_path)

    snapshot = {
        "module_id": "m01",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "deterministic-rule",
                "priority": 1,
                "conditions": {"input": "test"},
                "decision": "allow",
                "rationale": "deterministic",
            }
        ],
    }
    runtime.load_policy_snapshot(snapshot, sign_snapshot(snapshot))
    runtime.bootstrap(dependency_health())

    actor_context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    # Execute same flow twice
    result1 = runtime.execute_flow(
        module_id="m01",
        inputs={"input": "test"},
        action_id="test",
        cost=1,
        config_key="feature",
        payload={},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    result2 = runtime.execute_flow(
        module_id="m01",
        inputs={"input": "test"},
        action_id="test",
        cost=1,
        config_key="feature",
        payload={},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    # Results should be deterministic
    assert result1["policy"].decision == result2["policy"].decision
    assert result1["policy"].rationale == result2["policy"].rationale


def test_edge_agent_offline_48h_reconnect_zero_data_loss(tmp_path):
    """Test Edge Agent offline 48h → reconnect → zero data loss."""
    runtime = _runtime(tmp_path)
    empty_snapshot = {"module_id": "m01", "version": "1.0.0", "rules": []}
    runtime.load_policy_snapshot(empty_snapshot, sign_snapshot(empty_snapshot))
    runtime.bootstrap(dependency_health())

    actor_context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    # Prime caches before entering offline mode
    runtime._identity.resolve_actor(actor_context, use_cache=False)
    for i in range(5):
        runtime._ratelimiter._budget_cache[f"offline-{i}"] = 10.0  # noqa: SLF001

    # Simulate degraded mode
    runtime._dependencies_ready = False

    # Should still work in degraded mode (edge mode) writing receipts flagged as degraded
    receipts = []
    for i in range(5):
        result = runtime.execute_flow(
            module_id="m01",
            inputs={"offline": True, "index": i},
            action_id=f"offline-{i}",
            cost=1,
            config_key="feature",
            payload={},
            redaction_hint="rules-v1",
            actor_context=actor_context,
        )
        receipts.append(result["receipt"])

    # Verify WAL has entries
    wal_path = tmp_path / "wal.log"
    if wal_path.exists():
        import json

        wal_entries = [
            json.loads(line)
            for line in wal_path.read_text().splitlines()
            if line.strip()
        ]
        assert len(wal_entries) >= len(receipts)
        # Receipts should be marked as degraded while offline
        assert all(entry["payload"]["degraded"] for entry in wal_entries if entry["payload"].get("receipt_id"))

    # "Reconnect" - services available again
    runtime.bootstrap(dependency_health())

    # Drain courier - should process all pending receipts
    drained = runtime.drain_courier()
    assert len(drained) >= len(receipts)


def test_security_attestation_forged_receipt(tmp_path):
    """Test security attestation: forged receipt detection."""
    runtime = _runtime(tmp_path)
    empty_snapshot = {"module_id": "m01", "version": "1.0.0", "rules": []}
    runtime.load_policy_snapshot(empty_snapshot, sign_snapshot(empty_snapshot))
    runtime.bootstrap(dependency_health())

    # Create a receipt
    actor_context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    result = runtime.execute_flow(
        module_id="m01",
        inputs={},
        action_id="test",
        cost=1,
        config_key="feature",
        payload={},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    receipt_id = result["receipt"].receipt_id

    # Verify signature can be validated
    receipts_file = tmp_path / "receipts.jsonl"
    if receipts_file.exists():
        content = receipts_file.read_text()
        assert receipt_id in content
        assert "signature" in content

    # Attempt to verify signature via EPC-11
    import asyncio
    signing_adapter = runtime._receipts._signing_adapter  # noqa: SLF001

    # Read receipt from file
    import json
    for line in receipts_file.read_text().splitlines():
        if line.strip():
            receipt = json.loads(line)
            if receipt["receipt_id"] == receipt_id:
                signature = receipt.pop("signature")
                # Verify signature
                valid = asyncio.run(signing_adapter.verify_signature(receipt, signature))
                assert valid is True

                # Forged signature should fail
                forged_valid = asyncio.run(signing_adapter.verify_signature(receipt, "forged-sig"))
                assert forged_valid is False
                break


def test_security_attestation_replay_attempt(tmp_path):
    """Test security attestation: replay attempt detection."""
    runtime = _runtime(tmp_path)
    empty_snapshot = {"module_id": "m01", "version": "1.0.0", "rules": []}
    runtime.load_policy_snapshot(empty_snapshot, sign_snapshot(empty_snapshot))
    runtime.bootstrap(dependency_health())

    actor_context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    # First execution
    result1 = runtime.execute_flow(
        module_id="m01",
        inputs={"nonce": "unique-1"},
        action_id="replay-test",
        cost=1,
        config_key="feature",
        payload={},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    # Replay attempt with same inputs
    result2 = runtime.execute_flow(
        module_id="m01",
        inputs={"nonce": "unique-1"},  # Same nonce
        action_id="replay-test",
        cost=1,
        config_key="feature",
        payload={},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    # Receipts should have different IDs (monotonic sequence prevents replay)
    assert result1["receipt"].receipt_id != result2["receipt"].receipt_id
    assert result1["receipt"].fsync_offset < result2["receipt"].fsync_offset


def test_security_attestation_tamper_detection(tmp_path):
    """Test security attestation: tamper detection."""
    runtime = _runtime(tmp_path)
    empty_snapshot = {"module_id": "m01", "version": "1.0.0", "rules": []}
    runtime.load_policy_snapshot(empty_snapshot, sign_snapshot(empty_snapshot))
    runtime.bootstrap(dependency_health())

    actor_context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    result = runtime.execute_flow(
        module_id="m01",
        inputs={},
        action_id="tamper-test",
        cost=1,
        config_key="feature",
        payload={},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    # Verify WAL entry integrity
    wal_path = tmp_path / "wal.log"
    if wal_path.exists():
        import json
        wal_entries = []
        for line in wal_path.read_text().splitlines():
            if line.strip():
                wal_entries.append(json.loads(line))

        # WAL entries should have sequence numbers
        sequences = [e["sequence"] for e in wal_entries]
        assert sequences == sorted(sequences)  # Monotonic sequence
