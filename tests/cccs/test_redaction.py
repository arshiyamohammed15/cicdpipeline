"""
Tests for Secure Redaction (SSDRS) with rule-version negotiation.

Covers PRD section 10.1: Redaction correctness, blocked rule scenarios.
"""

import pytest

from src.shared_libs.cccs.redaction import RedactionConfig, RedactionRule, RedactionService
from src.shared_libs.cccs.exceptions import RedactionBlockedError


def test_redaction_remove_and_mask():
    """Test redaction removes and masks fields correctly."""
    config = RedactionConfig(
        rules=[
            RedactionRule(field_path="secret", strategy="remove"),
            RedactionRule(field_path="token", strategy="mask", mask_value="***redacted***"),
        ],
        rule_version_negotiation_enabled=True,
        require_rule_version_match=False,
    )
    service = RedactionService(config)
    result = service.apply_redaction({"secret": "value", "token": "abc"})
    assert "secret" not in result["redacted_payload"]
    assert result["redacted_payload"]["token"] == "***redacted***"
    assert set(result["removed_fields"]) == {"secret", "token"}


def test_redaction_requires_rules():
    """Test redaction requires rules."""
    config = RedactionConfig(
        rules=[],
        rule_version_negotiation_enabled=True,
        require_rule_version_match=False,
    )
    with pytest.raises(RedactionBlockedError, match="No redaction rules available"):
        RedactionService(config)


def test_redaction_deep_copy_payload():
    """Test redaction deep-copies payload to prevent mutation."""
    config = RedactionConfig(
        rules=[RedactionRule(field_path="secret", strategy="remove")],
        rule_version_negotiation_enabled=True,
        require_rule_version_match=False,
    )
    service = RedactionService(config)

    original = {"secret": "value", "visible": "ok"}
    result = service.apply_redaction(original)

    # Original should not be mutated
    assert "secret" in original
    assert "secret" not in result["redacted_payload"]


def test_redaction_blocked_rule_scenarios():
    """Test redaction blocked rule scenarios."""
    config = RedactionConfig(
        rules=[RedactionRule(field_path="secret", strategy="remove", rule_version="v2")],
        rule_version_negotiation_enabled=True,
        require_rule_version_match=True,
    )
    service = RedactionService(config)

    # Request v1 but rules are v2 - per PRD §7.1: should raise redaction_blocked and halt
    with pytest.raises(RedactionBlockedError, match="No redaction rules available for version v1"):
        service.apply_redaction({"secret": "value"}, policy_hint="v1")


def test_redaction_rule_version_negotiation():
    """Test redaction rule version negotiation."""
    config = RedactionConfig(
        rules=[
            RedactionRule(field_path="secret", strategy="remove", rule_version="v1"),
            RedactionRule(field_path="token", strategy="mask", rule_version="v2"),
        ],
        rule_version_negotiation_enabled=True,
        require_rule_version_match=True,
    )
    service = RedactionService(config)

    # v1 rules should work
    result1 = service.apply_redaction({"secret": "value", "token": "abc"}, policy_hint="v1")
    assert "secret" not in result1["redacted_payload"]
    assert result1["rule_version"] == "v1"

    # v2 rules should work
    result2 = service.apply_redaction({"secret": "value", "token": "abc"}, policy_hint="v2")
    assert "token" in result2["redacted_payload"]  # Masked, not removed
    assert result2["rule_version"] == "v2"


def test_redaction_nested_field_paths():
    """Test redaction handles nested field paths."""
    config = RedactionConfig(
        rules=[
            RedactionRule(field_path="user.email", strategy="remove"),
            RedactionRule(field_path="user.password", strategy="mask"),
        ],
        rule_version_negotiation_enabled=True,
        require_rule_version_match=False,
    )
    service = RedactionService(config)

    payload = {
        "user": {
            "email": "test@example.com",
            "password": "secret123",
            "name": "John",
        },
        "public": "data",
    }

    result = service.apply_redaction(payload)
    assert "email" not in result["redacted_payload"]["user"]
    assert result["redacted_payload"]["user"]["password"] == "***"
    assert result["redacted_payload"]["user"]["name"] == "John"
    assert result["redacted_payload"]["public"] == "data"


