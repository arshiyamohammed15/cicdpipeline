"""
Security tests for ZeroUI Observability Layer Phase 0.

Tests security aspects: redaction enforcement, deny patterns, field blocking.
"""

import json
import unittest
from pathlib import Path

from ..privacy.redaction_enforcer import RedactionEnforcer

# Fixtures directory
_FIXTURES_DIR = Path(__file__).parent.parent / "privacy" / "tests" / "fixtures"


class TestSecurity(unittest.TestCase):
    """Security tests for redaction enforcement."""

    def setUp(self):
        """Set up redaction enforcer."""
        self.enforcer = RedactionEnforcer(use_cccs=False)

    def test_api_keys_blocked(self):
        """Test API keys are blocked."""
        payload = {
            "error_class": "security",
            "api_key": "REDACTED_KEY_PLACEHOLDER",
            "apikey": "REDACTED_KEY_PLACEHOLDER_ALT"
        }
        result = self.enforcer.enforce(payload)
        self.assertNotIn("api_key", result.redacted_payload)
        self.assertNotIn("apikey", result.redacted_payload)

    def test_passwords_blocked(self):
        """Test passwords are blocked."""
        payload = {
            "error_class": "security",
            "password": "secret123",
            "passwd": "admin123",
            "pwd": "test123"
        }
        result = self.enforcer.enforce(payload)
        self.assertNotIn("password", result.redacted_payload)
        self.assertNotIn("passwd", result.redacted_payload)
        self.assertNotIn("pwd", result.redacted_payload)

    def test_tokens_blocked(self):
        """Test tokens are blocked."""
        payload = {
            "error_class": "security",
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "refresh_token": "refresh_token_1234567890"
        }
        result = self.enforcer.enforce(payload)
        self.assertNotIn("access_token", result.redacted_payload)
        self.assertNotIn("refresh_token", result.redacted_payload)

    def test_raw_content_blocked(self):
        """Test raw content fields are blocked."""
        payload = {
            "error_class": "architecture",
            "raw_input": "user@example.com",
            "raw_output": "Processing complete",
            "raw_message": "Error occurred",
            "raw_code": "def process(): pass"
        }
        result = self.enforcer.enforce(payload)
        self.assertNotIn("raw_input", result.redacted_payload)
        self.assertNotIn("raw_output", result.redacted_payload)
        self.assertNotIn("raw_message", result.redacted_payload)
        self.assertNotIn("raw_code", result.redacted_payload)

    def test_pii_patterns_detected(self):
        """Test PII patterns are detected in content."""
        payload = {
            "error_class": "data",
            "message": "User email: user@example.com",
            "data": "SSN: 123-45-6789"
        }
        result = self.enforcer.enforce(payload)
        # PII patterns should trigger redaction
        self.assertTrue(result.redaction_applied)

    def test_secret_patterns_detected(self):
        """Test secret patterns are detected in content."""
        payload = {
            "error_class": "security",
            "message": "API key: REDACTED_KEY_PLACEHOLDER",
            "config": "password=secret123"
        }
        result = self.enforcer.enforce(payload)
        # Secret patterns should trigger redaction
        self.assertTrue(result.redaction_applied)

    def test_redaction_does_not_leak_secrets(self):
        """Test redaction does not leak secrets in redacted payload."""
        payload = {
            "error_class": "security",
            "api_key": "REDACTED_KEY_PLACEHOLDER",
            "password": "secret123",
            "message": "API key validation failed: REDACTED_KEY_PLACEHOLDER"
        }
        result = self.enforcer.enforce(payload)
        redacted_str = json.dumps(result.redacted_payload)
        # Verify secrets are not in redacted payload
        self.assertNotIn("REDACTED_KEY_PLACEHOLDER", redacted_str)
        self.assertNotIn("secret123", redacted_str)

    def test_fingerprints_do_not_contain_secrets(self):
        """Test fingerprints computed after redaction don't contain secrets."""
        payload = {
            "error_class": "security",
            "message": "API key: REDACTED_KEY_PLACEHOLDER"
        }
        result = self.enforcer.enforce(payload, compute_fingerprints=True)
        # Fingerprints should not contain raw secrets
        for fingerprint in result.fingerprints.values():
            self.assertNotIn("REDACTED_KEY_PLACEHOLDER", fingerprint)


if __name__ == "__main__":
    unittest.main()
