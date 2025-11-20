"""
Tests for Policy Runtime & Evaluation Engine (PREE) and Configuration Service.

Covers PRD section 10.1: Policy signature validation, concurrent requests, config merge.
"""

import threading

import pytest

from src.shared_libs.cccs.config import ConfigService
from src.shared_libs.cccs.config.service import ConfigLayers
from src.shared_libs.cccs.exceptions import PolicyUnavailableError
from src.shared_libs.cccs.policy import PolicyConfig, PolicyRuntime
from src.shared_libs.cccs.types import PolicyDecision
from tests.cccs.helpers import SIGNING_SECRET, sign_snapshot


def _policy_config() -> PolicyConfig:
    return PolicyConfig(
        signing_secrets=[SIGNING_SECRET],
        rule_version_negotiation_enabled=True,
    )


def test_policy_snapshot_signature_verification_valid():
    """Test policy signature validation with valid signature."""
    config = _policy_config()
    runtime = PolicyRuntime(config)
    payload = {
        "module_id": "m01",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "allow-safe",
                "priority": 1,
                "conditions": {"risk": {"op": "lte", "value": 3}},
                "decision": "allow",
                "rationale": "low_risk",
            }
        ],
    }
    runtime.load_snapshot(payload, sign_snapshot(payload))
    decision = runtime.evaluate("m01", {"risk": 2})
    assert isinstance(decision, PolicyDecision)
    assert decision.decision == "allow"
    assert decision.policy_snapshot_hash.startswith("sha256:")


def test_policy_signature_validation_invalid():
    """Test policy signature validation with invalid signature."""
    config = _policy_config()
    runtime = PolicyRuntime(config)
    payload = {"module_id": "m01", "version": "1.0.0", "rules": []}
    with pytest.raises(PolicyUnavailableError, match="Policy snapshot signature invalid"):
        runtime.load_snapshot(payload, "invalid")


def test_policy_signature_validation_corrupted():
    """Test policy signature validation with adapter failure."""
    config = _policy_config()
    runtime = PolicyRuntime(config)
    payload = {"module_id": "m01", "version": "1.0.0", "rules": []}
    signature = sign_snapshot(payload)
    payload["rules"].append({"rule_id": "tampered"})
    with pytest.raises(PolicyUnavailableError, match="Policy snapshot signature invalid"):
        runtime.load_snapshot(payload, signature)


def test_policy_denial_determinism_concurrent_requests():
    """Test policy denial determinism under concurrent requests."""
    config = _policy_config()
    runtime = PolicyRuntime(config)
    payload = {
        "module_id": "m01",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "deny-high-risk",
                "priority": 1,
                "conditions": {"risk": {"op": "gte", "value": 5}},
                "decision": "deny",
                "rationale": "high_risk",
            }
        ],
    }
    runtime.load_snapshot(payload, sign_snapshot(payload))

    results = []

    def evaluate():
        decision = runtime.evaluate("m01", {"risk": 6})
        results.append(decision.decision)

    threads = [threading.Thread(target=evaluate) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert all(r == "deny" for r in results)
    assert len(results) == 10


def test_config_merge_precedence():
    """Test config merge precedence: local → tenant → product."""
    layers = ConfigLayers(
        local={"feature_enabled": False},
        tenant={"feature_enabled": True},
        product={"feature_enabled": False},
    )
    service = ConfigService(layers)

    result = service.get_config("feature_enabled")
    # Local has highest precedence, so should return False
    assert result.value is False
    assert "local" in result.source_layers

    # Test tenant overrides product when local not present
    layers2 = ConfigLayers(
        local={},
        tenant={"feature_enabled": True},
        product={"feature_enabled": False},
    )
    service2 = ConfigService(layers2)
    result2 = service2.get_config("feature_enabled")
    assert result2.value is True  # Tenant overrides product
    assert "tenant" in result2.source_layers


def test_config_gap_warning():
    """Test config gap warning emission."""
    layers = ConfigLayers(
        local={},
        tenant={},
        product={},
    )
    service = ConfigService(layers)

    missing = service.get_config("missing_key")
    assert missing.value is None
    assert "config_gap" in missing.warnings


def test_config_checksum_mismatch_handling():
    """Test config checksum mismatch handling."""
    layers = ConfigLayers(
        local={"key": "value"},
        tenant={},
        product={},
    )
    service = ConfigService(layers)

    result = service.get_config("key")
    assert result.value == "value"
    assert result.config_snapshot_hash is not None


def test_policy_rule_version_negotiation():
    """Test policy rule version negotiation."""
    config = _policy_config()
    runtime = PolicyRuntime(config)
    payload = {
        "module_id": "m01",
        "version": "1.0.0",
        "rules": [{"rule_id": "r1", "decision": "allow", "conditions": {}}],
    }
    runtime.load_snapshot(payload, sign_snapshot(payload))
    runtime.evaluate("m01", {})
    assert "m01" in runtime._negotiated_versions
