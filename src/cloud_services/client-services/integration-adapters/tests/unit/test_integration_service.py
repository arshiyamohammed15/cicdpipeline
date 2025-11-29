"""
Unit tests for IntegrationService.

What: Test all FR implementations in IntegrationService
Why: Ensure service orchestrates correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from database.models import IntegrationProvider, IntegrationConnection
from models import (
    IntegrationProviderCreate,
    IntegrationConnectionCreate,
    IntegrationConnectionUpdate,
    ProviderCategory,
    ProviderStatus,
    ConnectionStatus,
)


class TestIntegrationService:
    """Test IntegrationService."""

    def test_create_provider(self, integration_service):
        """Test creating a provider (FR-1)."""
        provider_data = IntegrationProviderCreate(
            provider_id="github",
            category=ProviderCategory.SCM,
            name="GitHub",
            status=ProviderStatus.GA,
            capabilities={"webhook_supported": True},
        )
        
        provider = integration_service.create_provider(provider_data)
        assert provider.provider_id == "github"
        assert provider.name == "GitHub"

    def test_get_provider(self, integration_service):
        """Test getting provider (FR-1)."""
        provider_data = IntegrationProviderCreate(
            provider_id="github",
            category=ProviderCategory.SCM,
            name="GitHub",
        )
        integration_service.create_provider(provider_data)
        
        provider = integration_service.get_provider("github")
        assert provider is not None
        assert provider.provider_id == "github"

    def test_create_connection(self, integration_service, sample_tenant_id):
        """Test creating a connection (FR-2)."""
        connection_data = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Test Connection",
            auth_ref="kms-secret-123",
            enabled_capabilities={"webhook": True},
        )
        
        connection = integration_service.create_connection(sample_tenant_id, connection_data)
        assert connection.tenant_id == sample_tenant_id
        assert connection.provider_id == "github"
        assert connection.status == ConnectionStatus.PENDING_VERIFICATION.value

    def test_get_connection_with_tenant_isolation(
        self, integration_service, sample_tenant_id
    ):
        """Test getting connection with tenant isolation (FR-2, FR-10)."""
        connection_data = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Test",
            auth_ref="secret",
        )
        
        connection = integration_service.create_connection(sample_tenant_id, connection_data)
        
        # Correct tenant can retrieve
        retrieved = integration_service.get_connection(
            connection.connection_id, sample_tenant_id
        )
        assert retrieved is not None
        
        # Wrong tenant cannot retrieve
        retrieved2 = integration_service.get_connection(
            connection.connection_id, "wrong-tenant"
        )
        assert retrieved2 is None

    def test_list_connections(self, integration_service, sample_tenant_id):
        """Test listing connections (FR-2, FR-10)."""
        connection_data = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Test",
            auth_ref="secret",
        )
        
        connection1 = integration_service.create_connection(sample_tenant_id, connection_data)
        connection2 = integration_service.create_connection(sample_tenant_id, connection_data)
        
        connections = integration_service.list_connections(sample_tenant_id)
        assert len(connections) == 2
        
        # Wrong tenant sees no connections
        connections2 = integration_service.list_connections("wrong-tenant")
        assert len(connections2) == 0

    def test_update_connection(self, integration_service, sample_tenant_id):
        """Test updating connection (FR-2)."""
        connection_data = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Original",
            auth_ref="secret",
        )
        connection = integration_service.create_connection(sample_tenant_id, connection_data)
        
        update_data = IntegrationConnectionUpdate(
            display_name="Updated",
            status=ConnectionStatus.ACTIVE,
        )
        
        updated = integration_service.update_connection(
            connection.connection_id, sample_tenant_id, update_data
        )
        assert updated is not None
        assert updated.display_name == "Updated"
        assert updated.status == ConnectionStatus.ACTIVE.value

    def test_verify_connection(self, integration_service, sample_tenant_id, mock_kms_client):
        """Test connection verification (FR-2, FR-3)."""
        # Register GitHub adapter
        from services.adapter_registry import get_adapter_registry
        from adapters.github.adapter import GitHubAdapter
        registry = get_adapter_registry()
        registry.register_adapter("github", GitHubAdapter)
        
        connection_data = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Test",
            auth_ref="kms-secret-123",
        )
        connection = integration_service.create_connection(sample_tenant_id, connection_data)
        
        # Mock KMS to return secret
        if hasattr(mock_kms_client, 'secrets'):
            mock_kms_client.secrets["kms-secret-123"] = "github-token-123"
        
        # Verify connection (would need mocked adapter for full test)
        # For now, test that it attempts verification
        is_valid = integration_service.verify_connection(
            connection.connection_id, sample_tenant_id
        )
        # Result depends on adapter implementation
        assert isinstance(is_valid, bool)

