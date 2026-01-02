from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.pm_audit.audit_log import append_record

os.environ.setdefault("USE_REAL_SERVICES", "false")
logging.disable(logging.CRITICAL)

E2E_LOG = "pm_e2e_receipts.jsonl"


@pytest.mark.asyncio
async def test_pm_e2e_golden_path(monkeypatch: pytest.MonkeyPatch):
    from signal_ingestion_normalization.dependencies import (
        MockM29DataGovernance,
        MockM32Trust,
        MockM34SchemaRegistry,
        MockM35Budgeting,
    )
    from signal_ingestion_normalization.dlq import DLQHandler
    from signal_ingestion_normalization.governance import GovernanceEnforcer
    from signal_ingestion_normalization.models import (
        DataContract,
        Environment,
        ErrorCode,
        IngestStatus,
        Plane,
        ProducerRegistration,
        SignalEnvelope,
        SignalKind,
    )
    from signal_ingestion_normalization.normalization import NormalizationEngine
    from signal_ingestion_normalization.observability import MetricsRegistry, StructuredLogger
    from signal_ingestion_normalization.producer_registry import ProducerRegistry
    from signal_ingestion_normalization.routing import RoutingEngine
    from signal_ingestion_normalization.services import SignalIngestionService
    from signal_ingestion_normalization.validation import ValidationEngine
    from signal_ingestion_normalization.deduplication import DeduplicationStore

    from detection_engine_core.models import DecisionRequest, EvaluationPoint
    from detection_engine_core.services import DetectionEngineService
    import detection_engine_core.services as detection_services

    from mmm_engine.models import MMMAction, MMMContext, MMMDecision, ActionType, ActorType, Surface
    from mmm_engine.services import MMMService
    import mmm_engine.services as mmm_services

    from integration_adapters.adapters.base import BaseAdapter
    from integration_adapters.database.models import Base, IntegrationConnection, IntegrationProvider
    from integration_adapters.services.adapter_registry import get_adapter_registry
    from integration_adapters.services.integration_service import (
        IntegrationService,
        ToolOutputSchemaViolation,
    )

    from evidence_receipt_indexing_service.services import ReceiptIngestionService

    fixed_time = datetime(2024, 1, 1, tzinfo=timezone.utc)

    class _FixedTrust(MockM32Trust):
        def emit_receipt(self, receipt_data):
            receipt_id = "receipt_0000000000000000"
            receipt_data["receipt_id"] = receipt_id
            receipt_data["timestamp"] = "2024-01-01T00:00:00Z"
            receipt_data["signature"] = "sig-fixed"
            self.receipts[receipt_id] = receipt_data
            return receipt_id

    schema_registry = MockM34SchemaRegistry()
    budgeting = MockM35Budgeting()
    data_governance = MockM29DataGovernance()
    trust = _FixedTrust()

    producer_registry = ProducerRegistry(schema_registry, budgeting)
    governance = GovernanceEnforcer(data_governance)
    validation_engine = ValidationEngine(producer_registry, governance, schema_registry)
    normalization_engine = NormalizationEngine(schema_registry)
    routing_engine = RoutingEngine()
    deduplication_store = DeduplicationStore()
    dlq_handler = DLQHandler(trust)
    metrics_registry = MetricsRegistry()
    structured_logger = StructuredLogger()

    contract = DataContract(
        signal_type="pr_opened",
        contract_version="1.0.0",
        required_fields=["event_name", "pr_id"],
        optional_fields=["severity"],
    )
    schema_registry.register_contract(
        contract.signal_type,
        contract.contract_version,
        contract.model_dump(),
    )

    producer = ProducerRegistration(
        producer_id="producer-1",
        name="Test Producer",
        plane=Plane.EDGE,
        owner="owner-1",
        allowed_signal_kinds=[SignalKind.EVENT],
        allowed_signal_types=["pr_opened"],
        contract_versions={"pr_opened": "1.0.0"},
    )
    producer_registry.register_producer(producer)

    ingestion_service = SignalIngestionService(
        producer_registry,
        validation_engine,
        normalization_engine,
        routing_engine,
        deduplication_store,
        dlq_handler,
        metrics_registry,
        structured_logger,
        governance,
    )

    signal = SignalEnvelope(
        signal_id="signal-001",
        tenant_id="tenant-1",
        environment=Environment.DEV,
        producer_id="producer-1",
        actor_id=None,
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=fixed_time,
        ingested_at=fixed_time,
        payload={"event_name": "pr_opened", "pr_id": 1, "severity": "info"},
        schema_version="1.0.0",
    )

    ingest_result = ingestion_service.ingest_signal(signal, tenant_id="tenant-1")
    assert ingest_result.status == IngestStatus.ACCEPTED

    dlq_handler.add_to_dlq(signal, ErrorCode.GOVERNANCE_VIOLATION, "governance")
    pm3_receipt_id = next(iter(trust.receipts))
    append_record(E2E_LOG, {"module": "PM-3", "receipt_id": pm3_receipt_id})

    fixed_decision_uuid = UUID("00000000-0000-0000-0000-000000000004")
    monkeypatch.setattr(detection_services.uuid, "uuid4", lambda: fixed_decision_uuid)

    dec_request = DecisionRequest(
        evaluation_point=EvaluationPoint.PRE_COMMIT,
        inputs={
            "risk_score": 0.2,
            "file_count": 2,
            "has_tests": True,
            "signal_id": signal.signal_id,
        },
        actor={"actor_id": "actor-1", "actor_type": "human"},
        context={"surface": "ci"},
        policy_version_ids=["POL-TEST"],
    )

    dec_response = DetectionEngineService().evaluate_decision(dec_request)
    pm4_receipt = dec_response.receipt.model_dump()
    append_record(E2E_LOG, {"module": "PM-4", "receipt_id": pm4_receipt["receipt_id"]})

    fixed_mmm_uuid = UUID("00000000-0000-0000-0000-000000000001")
    monkeypatch.setattr(mmm_services.uuid, "uuid4", lambda: fixed_mmm_uuid)

    class _ErisStub:
        def __init__(self) -> None:
            self.payloads: list[dict] = []

        async def emit_receipt(self, payload: dict) -> str:
            self.payloads.append(payload)
            return payload.get("receipt_id", "")

    mmm_service = MMMService()
    eris_stub = _ErisStub()
    mmm_service.eris = eris_stub

    mmm_context = MMMContext(
        tenant_id="tenant-1",
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
    mmm_action = MMMAction(
        action_id="action-1",
        type=ActionType.MENTOR,
        surfaces=[Surface.CI],
        payload={"note": "e2e"},
    )
    mmm_decision = MMMDecision(
        decision_id="pm1-e2e-001",
        tenant_id="tenant-1",
        actor_id="actor-1",
        actor_type=ActorType.HUMAN,
        context=mmm_context,
        actions=[mmm_action],
        policy_snapshot_id="policy-snap-1",
    )

    ok = await asyncio.to_thread(
        mmm_service._emit_decision_receipt,
        mmm_decision,
        None,
        False,
        False,
    )
    assert ok is True
    assert eris_stub.payloads
    pm1_receipt = eris_stub.payloads[-1]
    append_record(E2E_LOG, {"module": "PM-1", "receipt_id": pm1_receipt["receipt_id"]})

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
    integration_service = IntegrationService(
        session=session,
        kms_client=_StubKMSClient(),
        budget_client=_StubBudgetClient(),
        pm3_client=None,
        eris_client=eris_client,
    )
    integration_service.metrics = _StubMetrics()

    action_data = {
        "provider_id": "stub-provider",
        "connection_id": str(connection.connection_id),
        "canonical_type": "post_chat_message",
        "target": {"channel_id": "C123"},
        "payload": {"text": "hello"},
        "idempotency_key": "idem-e2e",
        "correlation_id": "corr-e2e",
    }

    with pytest.raises(ToolOutputSchemaViolation):
        integration_service.execute_action("tenant-1", action_data)

    pm5_receipt = eris_client.receipts[0]
    append_record(E2E_LOG, {"module": "PM-5", "receipt_id": pm5_receipt["receipt_id"]})

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

    session_stub = _SessionStub()
    ingestion = ReceiptIngestionService(session_stub)

    errors: list[str] = []
    for module_name, receipt in (
        ("PM-4", pm4_receipt),
        ("PM-1", pm1_receipt),
        ("PM-5", pm5_receipt),
    ):
        try:
            success, receipt_id, error = await ingestion.ingest_receipt(receipt, tenant_id="tenant-1")
            if not success or error:
                errors.append(f"{module_name}: {error or 'unknown error'}")
                append_record(
                    E2E_LOG,
                    {
                        "module": "PM-7",
                        "source_module": module_name,
                        "receipt_id": receipt.get("receipt_id"),
                        "ingest_status": "error",
                        "error": error or "unknown error",
                    },
                )
            else:
                append_record(
                    E2E_LOG,
                    {
                        "module": "PM-7",
                        "source_module": module_name,
                        "receipt_id": receipt_id,
                        "ingest_status": "success",
                    },
                )
        except Exception as exc:
            errors.append(f"{module_name}: {exc}")
            append_record(
                E2E_LOG,
                {
                    "module": "PM-7",
                    "source_module": module_name,
                    "receipt_id": receipt.get("receipt_id"),
                    "ingest_status": "exception",
                    "error": str(exc),
                },
            )

    assert not errors, f"PM-7 ingestion failures: {errors}"
