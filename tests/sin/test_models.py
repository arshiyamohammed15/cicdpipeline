"""
Tests for SIN module models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

# Import from conftest
import tests.sin.conftest as conftest

SignalEnvelope = conftest.SignalEnvelope
SignalKind = conftest.SignalKind
Environment = conftest.Environment
ProducerRegistration = conftest.ProducerRegistration
Plane = conftest.Plane
DataContract = conftest.DataContract


def test_signal_envelope_creation(sample_signal):
    """Test SignalEnvelope creation."""
    assert sample_signal.signal_id == "signal_123"
    assert sample_signal.tenant_id == "tenant_1"
    assert sample_signal.signal_kind == SignalKind.EVENT


def test_signal_envelope_validation():
    """Test SignalEnvelope validation."""
    # Valid signal
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
    assert signal.signal_id == "signal_1"

    # Missing required field
    with pytest.raises(ValidationError):
        SignalEnvelope(
            tenant_id="tenant_1",
            environment=Environment.DEV,
            producer_id="producer_1",
            signal_kind=SignalKind.EVENT,
            signal_type="pr_opened",
            occurred_at=datetime.utcnow(),
            ingested_at=datetime.utcnow(),
            payload={},
            schema_version="1.0.0"
        )


def test_producer_registration():
    """Test ProducerRegistration model."""
    producer = ProducerRegistration(
        producer_id="producer_1",
        name="Test Producer",
        plane=Plane.EDGE,
        owner="test_owner",
        allowed_signal_kinds=[SignalKind.EVENT],
        allowed_signal_types=["pr_opened"],
        contract_versions={"pr_opened": "1.0.0"}
    )
    assert producer.producer_id == "producer_1"
    assert producer.plane == Plane.EDGE


def test_data_contract():
    """Test DataContract model."""
    contract = DataContract(
        signal_type="pr_opened",
        contract_version="1.0.0",
        required_fields=["event_name"],
        optional_fields=["severity"]
    )
    assert contract.signal_type == "pr_opened"
    assert "event_name" in contract.required_fields

