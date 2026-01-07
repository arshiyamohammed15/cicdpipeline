from __future__ import annotations
"""
Unit tests for Pydantic models.

What: Test all Pydantic model validation, serialization
Why: Ensure models validate correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from datetime import datetime
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.models import (
    IntegrationProviderCreate,
    IntegrationProviderResponse,
    IntegrationConnectionCreate,
    IntegrationConnectionUpdate,
    IntegrationConnectionResponse,
    NormalisedActionCreate,
    NormalisedActionResponse,
    ProviderCategory,
    ProviderStatus,
    ConnectionStatus,
    ActionStatus,
)

@pytest.mark.unit
class TestIntegrationProviderModels:
    """Test IntegrationProvider models."""

    @pytest.mark.unit
    def test_provider_create_valid(self):
        """Test creating valid provider."""
        provider = IntegrationProviderCreate(
            provider_id="github",
            category=ProviderCategory.SCM,
            name="GitHub",
            status=ProviderStatus.GA,
            capabilities={"webhook_supported": True},
            api_version="v3",
        )
        assert provider.provider_id == "github"
        assert provider.category == ProviderCategory.SCM
        assert provider.status == ProviderStatus.GA

    @pytest.mark.unit
    def test_provider_create_defaults(self):
        """Test provider creation with defaults."""
        provider = IntegrationProviderCreate(
            provider_id="github",
            category=ProviderCategory.SCM,
            name="GitHub",
        )
        assert provider.status == ProviderStatus.ALPHA
        assert provider.capabilities == {}

    @pytest.mark.unit
    def test_provider_create_invalid_category(self):
        """Test provider creation with invalid category."""
        with pytest.raises(Exception):  # Pydantic validation error
            IntegrationProviderCreate(
                provider_id="github",
                category="invalid",  # type: ignore
                name="GitHub",
            )

@pytest.mark.unit
class TestIntegrationConnectionModels:
    """Test IntegrationConnection models."""

    @pytest.mark.unit
    def test_connection_create_valid(self):
        """Test creating valid connection."""
        connection = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Test Connection",
            auth_ref="kms-secret-123",
            enabled_capabilities={"webhook": True},
            metadata_tags={"org": "test-org"},
        )
        assert connection.provider_id == "github"
        assert connection.display_name == "Test Connection"
        assert connection.auth_ref == "kms-secret-123"

    @pytest.mark.unit
    def test_connection_update_partial(self):
        """Test partial connection update."""
        update = IntegrationConnectionUpdate(
            display_name="Updated Name",
        )
        assert update.display_name == "Updated Name"
        assert update.status is None
        assert update.enabled_capabilities is None

    @pytest.mark.unit
    def test_connection_update_all_fields(self):
        """Test connection update with all fields."""
        update = IntegrationConnectionUpdate(
            display_name="Updated Name",
            status=ConnectionStatus.ACTIVE,
            enabled_capabilities={"webhook": True, "polling": False},
            metadata_tags={"org": "new-org"},
        )
        assert update.display_name == "Updated Name"
        assert update.status == ConnectionStatus.ACTIVE
        assert update.enabled_capabilities == {"webhook": True, "polling": False}

@pytest.mark.unit
class TestNormalisedActionModels:
    """Test NormalisedAction models."""

    @pytest.mark.unit
    def test_action_create_valid(self):
        """Test creating valid action."""
        action = NormalisedActionCreate(
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="comment_on_pr",
            target={"repository": "org/repo", "pr_number": 123},
            payload={"body": "Test comment"},
            idempotency_key="idempotency-123",
            correlation_id="correlation-456",
        )
        assert action.provider_id == "github"
        assert action.canonical_type == "comment_on_pr"
        assert action.idempotency_key == "idempotency-123"
        assert action.correlation_id == "correlation-456"

    @pytest.mark.unit
    def test_action_create_required_fields(self):
        """Test action creation requires all required fields."""
        with pytest.raises(Exception):  # Pydantic validation error
            NormalisedActionCreate(
                provider_id="github",
                # Missing required fields
            )

    @pytest.mark.unit
    def test_action_response_serialization(self):
        """Test action response serialization."""
        response = NormalisedActionResponse(
            action_id=uuid4(),
            tenant_id="tenant-123",
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="comment_on_pr",
            target={"repository": "org/repo"},
            payload={"comment_id": 456},
            idempotency_key="idempotency-123",
            correlation_id="correlation-456",
            status=ActionStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        assert response.status == ActionStatus.COMPLETED
        assert response.completed_at is not None

