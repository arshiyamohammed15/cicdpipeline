"""
Tests for CCCS Runtime orchestration with adapter-based implementations.

Covers PRD section 10.1: End-to-end flow, dependency gating, error taxonomy.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.shared_libs.cccs import CCCSConfig, CCCSRuntime
from src.shared_libs.cccs.errors.taxonomy import TaxonomyEntry
from src.shared_libs.cccs.exceptions import BudgetExceededError, PolicyUnavailableError, VersionMismatchError
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


def _runtime(tmp_path: Path, rate_config: RateLimiterConfig | None = None) -> CCCSRuntime:
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
        rate_limiter=rate_config or RateLimiterConfig(
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

        snapshot = {
            "module_id": "m01",
            "version": "1.0.0",
            "rules": [
                {
                    "rule_id": "allow-feature",
                    "priority": 1,
                    "conditions": {"feature_flag": True},
                    "decision": "allow",
                    "rationale": "feature_enabled",
                }
            ],
        }
        runtime.load_policy_snapshot(snapshot, sign_snapshot(snapshot))
    return runtime


def _actor_context():
    return ActorContext(
        tenant_id="t1",
        device_id="d1",
        session_id="s1",
        user_id="u1",
        actor_type="machine",
        runtime_clock=datetime.now(timezone.utc),
        extras={},
    )


def test_runtime_end_to_end(tmp_path):
    """Test end-to-end flow: IAPS → CFFS → PREE → RLBGS → OTCS → RGES → SSDRS → PM-7."""
    runtime = _runtime(tmp_path)
    runtime.bootstrap(dependency_health())
    runtime.negotiate_version("1.0.0")

    result = runtime.execute_flow(
        module_id="m01",
        inputs={"feature_flag": True},
        action_id="ingest",
        cost=1,
        config_key="feature",
        payload={"secret": "remove-me", "visible": "ok"},
        redaction_hint="rules-v1",
        actor_context=_actor_context(),
    )

    assert result["policy"].decision == "allow"
    assert result["config"].value is True
    assert result["redaction"]["redacted_payload"]["visible"] == "ok"
    assert "secret" not in result["redaction"]["redacted_payload"]
    # Drain courier - should have receipt, budget snapshot, and policy snapshot entries
    drained = runtime.drain_courier()
    assert len(drained) >= 1  # At least the receipt entry


def test_runtime_backend_requires_dependencies(tmp_path):
    """Test backend mode requires all dependencies."""
    runtime = _runtime(tmp_path)
    runtime._config.mode = "backend"
    with pytest.raises(PolicyUnavailableError, match="Bootstrap failed"):
        runtime.bootstrap(dependency_health(**{"epc-1": False}))


def test_runtime_edge_mode_degraded_startup(tmp_path):
    """Test edge mode allows degraded startup when dependencies unavailable."""
    runtime = _runtime(tmp_path)
    runtime._config.mode = "edge"
    runtime.bootstrap(dependency_health(**{"epc-1": False}))
    assert runtime._dependencies_ready is False


def test_version_negotiation_failure(tmp_path):
    """Test version negotiation failure."""
    runtime = _runtime(tmp_path)
    with pytest.raises(VersionMismatchError):
        runtime.negotiate_version("2.0.0")


def test_budget_exceeded(tmp_path):
    """Test budget exceeded handling."""
    runtime = _runtime(tmp_path, rate_config=RateLimiterConfig(
        epc13_base_url="http://localhost:8013",
        epc13_timeout_seconds=5.0,
        epc13_api_version="v1",
        default_deny_on_unavailable=True,
    ))
    runtime.bootstrap(dependency_health())

    # Set low capacity
    runtime._ratelimiter._adapter._default_capacity = 1.0

    with pytest.raises(BudgetExceededError):
        runtime.execute_flow(
            module_id="m01",
            inputs={"feature_flag": True},
            action_id="ingest",
            cost=5,
            config_key="feature",
            payload={},
            redaction_hint="rules",
            actor_context=_actor_context(),
        )


def test_error_taxonomy_mapping(tmp_path):
    """Test error taxonomy mapping including unknown exception fallback."""
    runtime = _runtime(tmp_path)
    err = BudgetExceededError("nope")
    canonical = runtime.normalize_error(err)
    assert canonical["canonical_code"] == "budget_exceeded"
    assert canonical["retryable"] is False


def test_error_taxonomy_unknown_exception(tmp_path):
    """Test error taxonomy fallback for unknown exceptions."""
    runtime = _runtime(tmp_path)
    err = ValueError("unknown error")
    canonical = runtime.normalize_error(err)
    # Should have some canonical mapping or fallback
    assert "canonical_code" in canonical


def test_dependency_health_checks(tmp_path):
    """Test dependency health checks during bootstrap."""
    runtime = _runtime(tmp_path)

    # Bootstrap with health checks
    runtime.bootstrap()  # No dependency_health provided, should check
    assert runtime._dependencies_ready is True


def test_wal_budget_snapshot_persistence(tmp_path):
    """Test WAL persists budget snapshots."""
    runtime = _runtime(tmp_path)
    wal = runtime._receipts._courier._wal  # noqa: SLF001

    budget_data = {"action_id": "action1", "remaining": 50.0}
    entry = wal.append_budget_snapshot(budget_data)
    assert entry.entry_type == "budget"
    assert entry.payload == budget_data


def test_wal_policy_snapshot_persistence(tmp_path):
    """Test WAL persists policy snapshots."""
    runtime = _runtime(tmp_path)
    wal = runtime._receipts._courier._wal  # noqa: SLF001

    policy_data = {"module_id": "m01", "version": "1.0.0"}
    entry = wal.append_policy_snapshot(policy_data)
    assert entry.entry_type == "policy_snapshot"
    assert entry.payload == policy_data
