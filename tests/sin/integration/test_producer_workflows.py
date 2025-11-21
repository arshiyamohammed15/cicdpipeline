"""
Integration tests for producer registration workflows.
"""

import pytest
from fastapi.testclient import TestClient

from tests.sin.conftest import (
    SignalEnvelope, SignalKind, Environment, Plane, ProducerRegistration,
    DataContract
)


# Client fixture is provided by tests/sin/integration/conftest.py


# auth_token fixture is provided by tests/sin/integration/conftest.py


def test_producer_registration_workflow(client, auth_token, app_schema_registry):
    """Test complete producer registration workflow."""
    # Step 1: Register contract
    contract = DataContract(
        signal_type="test_signal",
        contract_version="1.0.0",
        required_fields=["event_name"],
        optional_fields=["severity"]
    )
    app_schema_registry.register_contract(
        contract.signal_type,
        contract.contract_version,
        contract.model_dump()
    )

    # Step 2: Register producer
    producer = {
        "producer_id": "producer_workflow",
        "name": "Workflow Producer",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["test_signal"],
        "contract_versions": {"test_signal": "1.0.0"}
    }

    response = client.post(
        "/v1/producers/register",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["producer_id"] == "producer_workflow"
    assert data["status"] == "registered"

    # Step 3: Get producer
    response = client.get(
        "/v1/producers/producer_workflow",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["producer"]["producer_id"] == "producer_workflow"

    # Step 4: Update producer
    producer["name"] = "Updated Workflow Producer"
    response = client.put(
        "/v1/producers/producer_workflow",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"

    # Step 5: Verify update
    response = client.get(
        "/v1/producers/producer_workflow",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["producer"]["name"] == "Updated Workflow Producer"


def test_producer_registration_without_contract(client, auth_token):
    """Test producer registration fails without contract."""
    producer = {
        "producer_id": "producer_no_contract",
        "name": "No Contract Producer",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["missing_signal"],
        "contract_versions": {"missing_signal": "1.0.0"}
    }

    response = client.post(
        "/v1/producers/register",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400  # Bad request - contract not found


def test_producer_registration_duplicate(client, auth_token, app_schema_registry):
    """Test duplicate producer registration."""
    # Register contract
    contract = DataContract(
        signal_type="test_signal",
        contract_version="1.0.0",
        required_fields=["event_name"],
        optional_fields=[]
    )
    app_schema_registry.register_contract(
        contract.signal_type,
        contract.contract_version,
        contract.model_dump()
    )

    producer = {
        "producer_id": "producer_duplicate",
        "name": "Duplicate Producer",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["test_signal"],
        "contract_versions": {"test_signal": "1.0.0"}
    }

    # First registration
    response1 = client.post(
        "/v1/producers/register",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response1.status_code == 201

    # Duplicate registration
    response2 = client.post(
        "/v1/producers/register",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response2.status_code == 400  # Bad request - already registered


def test_producer_update_nonexistent(client, auth_token):
    """Test updating non-existent producer."""
    producer = {
        "producer_id": "producer_nonexistent",
        "name": "Nonexistent Producer",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["test_signal"],
        "contract_versions": {"test_signal": "1.0.0"}
    }

    response = client.put(
        "/v1/producers/producer_nonexistent",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # ProducerRegistryError raises HTTPException with status_code 400
    assert response.status_code == 400  # Bad request - not found


def test_producer_get_nonexistent(client, auth_token):
    """Test getting non-existent producer."""
    response = client.get(
        "/v1/producers/nonexistent",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404  # Not found


def test_producer_registration_multiple_contracts(client, auth_token, app_schema_registry):
    """Test producer registration with multiple contracts."""
    # Register multiple contracts
    contracts = [
        DataContract(
            signal_type="signal_1",
            contract_version="1.0.0",
            required_fields=["event_name"],
            optional_fields=[]
        ),
        DataContract(
            signal_type="signal_2",
            contract_version="1.0.0",
            required_fields=["event_name"],
            optional_fields=[]
        )
    ]

    for contract in contracts:
        app_schema_registry.register_contract(
            contract.signal_type,
            contract.contract_version,
            contract.model_dump()
        )

    producer = {
        "producer_id": "producer_multi_contract",
        "name": "Multi Contract Producer",
        "plane": "edge",
        "owner": "test_owner",
        "allowed_signal_kinds": ["event"],
        "allowed_signal_types": ["signal_1", "signal_2"],
        "contract_versions": {"signal_1": "1.0.0", "signal_2": "1.0.0"}
    }

    response = client.post(
        "/v1/producers/register",
        json={"producer": producer},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201

    # Verify producer can handle both signal types
    response = client.get(
        "/v1/producers/producer_multi_contract",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["producer"]["allowed_signal_types"]) == 2

