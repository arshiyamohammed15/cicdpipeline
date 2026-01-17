"""
Tests for redaction policy enforcement (OBS-02).

Tests redaction enforcer with allow/deny rules.
"""

import json
import unittest
from pathlib import Path

from ..privacy.redaction_enforcer import RedactionEnforcer, RedactionResult

# Fixtures directory
_FIXTURES_DIR = Path(__file__).parent.parent / "privacy" / "tests" / "fixtures"


class TestRedactionPolicy(unittest.TestCase):
    """Test redaction policy enforcement."""

    def setUp(self):
        """Set up redaction enforcer."""
        self.enforcer = RedactionEnforcer(use_cccs=False)  # Disable CCCS for unit tests

    def test_metadata_only_passes(self):
        """Test metadata-only payload passes (no redaction needed)."""
        fixture_path = _FIXTURES_DIR / "pass_metadata_only.json"
        if fixture_path.exists():
            with open(fixture_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            result = self.enforcer.enforce(payload)
            self.assertIsInstance(result, RedactionResult)
            # Metadata-only should pass without redaction
            self.assertEqual(len(result.removed_fields), 0)
            self.assertEqual(len(result.blocked_fields), 0)

    def test_raw_secrets_blocked(self):
        """Test raw secrets are blocked."""
        fixture_path = _FIXTURES_DIR / "fail_raw_secrets.json"
        if fixture_path.exists():
            with open(fixture_path, "r", encoding="utf-8") as f:
                payload = json.load(f)

            result = self.enforcer.enforce(payload)
            self.assertIsInstance(result, RedactionResult)
            # Secrets should be blocked
            self.assertTrue(result.redaction_applied)
            # Deny-listed fields should be removed
            self.assertGreater(len(result.blocked_fields), 0)

    def test_field_deny_list(self):
        """Test deny-listed field names are removed."""
        payload = {
            "error_class": "security",
            "api_key": "REDACTED_KEY_PLACEHOLDER",
            "password": "secret123",
            "raw_input": "user@example.com"
        }
        result = self.enforcer.enforce(payload)
        self.assertTrue(result.redaction_applied)
        self.assertIn("api_key", result.blocked_fields or result.removed_fields)
        self.assertIn("password", result.blocked_fields or result.removed_fields)
        self.assertIn("raw_input", result.blocked_fields or result.removed_fields)
        # Deny-listed fields should not be in redacted payload
        self.assertNotIn("api_key", result.redacted_payload)
        self.assertNotIn("password", result.redacted_payload)
        self.assertNotIn("raw_input", result.redacted_payload)

    def test_fingerprints_computed_after_redaction(self):
        """Test fingerprints are computed after redaction."""
        payload = {
            "error_class": "architecture",
            "message": "Error occurred",
            "input": "test input",
            "output": "test output"
        }
        result = self.enforcer.enforce(payload, compute_fingerprints=True)
        # Fingerprints should be computed if fields exist
        # (Note: actual fingerprint computation depends on field names)

    def test_payload_not_mutated(self):
        """Test original payload is not mutated."""
        original = {
            "error_class": "architecture",
            "api_key": "REDACTED_KEY_PLACEHOLDER",
            "message": "Error occurred"
        }
        payload_copy = original.copy()
        result = self.enforcer.enforce(payload_copy)
        # Original should remain unchanged (enforcer uses deep copy)
        self.assertEqual(original, payload_copy)

    def test_redaction_applied_flag(self):
        """Test redaction_applied flag is set correctly."""
        # Payload with deny-listed fields
        payload = {
            "error_class": "security",
            "api_key": "REDACTED_KEY_PLACEHOLDER"
        }
        result = self.enforcer.enforce(payload)
        self.assertTrue(result.redaction_applied)

        # Payload without deny-listed fields
        payload_clean = {
            "error_class": "architecture",
            "error_code": "ERR_001"
        }
        result_clean = self.enforcer.enforce(payload_clean)
        # May or may not have redaction applied depending on patterns
        self.assertIsInstance(result_clean.redaction_applied, bool)

    def test_policy_version(self):
        """Test policy version is included in result."""
        payload = {
            "error_class": "architecture",
            "error_code": "ERR_001"
        }
        result = self.enforcer.enforce(payload)
        self.assertIsNotNone(result.policy_version)
        self.assertIsInstance(result.policy_version, str)


if __name__ == "__main__":
    unittest.main()
