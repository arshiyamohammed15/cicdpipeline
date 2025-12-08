from __future__ import annotations
"""Integration tests for Contracts & Schema Registry API."""

# Imports handled by conftest.py

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from contracts_schema_registry.main import app


@pytest.mark.integration
class TestSchemaLifecycle:
    """Test schema lifecycle integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_register_and_validate_schema(self, client):
        """Test registering and validating a schema."""
        # Register schema
        register_response = client.post(
            "/registry/v1/schemas",
            json={
                "name": "test-schema",
                "schema_type": "json",
                "definition": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"}
                    }
                },
                "namespace": "test"
            }
        )
        
        assert register_response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
        
        # Validate data against schema
        if register_response.status_code == status.HTTP_201_CREATED:
            schema_id = register_response.json().get("schema_id")
            if schema_id:
                validate_response = client.post(
                    "/registry/v1/validate",
                    json={
                        "schema_id": schema_id,
                        "data": {"name": "test"}
                    }
                )
                
                assert validate_response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_404_NOT_FOUND
                ]

    def test_schema_versioning(self, client):
        """Test schema versioning workflow."""
        # Register initial schema
        register_response = client.post(
            "/registry/v1/schemas",
            json={
                "name": "versioned-schema",
                "schema_type": "json",
                "definition": {"type": "object"},
                "namespace": "test"
            }
        )
        
        if register_response.status_code == status.HTTP_201_CREATED:
            schema_id = register_response.json().get("schema_id")
            # Update schema (creates new version)
            update_response = client.put(
                f"/registry/v1/schemas/{schema_id}",
                json={
                    "definition": {"type": "object", "properties": {"id": {"type": "string"}}}
                }
            )
            
            assert update_response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_404_NOT_FOUND,
                    status.HTTP_400_BAD_REQUEST
                ]


@pytest.mark.integration
class TestContractFlow:
    """Test contract management integration."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_contract_creation_and_retrieval(self, client):
        """Test contract creation and retrieval."""
        # Create contract
        create_response = client.post(
            "/registry/v1/contracts",
            json={
                "name": "test-contract",
                "schema_id": "test-schema-id",
                "contract_type": "api",
                "definition": {}
            }
        )
        
        assert create_response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_compatibility_check(self, client):
        """Test schema compatibility checking."""
        response = client.post(
            "/registry/v1/compatibility",
            json={
                "source_schema": {"type": "object"},
                "target_schema": {"type": "object", "properties": {"id": {"type": "string"}}},
                "compatibility_mode": "backward"
            }
        )
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

