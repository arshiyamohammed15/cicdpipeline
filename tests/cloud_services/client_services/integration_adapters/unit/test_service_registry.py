from __future__ import annotations
"""
Unit tests for service registry.

What: Test service registration and retrieval
Why: Ensure service registry works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest

# Module setup handled by root conftest.py

from integration_adapters.service_registry import ServiceRegistry, get_service_registry

class TestServiceRegistry:
    """Test ServiceRegistry."""

    def test_register_service(self):
        """Test registering a service."""
        registry = ServiceRegistry()
        service = object()

        registry.register("test_service", service)
        assert registry.has("test_service") is True
        assert registry.get("test_service") is service

    def test_get_unregistered_service(self):
        """Test getting unregistered service returns None."""
        registry = ServiceRegistry()
        service = registry.get("unknown")
        assert service is None

    def test_has_service(self):
        """Test checking if service is registered."""
        registry = ServiceRegistry()
        service = object()

        assert registry.has("test") is False
        registry.register("test", service)
        assert registry.has("test") is True

    def test_get_global_registry(self):
        """Test getting global service registry."""
        registry1 = get_service_registry()
        registry2 = get_service_registry()

        assert registry1 is registry2

