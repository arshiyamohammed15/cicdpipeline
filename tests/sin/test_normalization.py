"""Tests for normalization engine."""

import pytest
from datetime import datetime

from tests.sin.conftest import SignalEnvelope, SignalKind, Environment


def test_field_mapping(normalization_engine, mock_schema_registry):
    """Test field name mapping."""
    # Register transformation rules
    mock_schema_registry.register_contract(
        "pr_opened", "1.0.0",
        {
            "field_mappings": {"buildTimeMs": "duration_ms"},
            "unit_conversions": {}
        }
    )

    signal = SignalEnvelope(
        signal_id="signal_1",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={"buildTimeMs": 1000},
        schema_version="1.0.0"
    )

    normalized = normalization_engine.normalize(signal)
    assert "duration_ms" in normalized.payload
    assert "buildTimeMs" not in normalized.payload


def test_unit_normalization(normalization_engine):
    """Test unit normalization."""
    value, converted = normalization_engine.normalize_units(1.0, "s", "ms")
    assert converted
    assert value == 1000.0

