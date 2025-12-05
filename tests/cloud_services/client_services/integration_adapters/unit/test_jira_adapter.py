from __future__ import annotations
"""
Unit tests for Jira adapter.

What: Test Jira adapter polling, action execution
Why: Ensure Jira adapter works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.adapters.jira.adapter import JiraAdapter

class TestJiraAdapter:
    """Test JiraAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = JiraAdapter(
            "jira",
            uuid4(),
            "tenant-123",
            api_token="token-123",
            jira_url="https://test.atlassian.net",
        )
        assert adapter.provider_id == "jira"
        assert adapter.api_token == "token-123"
        assert adapter.jira_url == "https://test.atlassian.net"

    def test_get_capabilities(self):
        """Test getting adapter capabilities."""
        adapter = JiraAdapter("jira", uuid4(), "tenant-123")
        capabilities = adapter.get_capabilities()

        assert capabilities["webhook_supported"] is False
        assert capabilities["polling_supported"] is True
        assert capabilities["outbound_actions_supported"] is True

    def test_poll_events_returns_events(self):
        """Test polling events returns events list."""
        adapter = JiraAdapter("jira", uuid4(), "tenant-123", api_token="token")

        # Mock would be needed for full test
        events, cursor = adapter.poll_events()
        assert isinstance(events, list)
        # Cursor may be None or a string
        assert cursor is None or isinstance(cursor, str)

