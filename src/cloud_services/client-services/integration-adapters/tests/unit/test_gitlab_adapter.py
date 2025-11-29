"""
Unit tests for GitLab adapter.

What: Test GitLab adapter webhook processing, action execution
Why: Ensure GitLab adapter works correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from adapters.gitlab.adapter import GitLabAdapter


class TestGitLabAdapter:
    """Test GitLabAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = GitLabAdapter(
            "gitlab",
            uuid4(),
            "tenant-123",
            api_token="token-123",
            webhook_secret="secret-123",
        )
        assert adapter.provider_id == "gitlab"
        assert adapter.api_token == "token-123"
        assert adapter.webhook_secret == "secret-123"

    def test_process_webhook_valid_token(self):
        """Test processing webhook with valid token."""
        payload = {"object_kind": "merge_request", "object_attributes": {"id": 123}}
        headers = {
            "X-Gitlab-Event": "Merge Request Hook",
            "X-Gitlab-Token": "secret-123",
        }
        
        adapter = GitLabAdapter(
            "gitlab",
            uuid4(),
            "tenant-123",
            webhook_secret="secret-123",
        )
        
        result = adapter.process_webhook(payload, headers)
        assert result["event_type"] == "Merge Request Hook"
        assert result["payload"] == payload

    def test_process_webhook_invalid_token(self):
        """Test processing webhook with invalid token."""
        payload = {"test": "data"}
        headers = {
            "X-Gitlab-Event": "Merge Request Hook",
            "X-Gitlab-Token": "wrong-token",
        }
        
        adapter = GitLabAdapter(
            "gitlab",
            uuid4(),
            "tenant-123",
            webhook_secret="correct-secret",
        )
        
        with pytest.raises(ValueError, match="Invalid webhook token"):
            adapter.process_webhook(payload, headers)

    def test_get_capabilities(self):
        """Test getting adapter capabilities."""
        adapter = GitLabAdapter("gitlab", uuid4(), "tenant-123")
        capabilities = adapter.get_capabilities()
        
        assert capabilities["webhook_supported"] is True
        assert capabilities["polling_supported"] is False
        assert capabilities["outbound_actions_supported"] is True

