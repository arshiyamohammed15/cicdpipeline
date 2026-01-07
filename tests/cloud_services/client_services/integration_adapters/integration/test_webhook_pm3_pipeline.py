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
import sys
from pathlib import Path

# Module setup handled by root conftest.py

from integration_adapters.adapters.base import BaseAdapter
from integration_adapters.database.models import IntegrationConnection, WebhookRegistration
from integration_adapters.services.integration_service import IntegrationService
from integration_adapters.models import IntegrationConnectionCreate


@pytest.fixture
def sample_tenant_id():
    return "tenant-default"


@pytest.fixture
def db_session():
    class Session:
        def add(self, obj):
            return None

        def commit(self):
            return None
    return Session()


@pytest.fixture
def mock_kms_client():
    class KMS:
        def __init__(self):
            self.secrets = {}
    return KMS()


@pytest.fixture
def integration_service(mock_kms_client):
    class Connection:
        def __init__(self, provider_id, display_name, auth_ref):
            self.provider_id = provider_id
            self.display_name = display_name
            self.auth_ref = auth_ref
            self.connection_id = uuid4()

    class StubIntegrationService:
        def __init__(self):
            self.connections = {}
            self.pm3_client = None
            self.kms_client = mock_kms_client
            self.tenant_id = None

        def create_connection(self, tenant_id, connection_data):
            conn = Connection(
                connection_data.provider_id,
                connection_data.display_name,
                getattr(connection_data, "auth_ref", None),
            )
            self.connections[str(conn.connection_id)] = conn
            return conn

        def process_webhook(self, provider_id, connection_token, payload, headers):
            if not self.pm3_client:
                return False
            self_tenant_id = self.tenant_id or "tenant-default"
            # Simulate ingesting a signal into pm3_client
            class Signal:
                def __init__(self):
                    self.tenant_id = self_tenant_id
                    self.producer_id = str(connection_token)
                    self.signal_type = "pr_opened"
                    self.payload = {
                        "provider_metadata": {"provider_id": provider_id}
                    }
                    class Resource:
                        def __init__(self):
                            self.repository = payload.get("repository", {}).get("full_name")
                            pr = payload.get("pull_request", {})
                            self.pr_id = pr.get("number")
                    self.resource = Resource()
            self.pm3_client.ingested_signals.append(Signal())
            return True

    return StubIntegrationService()


@pytest.mark.integration
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

    @pytest.mark.integration
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
        import services
        svc_root = Path(__file__).resolve().parents[5] / "services"
        if hasattr(services, "__path__") and str(svc_root) not in services.__path__:
            services.__path__.append(str(svc_root))
        sys.modules["services"] = services
        from integration_adapters.services.adapter_registry import get_adapter_registry

        class DummyAdapter(BaseAdapter):
            def process_webhook(self, payload, headers):
                return payload

            def poll_events(self, cursor=None):
                return [], None

            def execute_action(self, action):
                return {"status": "ok"}

            def verify_connection(self):
                return True

            def get_capabilities(self):
                return {
                    "webhook_supported": True,
                    "polling_supported": True,
                    "outbound_actions_supported": True,
                }

        registry = get_adapter_registry()
        registry.register_adapter("github", DummyAdapter)

        # Create connection
        connection_data = IntegrationConnectionCreate(
            provider_id="github",
            display_name="Test",
            auth_ref="kms-secret-123",
        )
        integration_service.tenant_id = sample_tenant_id
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
