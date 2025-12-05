from __future__ import annotations
"""
Unit tests for database models.

What: Test all database model creation, validation, relationships
Why: Ensure models work correctly with SQLAlchemy
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from datetime import datetime
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.database.models import (
    IntegrationProvider,
    IntegrationConnection,
    WebhookRegistration,
    PollingCursor,
    AdapterEvent,
    NormalisedAction,
)

class TestIntegrationProvider:
    """Test IntegrationProvider model."""

    def test_create_provider(self):
        """Test creating a provider."""
        provider = IntegrationProvider(
            provider_id="github",
            category="SCM",
            name="GitHub",
            status="GA",
            capabilities={"webhook_supported": True},
            api_version="v3",
        )
        assert provider.provider_id == "github"
        assert provider.category == "SCM"
        assert provider.name == "GitHub"
        assert provider.status == "GA"
        assert provider.capabilities == {"webhook_supported": True}
        assert provider.api_version == "v3"

    def test_provider_defaults(self):
        """Test provider default values."""
        provider = IntegrationProvider(
            provider_id="test",
            category="SCM",
            name="Test",
        )
        assert provider.status == "alpha"
        assert provider.capabilities == {}

class TestIntegrationConnection:
    """Test IntegrationConnection model."""

    def test_create_connection(self, sample_tenant_id):
        """Test creating a connection."""
        connection = IntegrationConnection(
            tenant_id=sample_tenant_id,
            provider_id="github",
            display_name="Test Connection",
            auth_ref="kms-secret-123",
            status="pending_verification",
            enabled_capabilities={"webhook": True},
            metadata_tags={"org": "test-org"},
        )
        assert connection.tenant_id == sample_tenant_id
        assert connection.provider_id == "github"
        assert connection.display_name == "Test Connection"
        assert connection.auth_ref == "kms-secret-123"
        assert connection.status == "pending_verification"
        assert connection.enabled_capabilities == {"webhook": True}
        assert connection.metadata_tags == {"org": "test-org"}
        assert connection.connection_id is not None
        assert isinstance(connection.created_at, datetime)
        assert isinstance(connection.updated_at, datetime)

    def test_connection_timestamps(self, sample_tenant_id):
        """Test connection timestamp defaults."""
        connection = IntegrationConnection(
            tenant_id=sample_tenant_id,
            provider_id="github",
            display_name="Test",
            auth_ref="secret",
        )
        assert connection.created_at is not None
        assert connection.updated_at is not None

class TestWebhookRegistration:
    """Test WebhookRegistration model."""

    def test_create_webhook_registration(self, sample_connection_id):
        """Test creating a webhook registration."""
        registration = WebhookRegistration(
            connection_id=uuid4(),
            public_url="https://example.com/webhook",
            secret_ref="kms-secret-456",
            events_subscribed=["pull_request", "push"],
            status="active",
        )
        assert registration.public_url == "https://example.com/webhook"
        assert registration.secret_ref == "kms-secret-456"
        assert registration.events_subscribed == ["pull_request", "push"]
        assert registration.status == "active"
        assert registration.registration_id is not None

class TestPollingCursor:
    """Test PollingCursor model."""

    def test_create_polling_cursor(self):
        """Test creating a polling cursor."""
        cursor = PollingCursor(
            connection_id=uuid4(),
            cursor_position="last-event-123",
            last_polled_at=datetime.utcnow(),
        )
        assert cursor.cursor_position == "last-event-123"
        assert cursor.last_polled_at is not None
        assert cursor.cursor_id is not None

class TestAdapterEvent:
    """Test AdapterEvent model."""

    def test_create_adapter_event(self):
        """Test creating an adapter event."""
        event = AdapterEvent(
            connection_id=uuid4(),
            provider_event_type="pull_request.opened",
            received_at=datetime.utcnow(),
            raw_payload_ref="storage://event-123",
        )
        assert event.provider_event_type == "pull_request.opened"
        assert event.received_at is not None
        assert event.raw_payload_ref == "storage://event-123"
        assert event.event_id is not None

class TestNormalisedAction:
    """Test NormalisedAction model."""

    def test_create_normalised_action(self, sample_tenant_id):
        """Test creating a normalised action."""
        action = NormalisedAction(
            tenant_id=sample_tenant_id,
            provider_id="github",
            connection_id=uuid4(),
            canonical_type="comment_on_pr",
            target={"repository": "org/repo", "pr_number": 123},
            payload={"body": "Test comment"},
            idempotency_key="idempotency-123",
            correlation_id="correlation-456",
            status="pending",
        )
        assert action.tenant_id == sample_tenant_id
        assert action.provider_id == "github"
        assert action.canonical_type == "comment_on_pr"
        assert action.target == {"repository": "org/repo", "pr_number": 123}
        assert action.payload == {"body": "Test comment"}
        assert action.idempotency_key == "idempotency-123"
        assert action.correlation_id == "correlation-456"
        assert action.status == "pending"
        assert action.action_id is not None
        assert isinstance(action.created_at, datetime)

