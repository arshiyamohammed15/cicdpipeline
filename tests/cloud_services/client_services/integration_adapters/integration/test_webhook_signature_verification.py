from __future__ import annotations
"""
Integration test: Webhook Signature Verification (UT-IA-01).

What: Test webhook signature verification for all providers
Why: Ensure webhook authenticity
Coverage Target: All providers
"""

# Imports handled by conftest.py

import pytest
import json
import hmac
import hashlib

# Module setup handled by root conftest.py

from integration_adapters.adapters.github.webhook_verifier import GitHubWebhookVerifier

class TestWebhookSignatureVerification:
    """Test webhook signature verification."""

    def test_github_signature_verification_valid(self):
        """Test GitHub signature verification with valid signature."""
        secret = "test-secret"
        payload = {"action": "opened", "pull_request": {"number": 123}}
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        # Calculate signature
        signature_hash = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={signature_hash}"

        is_valid = GitHubWebhookVerifier.verify_signature(
            payload_bytes, signature, secret
        )
        assert is_valid is True

    def test_github_signature_verification_invalid(self):
        """Test GitHub signature verification with invalid signature."""
        secret = "test-secret"
        payload = {"test": "data"}
        payload_bytes = json.dumps(payload).encode("utf-8")
        signature = "sha256=invalid-hash"

        is_valid = GitHubWebhookVerifier.verify_signature(
            payload_bytes, signature, secret
        )
        assert is_valid is False

    def test_github_signature_verification_wrong_secret(self):
        """Test GitHub signature verification with wrong secret."""
        correct_secret = "correct-secret"
        wrong_secret = "wrong-secret"
        payload = {"test": "data"}
        payload_bytes = json.dumps(payload).encode("utf-8")

        # Calculate signature with correct secret
        signature_hash = hmac.new(
            correct_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={signature_hash}"

        # Verify with wrong secret
        is_valid = GitHubWebhookVerifier.verify_signature(
            payload_bytes, signature, wrong_secret
        )
        assert is_valid is False

