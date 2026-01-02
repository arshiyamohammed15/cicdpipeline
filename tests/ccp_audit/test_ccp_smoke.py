from __future__ import annotations

import os
from uuid import UUID

import pytest

os.environ.setdefault("USE_REAL_SERVICES", "false")


def test_ccp_identity_and_policy_imports() -> None:
    from identity_access_management.services import (
        IAMService,
        TokenValidator,
        RBACEvaluator,
        ABACEvaluator,
    )
    from configuration_policy_management.services import PolicyService

    assert IAMService is not None
    assert TokenValidator is not None
    assert RBACEvaluator is not None
    assert ABACEvaluator is not None
    assert PolicyService is not None


def test_ccp_schema_validation_smoke() -> None:
    from shared_libs.tool_schema_validation import ToolOutputValidator, ToolSchemaRegistry

    registry = ToolSchemaRegistry()
    registry.register(
        "tool.sample",
        {
            "type": "object",
            "required": ["id", "status"],
            "properties": {"id": {"type": "string"}, "status": {"type": "string"}},
        },
        "1.0.0",
    )
    validator = ToolOutputValidator(registry)
    result = validator.validate("tool.sample", {"id": "tool-1", "status": "ok"})

    assert result.ok is True
    assert result.schema_version == "1.0.0"


def test_ccp_governed_memory_emits_receipts() -> None:
    from data_governance_privacy.services import DataGovernanceService

    service = DataGovernanceService()
    result = service.submit_rights_request(
        tenant_id="tenant-1",
        data_subject_id="subject-1",
        right_type="access",
        verification_data={"method": "email"},
        additional_info="smoke",
    )

    assert result.get("request_id")
    assert service.evidence_ledger.receipts
    receipt = next(iter(service.evidence_ledger.receipts.values()))
    assert receipt.get("operation", "").startswith("rights_")


def test_ccp_external_tool_reliability_owner() -> None:
    from integration_adapters.reliability.circuit_breaker import CircuitBreaker, CircuitState

    breaker = CircuitBreaker(UUID("00000000-0000-0000-0000-000000000050"))
    result = breaker.call(lambda: "ok")

    assert result == "ok"
    assert breaker.state == CircuitState.CLOSED


def test_ccp_llm_gateway_budget_owner() -> None:
    from cloud_services.llm_gateway.services import llm_gateway_service
    from shared_libs.token_budget import BudgetManager

    assert llm_gateway_service.BudgetManager is BudgetManager


def test_ccp_observability_settings_smoke() -> None:
    from health_reliability_monitoring.config import Settings

    settings = Settings()
    assert settings.service.name == "health-reliability-monitoring"


@pytest.mark.asyncio
async def test_ccp_pm7_receipt_ingestion_smoke() -> None:
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
        "receipt_id": "00000000-0000-0000-0000-000000000051",
        "gate_id": "ccp-smoke",
        "policy_version_ids": ["pol-1"],
        "snapshot_hash": "sha256:" + "0" * 64,
        "timestamp_utc": "2024-01-01T00:00:00Z",
        "timestamp_monotonic_ms": 123456,
        "evaluation_point": "ccp-smoke",
        "inputs": {"request_id": "req-smoke"},
        "decision": {"status": "pass", "rationale": "ok", "badges": []},
        "actor": {"actor_id": "actor-1", "actor_type": "service"},
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
