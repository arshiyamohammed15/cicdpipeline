from __future__ import annotations
"""
Integration test: Webhook → PM-3 Pipeline (IT-IA-02).

What: Test end-to-end webhook processing pipeline
Why: Ensure webhooks are correctly transformed and forwarded to PM-3
Coverage Target: Full pipeline coverage
"""

# Imports handled by conftest.py

import pytest
import json
import hmac
import hashlib
from unittest.mock import Mock, patch
from uuid import uuid4

# Module setup handled by root conftest.py

from integration_adapters.database.models import IntegrationConnection, WebhookRegistration
from integration_adapters.services.integration_service import IntegrationService
from integration_adapters.models import IntegrationConnectionCreate

class TestWebhookPM3Pipeline:
    """Test webhook → PM-3 pipeline integration."""

    @pytest.fixture
    def mock_pm3_client(self):
        """Mock PM-3 client that captures ingested signals."""
        class MockPM3:
            def __init__(self):
                self.ingested_signals = []

            def ingest_signal(self, signal):
                self.ingested_signals.append(signal)
                return True

        return MockPM3()

    def test_webhook_to_pm3_pipeline(
        self,
        integration_service,
        db_session,
        sample_tenant_id,
        mock_kms_client,
        mock_pm3_client,
    ):
        """Test webhook → adapter → SignalEnvelope → PM-3 pipeline."""
        # Register GitHub adapter
        from services.adapter_registry import get_adapter_registry
        from adapters.github.adapter import GitHubAdapter
        registry = get_adapter_registry()
        registry.register_adapter("github", GitHubAdapter)

        # Create connection
        connection_data = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Test",
            auth_ref="kms-secret-123",
        )
        connection = integration_service.create_connection(sample_tenant_id, connection_data)

        # Create webhook registration
        webhook_reg = WebhookRegistration(
            connection_id=connection.connection_id,
            public_url="https://example.com/webhook",
            secret_ref="kms-secret-456",
            events_subscribed=["pull_request"],
            status="active",
        )
        db_session.add(webhook_reg)
        db_session.commit()

        # Mock KMS to return webhook secret
        if hasattr(mock_kms_client, 'secrets'):
            mock_kms_client.secrets["kms-secret-456"] = "webhook-secret-123"

        # GitHub webhook payload
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 123,
                "title": "Test PR",
                "state": "open",
                "head": {"ref": "feature-branch"},
            },
            "repository": {"full_name": "org/repo"},
            "id": "github-event-123",
        }

        # Calculate signature
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature_hash = hmac.new(
            "webhook-secret-123".encode("utf-8"),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()

        headers = {
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={signature_hash}",
        }

        # Replace PM-3 client in service
        integration_service.pm3_client = mock_pm3_client

        # Process webhook
        success = integration_service.process_webhook(
            provider_id="github",
            connection_token=str(connection.connection_id),
            payload=payload,
            headers=headers,
        )

        assert success is True
        assert len(mock_pm3_client.ingested_signals) == 1

        signal = mock_pm3_client.ingested_signals[0]
        assert signal.tenant_id == sample_tenant_id
        assert signal.producer_id == str(connection.connection_id)
        assert signal.signal_type == "pr_opened"
        assert signal.payload["provider_metadata"]["provider_id"] == "github"
        assert signal.resource is not None
        assert signal.resource.repository == "org/repo"
        assert signal.resource.pr_id == 123

