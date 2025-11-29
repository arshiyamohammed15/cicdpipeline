"""
Unit tests for SignalEnvelope mapping.

What: Test provider event → SignalEnvelope transformation per PRD Section 10.1
Why: Ensure correct mapping to canonical format
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from services.signal_mapper import SignalMapper


class TestSignalMapper:
    """Test SignalEnvelope mapping."""

    def test_map_github_pr_event(self):
        """Test mapping GitHub PR opened event to SignalEnvelope."""
        mapper = SignalMapper()
        
        provider_event = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "state": "open",
                "head": {
                    "ref": "feature-branch",
                },
            },
            "repository": {
                "full_name": "org/repo",
            },
            "id": "event-123",
        }
        
        signal = mapper.map_provider_event_to_signal_envelope(
            provider_id="github",
            connection_id="connection-123",
            tenant_id="tenant-123",
            provider_event=provider_event,
            provider_event_type="pull_request.opened",
            occurred_at=datetime.utcnow(),
            correlation_id="event-123",
        )
        
        assert signal.provider_id == "github"  # Check producer_id
        assert signal.tenant_id == "tenant-123"
        assert signal.signal_type == "pr_opened"
        assert signal.producer_id == "connection-123"
        assert signal.correlation_id == "event-123"
        assert signal.resource is not None
        assert signal.resource.repository == "org/repo"
        assert signal.resource.branch == "feature-branch"
        assert signal.resource.pr_id == 123
        assert "provider_metadata" in signal.payload
        assert signal.payload["provider_metadata"]["provider_id"] == "github"
        assert signal.payload["pr_number"] == 123
        assert signal.payload["title"] == "Test PR"

    def test_map_jira_issue_event(self):
        """Test mapping Jira issue created event to SignalEnvelope."""
        mapper = SignalMapper()
        
        provider_event = {
            "issue": {
                "key": "PROJ-123",
                "fields": {
                    "summary": "Test Issue",
                },
            },
            "id": "jira-event-456",
        }
        
        signal = mapper.map_provider_event_to_signal_envelope(
            provider_id="jira",
            connection_id="connection-456",
            tenant_id="tenant-123",
            provider_event=provider_event,
            provider_event_type="issue.created",
            occurred_at=datetime.utcnow(),
        )
        
        assert signal.signal_type == "issue_created"
        assert signal.payload["issue_key"] == "PROJ-123"
        assert signal.payload["summary"] == "Test Issue"
        assert "canonical_keys" in signal.payload
        assert signal.payload["canonical_keys"]["issue_key"] == "PROJ-123"

    def test_map_slack_message_event(self):
        """Test mapping Slack message event to SignalEnvelope."""
        mapper = SignalMapper()
        
        provider_event = {
            "channel": {
                "id": "C123456",
            },
            "text": "Hello world",
            "ts": "1234567890.123456",
        }
        
        signal = mapper.map_provider_event_to_signal_envelope(
            provider_id="slack",
            connection_id="connection-789",
            tenant_id="tenant-123",
            provider_event=provider_event,
            provider_event_type="message.posted",
            occurred_at=datetime.utcnow(),
        )
        
        assert signal.signal_type == "chat_message"
        assert "canonical_keys" in signal.payload
        assert signal.payload["canonical_keys"]["channel_id"] == "C123456"

    def test_map_event_with_missing_fields(self):
        """Test mapping event with missing optional fields."""
        mapper = SignalMapper()
        
        provider_event = {
            "id": "event-789",
        }
        
        signal = mapper.map_provider_event_to_signal_envelope(
            provider_id="github",
            connection_id="connection-123",
            tenant_id="tenant-123",
            provider_event=provider_event,
            provider_event_type="unknown.event",
            occurred_at=datetime.utcnow(),
        )
        
        assert signal.signal_id is not None
        assert signal.tenant_id == "tenant-123"
        assert signal.producer_id == "connection-123"
        assert "provider_metadata" in signal.payload

    def test_event_type_mapping(self):
        """Test event type to canonical signal_type mapping."""
        mapper = SignalMapper()
        
        test_cases = [
            ("pull_request.opened", "pr_opened"),
            ("pull_request.closed", "pr_closed"),
            ("issues.opened", "issue_created"),
            ("message.posted", "chat_message"),
            ("unknown.event", "unknown_event"),
        ]
        
        for provider_type, expected_canonical in test_cases:
            canonical = mapper._map_event_type_to_canonical("github", provider_type)
            assert canonical == expected_canonical

