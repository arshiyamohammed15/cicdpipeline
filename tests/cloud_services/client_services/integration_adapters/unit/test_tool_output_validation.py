from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from integration_adapters.adapters.base import BaseAdapter
from integration_adapters.database.models import Base, IntegrationConnection, IntegrationProvider, NormalisedAction
from integration_adapters.models import ActionStatus, NormalisedActionResponse
from integration_adapters.services.adapter_registry import get_adapter_registry
from integration_adapters.services.integration_service import (
    IntegrationService,
    ToolOutputSchemaViolation,
    TOOL_OUTPUT_SCHEMA_VIOLATION,
)
from tests.shared_harness import assert_enforcement_receipt_fields


class StubBudgetClient:
    def check_budget(self, tenant_id: str, provider_id: str, connection_id: str, cost: float = 1.0):
        return True, None


class StubKMSClient:
    def get_secret(self, auth_ref: str, tenant_id: str):
        return "secret-token"


class StubERISClient:
    def __init__(self) -> None:
        self.receipts: list[dict] = []

    def emit_receipt(self, **kwargs) -> bool:
        self.receipts.append(kwargs)
        return True


class StubMetrics:
    def increment_action_error(self, *args, **kwargs) -> None:
        return None

    def increment_action_executed(self, *args, **kwargs) -> None:
        return None


def _build_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _seed_connection(session, tenant_id: str, provider_id: str):
    provider = IntegrationProvider(
        provider_id=provider_id,
        category="chat",
        name="Stub",
        status="GA",
        capabilities={},
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)

    connection = IntegrationConnection(
        tenant_id=tenant_id,
        provider_id=provider_id,
        display_name="Stub Connection",
        auth_ref="kms-secret",
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)
    return connection


def test_invalid_tool_output_is_rejected_and_emits_receipt():
    session = _build_session()
    tenant_id = "tenant-1"
    provider_id = "stub-invalid"
    connection = _seed_connection(session, tenant_id, provider_id)

    class InvalidAdapter(BaseAdapter):
        def process_webhook(self, payload, headers):
            return {}

        def poll_events(self, cursor=None):
            return [], cursor

        def execute_action(self, action):
            return {"status": "ok"}

        def verify_connection(self):
            return True

        def get_capabilities(self):
            return {"outbound_actions_supported": True}

    registry = get_adapter_registry()
    registry.register_adapter(provider_id, InvalidAdapter)

    eris_client = StubERISClient()
    service = IntegrationService(
        session=session,
        kms_client=StubKMSClient(),
        budget_client=StubBudgetClient(),
        pm3_client=None,
        eris_client=eris_client,
    )
    service.metrics = StubMetrics()

    action_data = {
        "provider_id": provider_id,
        "connection_id": str(connection.connection_id),
        "canonical_type": "post_chat_message",
        "target": {"channel_id": "C123"},
        "payload": {"text": "hello"},
        "idempotency_key": "idem-1",
        "correlation_id": "corr-1",
    }

    with pytest.raises(ToolOutputSchemaViolation):
        service.execute_action(tenant_id, action_data)

    stored_action = (
        session.query(NormalisedAction)
        .filter(NormalisedAction.idempotency_key == "idem-1")
        .first()
    )
    assert stored_action is not None
    assert stored_action.status == "failed"
    assert stored_action.payload == {"error": "tool output schema violation"}

    assert eris_client.receipts
    receipt = eris_client.receipts[0]
    assert_enforcement_receipt_fields(receipt, require_correlation=True)
    result = receipt.get("result", {})
    assert result.get("reason_code") == TOOL_OUTPUT_SCHEMA_VIOLATION
    assert result.get("tool_id") == f"{provider_id}.post_chat_message"
    assert result.get("schema_version") == "1.0.0"
    assert "validation_summary" in result
    assert "payload" not in result


def test_valid_tool_output_proceeds():
    session = _build_session()
    tenant_id = "tenant-2"
    provider_id = "stub-valid"
    connection = _seed_connection(session, tenant_id, provider_id)

    class ValidAdapter(BaseAdapter):
        def process_webhook(self, payload, headers):
            return {}

        def poll_events(self, cursor=None):
            return [], cursor

        def execute_action(self, action):
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=tenant_id,
                provider_id=provider_id,
                connection_id=connection.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"status": "ok"},
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
            return {"outbound_actions_supported": True}

    registry = get_adapter_registry()
    registry.register_adapter(provider_id, ValidAdapter)

    service = IntegrationService(
        session=session,
        kms_client=StubKMSClient(),
        budget_client=StubBudgetClient(),
        pm3_client=None,
        eris_client=StubERISClient(),
    )
    service.metrics = StubMetrics()

    action_data = {
        "provider_id": provider_id,
        "connection_id": str(connection.connection_id),
        "canonical_type": "post_chat_message",
        "target": {"channel_id": "C456"},
        "payload": {"text": "hello"},
        "idempotency_key": "idem-2",
        "correlation_id": "corr-2",
    }

    action = service.execute_action(tenant_id, action_data)

    assert action is not None
    assert action.status == ActionStatus.COMPLETED.value
