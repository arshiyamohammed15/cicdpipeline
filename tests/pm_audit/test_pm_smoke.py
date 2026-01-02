from __future__ import annotations

import os
from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.pm_audit.audit_log import append_record

os.environ.setdefault("USE_REAL_SERVICES", "false")

SMOKE_LOG = "pm_smoke_receipts.jsonl"


def test_pm1_mmm_receipt_smoke(monkeypatch: pytest.MonkeyPatch):
    from mmm_engine.models import MMMAction, MMMContext, MMMDecision, ActionType, ActorType, Surface
    from mmm_engine.services import MMMService
    import mmm_engine.services as services_module

    fixed_uuid = UUID("00000000-0000-0000-0000-000000000001")
    monkeypatch.setattr(services_module.uuid, "uuid4", lambda: fixed_uuid)

    class _ErisStub:
        def __init__(self) -> None:
            self.payloads: list[dict] = []

        async def emit_receipt(self, payload: dict) -> str:
            self.payloads.append(payload)
            return payload.get("receipt_id", "")

    service = MMMService()
    eris_stub = _ErisStub()
    service.eris = eris_stub

    context = MMMContext(
        tenant_id="tenant-smoke",
        actor_id="actor-1",
        actor_type=ActorType.HUMAN,
        actor_roles=["developer"],
        repo_id="repo-1",
        branch="main",
        file_path=None,
        policy_snapshot_id="policy-snap-1",
        quiet_hours=None,
        recent_signals=[],
    )
    action = MMMAction(
        action_id="action-1",
        type=ActionType.MIRROR,
        surfaces=[Surface.CI],
        payload={"message": "smoke"},
    )
    decision = MMMDecision(
        decision_id="pm1-decision-001",
        tenant_id="tenant-smoke",
        actor_id="actor-1",
        actor_type=ActorType.HUMAN,
        context=context,
        actions=[action],
        policy_snapshot_id="policy-snap-1",
    )

    ok = service._emit_decision_receipt(decision, None, degraded_mode=False, policy_stale=False)
    assert ok is True
    assert eris_stub.payloads

    receipt_id = eris_stub.payloads[-1]["receipt_id"]
    append_record(SMOKE_LOG, {"module": "PM-1", "receipt_id": receipt_id})


def test_pm2_cccs_receipt_smoke(monkeypatch: pytest.MonkeyPatch, tmp_path):
    from shared_libs.cccs.receipts import OfflineCourier, ReceiptConfig, ReceiptService, WALQueue
    from shared_libs.cccs.receipts import service as receipts_service

    fixed_uuid = UUID("00000000-0000-0000-0000-000000000002")
    monkeypatch.setattr(receipts_service.uuid, "uuid4", lambda: fixed_uuid)

    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    storage_path = tmp_path / "receipts.jsonl"
    wal_path = tmp_path / "wal.jsonl"

    config = ReceiptConfig(
        gate_id="cccs",
        storage_path=storage_path,
        epc11_base_url="http://epc11.local",
        epc11_key_id="key-1",
        pm7_base_url="",
    )
    courier = OfflineCourier(WALQueue(wal_path))
    service = ReceiptService(config, courier, time_fn=lambda: fixed_time)
    service._sign = lambda payload: "sig-fixed"

    record = service.write_receipt(
        inputs={"request_id": "req-smoke"},
        result={"status": "pass", "rationale": "ok", "badges": []},
        actor={"actor_id": "actor-1", "actor_type": "human"},
        policy_metadata={"policy_version_ids": ["pol-1"], "policy_version_hash": "hash"},
        trace=None,
    )

    assert record.receipt_id == str(fixed_uuid)
    append_record(SMOKE_LOG, {"module": "PM-2", "receipt_id": record.receipt_id})


