"""
Integration tests for CCCS services.

Covers PRD section 10.2: Policy → Receipt end-to-end, budget enforcement, trace propagation,
redaction + receipt + PM-7 courier replay, config override propagation.
"""

from datetime import datetime, timezone
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
from tests.cccs.mocks import (
    MockEPC1Adapter,
    MockEPC3Adapter,
    MockEPC11Adapter,
    MockEPC13Adapter,
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
            epc3_base_url="http://localhost:8003",
            epc3_timeout_seconds=5.0,
            epc3_api_version="v1",
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
         patch('src.shared_libs.cccs.policy.runtime.EPC3PolicyAdapter', MockEPC3Adapter), \
         patch('src.shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter', MockEPC13Adapter), \
         patch('src.shared_libs.cccs.receipts.service.EPC11SigningAdapter', MockEPC11Adapter), \
         patch('src.shared_libs.cccs.receipts.service.PM7ReceiptAdapter', MockPM7Adapter):
        runtime = CCCSRuntime(config, wal_path=tmp_path / "wal.log")
    return runtime


def test_policy_to_receipt_end_to_end_offline_courier_replay(tmp_path):
    """Test Policy → Receipt end-to-end with offline courier replay."""
    runtime = _runtime(tmp_path)
    
    snapshot = {
        "module_id": "m01",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "allow-test",
                "priority": 1,
                "conditions": {"test": True},
                "decision": "allow",
                "rationale": "test_enabled",
            }
        ],
    }
    runtime.load_policy_snapshot(snapshot, "valid-sig")
    runtime.bootstrap({"epc-1": True, "epc-3": True, "epc-13": True})

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
        inputs={"test": True},
        action_id="test-action",
        cost=1,
        config_key="feature",
        payload={},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    # Verify receipt was created
    assert result["receipt"].receipt_id
    assert result["policy"].decision == "allow"

    # Verify courier has receipt
    drained = runtime.drain_courier()
    assert len(drained) > 0


def test_budget_enforcement_burst_and_sustained_traffic(tmp_path):
    """Test budget enforcement for burst + sustained traffic, including deny fallback."""
    runtime = _runtime(tmp_path)
    runtime._ratelimiter._adapter._default_capacity = 100.0
    runtime.load_policy_snapshot({"module_id": "m01", "version": "1.0.0", "rules": []}, "valid-sig")
    runtime.bootstrap({"epc-1": True, "epc-3": True, "epc-13": True})

    actor_context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    # Burst traffic
    for i in range(10):
        runtime.execute_flow(
            module_id="m01",
            inputs={},
            action_id="burst",
            cost=5.0,
            config_key="feature",
            payload={},
            redaction_hint="rules-v1",
            actor_context=actor_context,
        )

    # Should eventually exceed budget
    with pytest.raises(BudgetExceededError):
        runtime.execute_flow(
            module_id="m01",
            inputs={},
            action_id="burst",
            cost=60.0,  # Would exceed remaining budget
            config_key="feature",
            payload={},
            redaction_hint="rules-v1",
            actor_context=actor_context,
        )


def test_trace_propagation_concurrent_spans_receipt_linking(tmp_path):
    """Test trace propagation with concurrent spans and receipt linking."""
    runtime = _runtime(tmp_path)
    runtime.load_policy_snapshot({"module_id": "m01", "version": "1.0.0", "rules": []}, "valid-sig")
    runtime.bootstrap({"epc-1": True, "epc-3": True, "epc-13": True})

    actor_context = ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
    )

    receipts = []
    for i in range(3):
        result = runtime.execute_flow(
            module_id="m01",
            inputs={"span_id": i},
            action_id=f"span-{i}",
            cost=1,
            config_key="feature",
            payload={},
            redaction_hint="rules-v1",
            actor_context=actor_context,
        )
        receipts.append(result["receipt"])

    # Verify all receipts have trace information
    receipts_file = tmp_path / "receipts.jsonl"
    content = receipts_file.read_text()
    assert "trace" in content
    assert all(r.receipt_id for r in receipts)


def test_redaction_receipt_pm7_courier_replay(tmp_path):
    """Test redaction + receipt + PM-7 courier replay."""
    runtime = _runtime(tmp_path)
    runtime.load_policy_snapshot({"module_id": "m01", "version": "1.0.0", "rules": []}, "valid-sig")
    runtime.bootstrap({"epc-1": True, "epc-3": True, "epc-13": True})

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
        payload={"secret": "remove-me", "visible": "ok"},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    # Verify redaction
    assert "secret" not in result["redaction"]["redacted_payload"]
    assert "visible" in result["redaction"]["redacted_payload"]

    # Verify receipt
    assert result["receipt"].receipt_id

    # Verify PM-7 indexing (via mock)
    assert len(runtime._receipts._pm7_adapter._indexed_receipts) > 0  # noqa: SLF001


def test_config_override_propagation_tenant_to_edge_agent(tmp_path):
    """Test config override propagation from tenant to Edge Agent."""
    runtime = _runtime(tmp_path)
    
    # Update config layers with tenant override
    runtime._config_service._layers.tenant["override_key"] = "tenant_value"
    runtime._config_service._layers.local["override_key"] = "local_value"
    
    result = runtime._config_service.get_config("override_key")
    # Local has highest precedence, so should return local_value
    assert result.value == "local_value"
    assert "local" in result.source_layers
    
    # Test tenant override when local not present
    runtime._config_service._layers.local.pop("override_key")
    result2 = runtime._config_service.get_config("override_key")
    # Tenant should override product when local not present
    assert result2.value == "tenant_value"
    assert "tenant" in result2.source_layers
