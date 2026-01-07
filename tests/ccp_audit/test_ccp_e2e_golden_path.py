from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from shared_libs.cccs import CCCSConfig, CCCSRuntime
from shared_libs.cccs.errors.taxonomy import TaxonomyEntry
from shared_libs.cccs.exceptions import BudgetExceededError
from shared_libs.cccs.identity import IdentityConfig
from shared_libs.cccs.policy import PolicyConfig
from shared_libs.cccs.ratelimit import RateLimiterConfig
from shared_libs.cccs.receipts import ReceiptConfig, ReceiptService
from shared_libs.cccs.redaction import RedactionConfig, RedactionRule
from shared_libs.cccs.types import ActorContext, ConfigLayers
from shared_libs.tool_schema_validation import ToolOutputValidator, ToolSchemaRegistry
from tests.cccs.helpers import SIGNING_SECRET, dependency_health, sign_snapshot
from tests.cccs.mocks import MockEPC1Adapter, MockEPC11Adapter, MockEPC13Adapter, MockPM7Adapter

os.environ.setdefault("USE_REAL_SERVICES", "false")


def _runtime(tmp_path: Path) -> CCCSRuntime:
    config = CCCSConfig(
        mode="edge",
        version="1.0.0",
        identity=IdentityConfig(
            epc1_base_url="http://localhost:8001",
            epc1_timeout_seconds=5.0,
            epc1_api_version="v1",
        ),
        policy=PolicyConfig(
            signing_secrets=[SIGNING_SECRET],
            rule_version_negotiation_enabled=True,
        ),
        config_layers=ConfigLayers(
            local={"ccp_sample": {"feature": True}},
            tenant={"ccp_sample": {"feature": True}},
            product={},
        ),
        receipt=ReceiptConfig(
            gate_id="cccs",
            storage_path=tmp_path / "receipts.jsonl",
            epc11_base_url="http://localhost:8011",
            epc11_key_id="key-1",
            epc11_timeout_seconds=5.0,
            epc11_api_version="v1",
            pm7_base_url="http://localhost:8007",
            pm7_timeout_seconds=5.0,
            pm7_api_version="v1",
        ),
        redaction=RedactionConfig(
            rules=[RedactionRule(field_path="secret", strategy="remove")],
            rule_version_negotiation_enabled=True,
            require_rule_version_match=False,
        ),
        rate_limiter=RateLimiterConfig(
            epc13_base_url="http://localhost:8013",
            epc13_timeout_seconds=5.0,
            epc13_api_version="v1",
            default_deny_on_unavailable=True,
        ),
        taxonomy_mapping={BudgetExceededError: TaxonomyEntry("budget_exceeded", "high", False, "Budget exceeded")},
    )

    with patch("shared_libs.cccs.identity.service.EPC1IdentityAdapter", MockEPC1Adapter), \
        patch("shared_libs.cccs.ratelimit.service.EPC13BudgetAdapter", MockEPC13Adapter), \
        patch("shared_libs.cccs.receipts.service.EPC11SigningAdapter", MockEPC11Adapter), \
        patch("shared_libs.cccs.receipts.service.PM7ReceiptAdapter", MockPM7Adapter):
        runtime = CCCSRuntime(config, wal_path=tmp_path / "wal.log")
    return runtime


@pytest.mark.integration
def test_ccp_e2e_golden_path(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)

    snapshot = {
        "module_id": "ccp-audit",
        "version": "1.0.0",
        "rules": [
            {
                "rule_id": "allow-rule",
                "priority": 1,
                "conditions": {"intent": "allow"},
                "decision": "allow",
                "rationale": "golden-path",
            }
        ],
    }
    runtime.load_policy_snapshot(snapshot, sign_snapshot(snapshot))
    runtime.bootstrap(dependency_health())

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
    validation = validator.validate("tool.sample", {"id": "tool-1", "status": "ok"})
    assert validation.ok is True

    actor_context = ActorContext(
        tenant_id="tenant-1",
        device_id="device-1",
        session_id="session-1",
        user_id="user-1",
        actor_type="human",
        runtime_clock=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    result = runtime.execute_flow(
        module_id="ccp-audit",
        inputs={"intent": "allow", "tool_id": "tool.sample"},
        action_id="ccp-audit",
        cost=1.0,
        config_key="ccp_sample",
        payload={"tool_output": {"id": "tool-1", "status": "ok"}},
        redaction_hint="rules-v1",
        actor_context=actor_context,
    )

    receipt_record = result["receipt"]
    receipts_path = tmp_path / "receipts.jsonl"
    assert receipts_path.exists()

    receipts = [
        json.loads(line)
        for line in receipts_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    receipt = next(item for item in receipts if item.get("receipt_id") == receipt_record.receipt_id)
    for field in ReceiptService.REQUIRED_FIELDS:
        assert field in receipt
    assert receipt["receipt_id"] == receipt_record.receipt_id

    pm7_adapter = runtime._receipts._pm7_adapter  # noqa: SLF001
    assert pm7_adapter is not None
    assert pm7_adapter._indexed_receipts  # noqa: SLF001
    assert pm7_adapter._indexed_receipts[-1]["receipt_id"] == receipt_record.receipt_id  # noqa: SLF001
