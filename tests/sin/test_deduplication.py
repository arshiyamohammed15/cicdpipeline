"""
Tests for deduplication - TC-SIN-004: Duplicate Idempotency, TC-SIN-005: Ordering Semantics.
"""

import pytest
from datetime import datetime

from tests.sin.conftest import SignalEnvelope, SignalKind, Environment


@pytest.mark.unit
def test_tc_sin_004_duplicate_idempotency(deduplication_store):
    """TC-SIN-004: Duplicate signals are idempotent."""
    signal = SignalEnvelope(
        signal_id="signal_1",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened"},
        schema_version="1.0.0"
    )

    # First signal is not duplicate
    assert not deduplication_store.is_duplicate(signal)
    deduplication_store.mark_processed(signal)

    # Second signal with same ID is duplicate
    assert deduplication_store.is_duplicate(signal)


@pytest.mark.unit
def test_tc_sin_005_ordering_semantics(deduplication_store):
    """TC-SIN-005: Ordering semantics per producer."""
    signal1 = SignalEnvelope(
        signal_id="signal_1",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened"},
        schema_version="1.0.0",
        sequence_no=1
    )

    signal2 = SignalEnvelope(
        signal_id="signal_2",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"event_name": "pr_opened"},
        schema_version="1.0.0",
        sequence_no=2
    )

    # Process signal1
    deduplication_store.mark_processed(signal1)

    # signal2 is in order
    in_order, warning = deduplication_store.check_ordering(signal2)
    assert in_order
    assert warning is None

    # signal1 again is out of order
    in_order, warning = deduplication_store.check_ordering(signal1)
    assert not in_order
    assert warning is not None

