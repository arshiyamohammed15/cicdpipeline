"""
Tests for Receipt Generation (RGES) with EPC-11 signing and PM-7 indexing.

Covers PRD section 10.1: Receipt fsync + signature, courier sequence continuity, mutation hooks.
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.shared_libs.cccs.receipts import OfflineCourier, ReceiptConfig, ReceiptService, WALQueue
from src.shared_libs.cccs.types import TraceContext
from src.shared_libs.cccs.exceptions import ReceiptSchemaError
from tests.cccs.mocks import MockEPC11Adapter, MockPM7Adapter


@pytest.fixture(autouse=True)
def patch_receipt_adapters(monkeypatch):
    monkeypatch.setattr(
        "src.shared_libs.cccs.receipts.service.EPC11SigningAdapter",
        MockEPC11Adapter,
    )
    monkeypatch.setattr(
        "src.shared_libs.cccs.receipts.service.PM7ReceiptAdapter",
        MockPM7Adapter,
    )


def _receipt_service(tmp_path: Path) -> ReceiptService:
    storage = tmp_path / "receipts.jsonl"
    config = ReceiptConfig(
        gate_id="gate-1",
        storage_path=storage,
        epc11_base_url="http://localhost:8011",
        epc11_key_id="key-1",
        pm7_base_url="http://localhost:8007",
    )
    courier = OfflineCourier(WALQueue(tmp_path / "wal.log"))
    service = ReceiptService(config, courier)
    return service


def test_receipt_generation_and_hooks(tmp_path):
    """Test receipt generation with before_sign and before_flush hooks."""
    service = _receipt_service(tmp_path)

    hook_calls = []

    service.register_before_sign(lambda receipt: hook_calls.append(("sign", receipt["receipt_id"])))
    service.register_before_flush(lambda receipt: hook_calls.append(("flush", receipt["receipt_id"])))

    trace = TraceContext(
        trace_id="trace",
        span_id="span",
        parent_span_id=None,
        name="unit-test",
        start_time=datetime.now(timezone.utc),
    )

    record = service.write_receipt(
        inputs={"foo": "bar"},
        result={"status": "pass", "rationale": "ok", "badges": []},
        actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
        policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
        trace=trace,
        annotations={"source": "test"},
    )

    assert record.receipt_id
    assert record.courier_batch_id
    assert record.fsync_offset == 1
    assert hook_calls[0][0] == "sign"
    assert hook_calls[1][0] == "flush"


def test_receipt_fsync_and_signature(tmp_path):
    """Test receipt fsync and Ed25519 signature via EPC-11."""
    service = _receipt_service(tmp_path)

    record = service.write_receipt(
        inputs={"test": "data"},
        result={"status": "pass", "rationale": "ok", "badges": []},
        actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
        policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
        trace=None,
    )

    # Verify receipt was written to disk
    receipts_file = tmp_path / "receipts.jsonl"
    assert receipts_file.exists()
    
    # Verify signature is present
    content = receipts_file.read_text()
    assert "signature" in content
    assert record.receipt_id in content


def test_receipt_schema_validation(tmp_path):
    """Test receipt schema validation per receipt-schema-cross-reference.md."""
    service = _receipt_service(tmp_path)

    # Valid receipt
    record = service.write_receipt(
        inputs={},
        result={"status": "pass", "rationale": "ok", "badges": []},
        actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
        policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
        trace=None,
    )
    assert record.receipt_id

    # Invalid decision.status
    with pytest.raises(ReceiptSchemaError, match="Invalid decision.status"):
        service.write_receipt(
            inputs={},
            result={"status": "invalid", "rationale": "ok", "badges": []},
            actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
            policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
            trace=None,
        )


def test_receipt_courier_sequence_continuity(tmp_path):
    """Test courier sequence continuity."""
    service = _receipt_service(tmp_path)

    records = []
    for i in range(5):
        record = service.write_receipt(
            inputs={"index": i},
            result={"status": "pass", "rationale": "ok", "badges": []},
            actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
            policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
            trace=None,
        )
        records.append(record)

    # Verify fsync_offset increments
    assert records[0].fsync_offset == 1
    assert records[4].fsync_offset == 5


def test_receipt_mutation_hook_ordering(tmp_path):
    """Test receipt mutation hook ordering guarantees."""
    service = _receipt_service(tmp_path)

    hook_order = []

    def before_sign_hook(receipt):
        hook_order.append("before_sign")
        receipt["hook_modified"] = "sign"

    def before_flush_hook(receipt):
        hook_order.append("before_flush")
        assert receipt.get("hook_modified") == "sign"

    service.register_before_sign(before_sign_hook)
    service.register_before_flush(before_flush_hook)

    service.write_receipt(
        inputs={},
        result={"status": "pass", "rationale": "ok", "badges": []},
        actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
        policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
        trace=None,
    )

    assert hook_order == ["before_sign", "before_flush"]


def test_courier_dead_letter(tmp_path):
    """Test courier dead_letter receipt emission on failure."""
    service = _receipt_service(tmp_path)
    service.write_receipt(
        inputs={},
        result={"status": "hard_block", "rationale": "fail", "badges": []},
        actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
        policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
        trace=TraceContext(
            trace_id="trace",
            span_id="span",
            parent_span_id=None,
            name="unit-test",
            start_time=datetime.now(timezone.utc),
        ),
    )

    def failing_sink(_payload):
        raise RuntimeError("pm-7 unavailable")

    sequences = service._courier.drain(failing_sink)  # noqa: SLF001 - intentional inspection for test
    assert sequences == []

    wal_contents = (tmp_path / "wal.log").read_text(encoding="utf-8")
    assert "dead_letter" in wal_contents


def test_receipt_deep_copy_inputs(tmp_path):
    """Test receipt service deep-copies inputs to prevent mutation."""
    service = _receipt_service(tmp_path)

    inputs = {"mutable": {"key": "value"}}
    original_value = inputs["mutable"]["key"]

    service.write_receipt(
        inputs=inputs,
        result={"status": "pass", "rationale": "ok", "badges": []},
        actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
        policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
        trace=None,
    )

    # Inputs should not be mutated
    assert inputs["mutable"]["key"] == original_value


def test_receipt_pm7_indexing(tmp_path):
    """Test receipt indexing via PM-7."""
    service = _receipt_service(tmp_path)

    record = service.write_receipt(
        inputs={},
        result={"status": "pass", "rationale": "ok", "badges": []},
        actor={"actor_id": "a", "actor_type": "user", "session_id": "s"},
        policy_metadata={"policy_version_ids": ["1"], "policy_snapshot_hash": "sha256:abc"},
        trace=None,
    )

    # PM-7 indexing should be attempted (non-blocking, non-fatal)
    # In real scenario, would verify PM-7 adapter was called
    assert record.receipt_id


