from __future__ import annotations
"""
Unit tests for adapter registry.

What: Test adapter registration, retrieval, capability querying
Why: Ensure adapter registry works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.services.adapter_registry import AdapterRegistry, get_adapter_registry
from integration_adapters.adapters.base import BaseAdapter
from integration_adapters.adapters.github.adapter import GitHubAdapter

class TestAdapterRegistry:
    """Test AdapterRegistry."""

    def test_register_adapter(self):
        """Test registering an adapter."""
        registry = AdapterRegistry()
        registry.register_adapter("github", GitHubAdapter)

        assert registry.is_registered("github") is True
        assert registry.get_adapter_class("github") == GitHubAdapter

    def test_register_invalid_adapter(self):
        """Test registering invalid adapter raises error."""
        registry = AdapterRegistry()

        class NotAnAdapter:
            pass

        with pytest.raises(ValueError, match="must inherit from BaseAdapter"):
            registry.register_adapter("invalid", NotAnAdapter)

    def test_get_adapter_creates_instance(self):
        """Test getting adapter creates new instance."""
        registry = AdapterRegistry()
        registry.register_adapter("github", GitHubAdapter)

        connection_id = uuid4()
        adapter = registry.get_adapter("github", connection_id, "tenant-123")

        assert adapter is not None
        assert isinstance(adapter, GitHubAdapter)
        assert adapter.get_connection_id() == connection_id

    def test_get_adapter_returns_existing_instance(self):
        """Test getting adapter returns existing instance."""
        registry = AdapterRegistry()
        registry.register_adapter("github", GitHubAdapter)

        connection_id = uuid4()
        adapter1 = registry.get_adapter("github", connection_id, "tenant-123")
        adapter2 = registry.get_adapter("github", connection_id, "tenant-123")

        assert adapter1 is adapter2

    def test_get_adapter_returns_none_for_unregistered(self):
        """Test getting unregistered adapter returns None."""
        registry = AdapterRegistry()
        adapter = registry.get_adapter("unknown", uuid4(), "tenant-123")
        assert adapter is None

    def test_list_providers(self):
        """Test listing registered providers."""
        registry = AdapterRegistry()
        registry.register_adapter("github", GitHubAdapter)
        registry.register_adapter("gitlab", GitHubAdapter)  # Using GitHub as placeholder

        providers = registry.list_providers()
        assert "github" in providers
        assert "gitlab" in providers
        assert len(providers) == 2

    def test_remove_adapter_instance(self):
        """Test removing adapter instance."""
        registry = AdapterRegistry()
        registry.register_adapter("github", GitHubAdapter)

        connection_id = uuid4()
        registry.get_adapter("github", connection_id, "tenant-123")

        removed = registry.remove_adapter_instance("github", connection_id)
        assert removed is True

        removed_again = registry.remove_adapter_instance("github", connection_id)
        assert removed_again is False

    def test_get_global_registry(self):
        """Test getting global registry instance."""
        registry1 = get_adapter_registry()
        registry2 = get_adapter_registry()

        assert registry1 is registry2