def test_pm3_sin_receipt_smoke():
    from signal_ingestion_normalization.dependencies import MockM32Trust
    from signal_ingestion_normalization.dlq import DLQHandler
    from signal_ingestion_normalization.models import Environment, ErrorCode, SignalEnvelope, SignalKind

    class _FixedTrust(MockM32Trust):
        def emit_receipt(self, receipt_data):
            receipt_id = "receipt_0000000000000000"
            receipt_data["receipt_id"] = receipt_id
            receipt_data["timestamp"] = "2024-01-01T00:00:00Z"
            receipt_data["signature"] = "sig-fixed"
            self.receipts[receipt_id] = receipt_data
            return receipt_id

    trust = _FixedTrust()
    handler = DLQHandler(trust)

    signal = SignalEnvelope(
        signal_id="signal-001",
        tenant_id="tenant-1",
        environment=Environment.DEV,
        producer_id="producer-1",
        actor_id=None,
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        ingested_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        payload={"event_name": "pr_opened", "pr_id": 1},
        schema_version="1.0.0",
    )

    handler.add_to_dlq(signal, ErrorCode.GOVERNANCE_VIOLATION, "governance")
    assert trust.receipts
    receipt_id = next(iter(trust.receipts))
    append_record(SMOKE_LOG, {"module": "PM-3", "receipt_id": receipt_id})


def test_pm4_detection_receipt_smoke(monkeypatch: pytest.MonkeyPatch):
    from detection_engine_core.models import DecisionRequest, EvaluationPoint
    from detection_engine_core.services import DetectionEngineService
    import detection_engine_core.services as services_module

    fixed_uuid = UUID("00000000-0000-0000-0000-000000000004")
    monkeypatch.setattr(services_module.uuid, "uuid4", lambda: fixed_uuid)

    request = DecisionRequest(
        evaluation_point=EvaluationPoint.PRE_COMMIT,
        inputs={"risk_score": 0.1, "file_count": 1},
        actor={"actor_id": "actor-1", "actor_type": "human"},
        context={"surface": "ci"},
        policy_version_ids=["POL-TEST"],
    )

    response = DetectionEngineService().evaluate_decision(request)
    assert response.receipt.receipt_id == str(fixed_uuid)
    append_record(SMOKE_LOG, {"module": "PM-4", "receipt_id": response.receipt.receipt_id})


def test_pm5_integration_adapters_receipt_smoke():
    from integration_adapters.adapters.base import BaseAdapter
    from integration_adapters.database.models import Base, IntegrationConnection, IntegrationProvider, NormalisedAction
    from integration_adapters.services.adapter_registry import get_adapter_registry
    from integration_adapters.services.integration_service import (
        IntegrationService,
        ToolOutputSchemaViolation,
        TOOL_OUTPUT_SCHEMA_VIOLATION,
    )

    class _StubBudgetClient:
        def check_budget(self, tenant_id: str, provider_id: str, connection_id: str, cost: float = 1.0):
            return True, None

    class _StubKMSClient:
        def get_secret(self, auth_ref: str, tenant_id: str):
            return "secret"

    class _StubERISClient:
        def __init__(self) -> None:
            self.receipts: list[dict] = []

        def emit_receipt(self, **kwargs) -> str:
            receipt_id = "00000000-0000-0000-0000-000000000005"
            kwargs["receipt_id"] = receipt_id
            self.receipts.append(kwargs)
            return receipt_id

    class _StubMetrics:
        def increment_action_error(self, *args, **kwargs) -> None:
            return None

        def increment_action_executed(self, *args, **kwargs) -> None:
            return None

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    provider = IntegrationProvider(
        provider_id="stub-provider",
        category="chat",
        name="Stub",
        status="GA",
        capabilities={},
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)

    connection = IntegrationConnection(
        tenant_id="tenant-1",
        provider_id="stub-provider",
        display_name="Stub Connection",
        auth_ref="kms-secret",
    )
    session.add(connection)
    session.commit()
    session.refresh(connection)

    class _InvalidAdapter(BaseAdapter):
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
    registry.register_adapter("stub-provider", _InvalidAdapter)

    eris_client = _StubERISClient()
    service = IntegrationService(
        session=session,
        kms_client=_StubKMSClient(),
        budget_client=_StubBudgetClient(),
        pm3_client=None,
        eris_client=eris_client,
    )
    service.metrics = _StubMetrics()

    action_data = {
        "provider_id": "stub-provider",
        "connection_id": str(connection.connection_id),
        "canonical_type": "post_chat_message",
        "target": {"channel_id": "C123"},
        "payload": {"text": "hello"},
        "idempotency_key": "idem-1",
        "correlation_id": "corr-1",
    }

    with pytest.raises(ToolOutputSchemaViolation):
        service.execute_action("tenant-1", action_data)

    stored_action = (
        session.query(NormalisedAction)
        .filter(NormalisedAction.idempotency_key == "idem-1")
        .first()
    )
    assert stored_action is not None
    assert stored_action.status == "failed"
    assert eris_client.receipts
    receipt = eris_client.receipts[0]
    assert receipt.get("result", {}).get("reason_code") == TOOL_OUTPUT_SCHEMA_VIOLATION

    append_record(SMOKE_LOG, {"module": "PM-5", "receipt_id": receipt["receipt_id"]})


