from __future__ import annotations
"""
Unit tests for base adapter interface.

What: Test BaseAdapter abstract class and adapter interface
Why: Ensure adapter contract is enforced
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from uuid import uuid4
import sys
import types
from enum import Enum
from datetime import datetime

# Module setup handled by root conftest.py

from integration_adapters.adapters.base import BaseAdapter
from integration_adapters.models import NormalisedActionCreate

# Provide shim models module to satisfy adapter imports.
_models = types.ModuleType("models")

class ActionStatus(Enum):
    COMPLETED = "completed"

class NormalisedActionResponse:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

_models.ActionStatus = ActionStatus
_models.NormalisedActionResponse = NormalisedActionResponse
sys.modules["models"] = _models

class ConcreteAdapter(BaseAdapter):
    """Concrete adapter for testing."""

    def process_webhook(self, payload, headers):
        return {"event_type": "test", "payload": payload}

    def poll_events(self, cursor=None):
        return [], "new-cursor"

    def execute_action(self, action):
        return NormalisedActionResponse(
            action_id=uuid4(),
            tenant_id=self.tenant_id,
            provider_id=self.provider_id,
            connection_id=self.connection_id,
            canonical_type=action.canonical_type,
            target=action.target,
            payload={"status": "success"},
            idempotency_key=action.idempotency_key,
            correlation_id=action.correlation_id,
            status=ActionStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

    def verify_connection(self):
        return True

    def get_capabilities(self):
        return {
            "webhook_supported": True,
            "polling_supported": True,
            "outbound_actions_supported": True,
        }

class TestBaseAdapter:
    """Test BaseAdapter interface."""

    def test_adapter_initialization(self):
        """Test adapter initialization."""
        adapter = ConcreteAdapter("github", uuid4(), "tenant-123")
        assert adapter.provider_id == "github"
        assert adapter.tenant_id == "tenant-123"

    def test_adapter_getters(self):
        """Test adapter getter methods."""
        connection_id = uuid4()
        adapter = ConcreteAdapter("github", connection_id, "tenant-123")
        assert adapter.get_provider_id() == "github"
        assert adapter.get_connection_id() == connection_id
        assert adapter.get_tenant_id() == "tenant-123"

    def test_adapter_process_webhook(self):
        """Test webhook processing."""
        adapter = ConcreteAdapter("github", uuid4(), "tenant-123")
        result = adapter.process_webhook({"test": "data"}, {"header": "value"})
        assert result["event_type"] == "test"

    def test_adapter_poll_events(self):
        """Test event polling."""
        adapter = ConcreteAdapter("github", uuid4(), "tenant-123")
        events, cursor = adapter.poll_events("old-cursor")
        assert events == []
        assert cursor == "new-cursor"

    def test_adapter_execute_action(self):
        """Test action execution."""
        adapter = ConcreteAdapter("github", uuid4(), "tenant-123")
        action = NormalisedActionCreate(
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="test_action",
            target={},
            payload={},
            idempotency_key="key-123",
        )
        result = adapter.execute_action(action)
        assert result.status.value == "completed"
        assert result.idempotency_key == "key-123"

    def test_adapter_verify_connection(self):
        """Test connection verification."""
        adapter = ConcreteAdapter("github", uuid4(), "tenant-123")
        assert adapter.verify_connection() is True

    def test_adapter_get_capabilities(self):
        """Test capability reporting."""
        adapter = ConcreteAdapter("github", uuid4(), "tenant-123")
        capabilities = adapter.get_capabilities()
        assert capabilities["webhook_supported"] is True
        assert capabilities["polling_supported"] is True
        assert capabilities["outbound_actions_supported"] is True

    def test_abstract_adapter_cannot_instantiate(self):
        """Test that BaseAdapter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAdapter("github", uuid4(), "tenant-123")

