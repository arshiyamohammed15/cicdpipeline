"""
Integration test: Normalisation for SCM Event (UT-IA-03).

What: Test SCM event normalization to SignalEnvelope
Why: Ensure correct canonical format
Coverage Target: All SCM event types
"""

from __future__ import annotations

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from services.signal_mapper import SignalMapper


class TestSCMEventNormalization:
    """Test SCM event normalization."""

    def test_github_pr_opened_normalization(self):
        """Test GitHub PR opened event normalization."""
        mapper = SignalMapper()
        
        provider_event = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "state": "open",
                "head": {"ref": "feature-branch"},
            },
            "repository": {"full_name": "org/repo"},
        }
        
        signal = mapper.map_provider_event_to_signal_envelope(
            provider_id="github",
            connection_id="connection-123",
            tenant_id="tenant-123",
            provider_event=provider_event,
            provider_event_type="pull_request.opened",
            occurred_at=datetime.utcnow(),
        )
        
        # Verify canonical format
        assert signal.signal_type == "pr_opened"
        assert signal.resource is not None
        assert signal.resource.repository == "org/repo"
        assert signal.resource.branch == "feature-branch"
        assert signal.resource.pr_id == 123
        assert signal.payload["pr_number"] == 123
        assert signal.payload["title"] == "Test PR"
        assert signal.payload["provider_metadata"]["provider_id"] == "github"

    def test_gitlab_push_normalization(self):
        """Test GitLab push event normalization."""
        mapper = SignalMapper()
        
        provider_event = {
            "ref": "refs/heads/main",
            "repository": {"full_name": "org/repo"},
            "commits": [{"id": "abc123"}],
        }
        
        signal = mapper.map_provider_event_to_signal_envelope(
            provider_id="gitlab",
            connection_id="connection-456",
            tenant_id="tenant-123",
            provider_event=provider_event,
            provider_event_type="push",
            occurred_at=datetime.utcnow(),
        )
        
        assert signal.signal_type == "push"
        assert signal.resource is not None
        assert signal.resource.repository == "org/repo"
        assert signal.resource.branch == "main"

