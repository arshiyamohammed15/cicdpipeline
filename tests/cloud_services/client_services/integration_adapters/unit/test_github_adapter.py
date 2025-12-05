from __future__ import annotations
"""
Unit tests for GitHub adapter.

What: Test GitHub adapter webhook processing, action execution, signature verification
Why: Ensure GitHub adapter works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
import json
import hmac
import hashlib
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.adapters.github.adapter import GitHubAdapter
from integration_adapters.adapters.github.webhook_verifier import GitHubWebhookVerifier
from integration_adapters.models import NormalisedActionCreate

class TestGitHubWebhookVerifier:
    """Test GitHub webhook signature verification."""

    def test_verify_valid_signature(self):
        """Test verifying valid signature."""
        secret = "test-secret"
        payload = b'{"test": "data"}'

        # Calculate expected signature
        expected_hash = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected_hash}"

        is_valid = GitHubWebhookVerifier.verify_signature(
            payload, signature, secret
        )
        assert is_valid is True

    def test_verify_invalid_signature(self):
        """Test verifying invalid signature."""
        secret = "test-secret"
        payload = b'{"test": "data"}'
        signature = "sha256=invalid-hash"

        is_valid = GitHubWebhookVerifier.verify_signature(
            payload, signature, secret
        )
        assert is_valid is False

    def test_verify_missing_signature(self):
        """Test verifying missing signature."""
        secret = "test-secret"
        payload = b'{"test": "data"}'

        is_valid = GitHubWebhookVerifier.verify_signature(
            payload, "", secret
        )
        assert is_valid is False

    def test_extract_signature_from_headers(self):
        """Test extracting signature from headers."""
        headers = {
            "X-Hub-Signature-256": "sha256=abc123",
        }

        signature = GitHubWebhookVerifier.extract_signature(headers)
        assert signature == "sha256=abc123"

        headers_lower = {
            "x-hub-signature-256": "sha256=def456",
        }

        signature = GitHubWebhookVerifier.extract_signature(headers_lower)
        assert signature == "sha256=def456"

class TestGitHubAdapter:
    """Test GitHubAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = GitHubAdapter(
            "github",
            uuid4(),
            "tenant-123",
            api_token="token-123",
            webhook_secret="secret-123",
        )
        assert adapter.provider_id == "github"
        assert adapter.api_token == "token-123"
        assert adapter.webhook_secret == "secret-123"

    def test_process_webhook_valid_signature(self):
        """Test processing webhook with valid signature."""
        secret = "test-secret"
        payload = {"action": "opened", "pull_request": {"number": 123}}
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        # Calculate signature
        signature_hash = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={signature_hash}",
        }

        adapter = GitHubAdapter(
            "github",
            uuid4(),
            "tenant-123",
            webhook_secret=secret,
        )

        result = adapter.process_webhook(payload, headers)
        assert result["event_type"] == "pull_request"
        assert result["payload"] == payload

    def test_process_webhook_invalid_signature(self):
        """Test processing webhook with invalid signature."""
        payload = {"test": "data"}
        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalid",
        }

        adapter = GitHubAdapter(
            "github",
            uuid4(),
            "tenant-123",
            webhook_secret="correct-secret",
        )

        with pytest.raises(ValueError, match="Invalid webhook signature"):
            adapter.process_webhook(payload, headers)

    def test_process_webhook_missing_event_header(self):
        """Test processing webhook without event header."""
        payload = {"test": "data"}
        headers = {}

        adapter = GitHubAdapter("github", uuid4(), "tenant-123")

        with pytest.raises(ValueError, match="Missing X-GitHub-Event header"):
            adapter.process_webhook(payload, headers)

    def test_get_capabilities(self):
        """Test getting adapter capabilities."""
        adapter = GitHubAdapter("github", uuid4(), "tenant-123")
        capabilities = adapter.get_capabilities()

        assert capabilities["webhook_supported"] is True
        assert capabilities["polling_supported"] is False
        assert capabilities["outbound_actions_supported"] is True

    def test_get_default_capabilities(self):
        """Test getting default capabilities."""
        capabilities = GitHubAdapter.get_default_capabilities()
        assert capabilities["webhook_supported"] is True
        assert capabilities["polling_supported"] is False
        assert capabilities["outbound_actions_supported"] is True

