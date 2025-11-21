"""Tests for producer registry."""

import pytest

from tests.sin.conftest import (
    ProducerRegistration, Plane, SignalKind, ProducerRegistryError
)


def test_producer_registration(producer_registry, sample_producer, sample_contract, mock_schema_registry):
    """Test producer registration."""
    # Register contract first
    mock_schema_registry.register_contract(
        sample_contract.signal_type,
        sample_contract.contract_version,
        sample_contract.model_dump()
    )

    # Register test_failed contract as well (since sample_producer allows it)
    from tests.sin.conftest import DataContract
    test_failed_contract = DataContract(
        signal_type="test_failed",
        contract_version="1.0.0",
        required_fields=["event_name"],
        optional_fields=[]
    )
    mock_schema_registry.register_contract(
        test_failed_contract.signal_type,
        test_failed_contract.contract_version,
        test_failed_contract.model_dump()
    )

    # Register producer
    producer_registry.register_producer(sample_producer)

    # Get producer
    retrieved = producer_registry.get_producer(sample_producer.producer_id)
    assert retrieved is not None
    assert retrieved.producer_id == sample_producer.producer_id


def test_producer_not_found(producer_registry):
    """Test getting non-existent producer."""
    producer = producer_registry.get_producer("nonexistent")
    assert producer is None


def test_signal_type_allowed(producer_registry, registered_producer):
    """Test signal type allowance check."""
    assert producer_registry.is_signal_type_allowed(
        "producer_1", SignalKind.EVENT, "pr_opened"
    )
    assert not producer_registry.is_signal_type_allowed(
        "producer_1", SignalKind.EVENT, "invalid_type"
    )