@pytest.mark.asyncio
async def test_pm6_llm_gateway_receipt_smoke():
    from cloud_services.llm_gateway.models import (
        Actor,
        Budget,
        LLMRequest,
        OperationType,
        SafetyOverrides,
        Tenant,
    )
    from cloud_services.llm_gateway.services import build_default_service
    from fastapi import HTTPException

    class _ProviderStub:
        def __init__(self) -> None:
            self.called = False

        def invoke(self, tenant_id: str, logical_model_id: str, prompt: str, operation_type: str, fallback: bool = False):
            self.called = True
            return {"model": logical_model_id, "content": "stub"}

    class _ErisSpy:
        def __init__(self) -> None:
            self.payloads: list[dict] = []

        def emit_receipt(self, payload: dict) -> str:
            self.payloads.append(payload)
            return payload.get("receipt_id", "")

    service = build_default_service()
    provider = _ProviderStub()
    eris_spy = _ErisSpy()
    service.provider_client = provider  # type: ignore[assignment]
    service.eris_client = eris_spy  # type: ignore[assignment]

    request = LLMRequest(
        request_id="req-smoke-001",
        actor=Actor(
            actor_id="actor-1",
            actor_type="human",
            roles=["developer"],
            capabilities=["llm.invoke"],
            scopes=["llm.chat"],
            session_assurance_level="high",
            workspace_id="workspace-1",
        ),
        tenant=Tenant(tenant_id="tenant-1", region="us-east"),
        logical_model_id="default_chat",
        operation_type=OperationType.CHAT,
        intended_capability="analysis",
        sensitivity_level="medium",
        system_prompt_id="sys-default",
        user_prompt="hello",
        context_segments=[],
        policy_snapshot_id="policy-snap-1",
        policy_version_ids=["pol-1"],
        budget=Budget(max_tokens=4096, timeout_ms=2000, priority="normal", temperature=0.2),
        safety_overrides=SafetyOverrides(),
    )

    with pytest.raises(HTTPException):
        await service.handle_chat(request)

    assert provider.called is False
    assert eris_spy.payloads
    receipt_id = eris_spy.payloads[-1]["receipt_id"]
    append_record(SMOKE_LOG, {"module": "PM-6", "receipt_id": receipt_id})


@pytest.mark.asyncio
async def test_pm7_eris_receipt_ingestion_smoke():
    from evidence_receipt_indexing_service.services import ReceiptIngestionService

    class _QueryStub:
        def filter(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def first(self):
            return None

    class _SessionStub:
        def __init__(self) -> None:
            self.added: list[object] = []
            self.committed = False

        def query(self, *args, **kwargs):
            return _QueryStub()

        def add(self, record):
            self.added.append(record)

        def commit(self):
            self.committed = True

        def rollback(self):
            self.committed = False

    receipt = {
        "receipt_id": "00000000-0000-0000-0000-000000000007",
        "gate_id": "pm7-smoke",
        "policy_version_ids": ["pol-1"],
        "snapshot_hash": "sha256:" + "0" * 64,
        "timestamp_utc": "2024-01-01T00:00:00Z",
        "timestamp_monotonic_ms": 123456,
        "evaluation_point": "pre-commit",
        "inputs": {"request_id": "req-smoke"},
        "decision": {"status": "pass", "rationale": "ok", "badges": []},
        "actor": {"repo_id": "repo-1", "type": "service"},
        "degraded": False,
        "signature": "sig-fixed",
        "schema_version": "v1",
    }

    session = _SessionStub()
    service = ReceiptIngestionService(session)
    success, receipt_id, error = await service.ingest_receipt(receipt, tenant_id="tenant-1")

    assert success is True
    assert error is None
    assert receipt_id == receipt["receipt_id"]
    assert session.added
    assert session.committed is True
    append_record(SMOKE_LOG, {"module": "PM-7", "receipt_id": receipt_id})
