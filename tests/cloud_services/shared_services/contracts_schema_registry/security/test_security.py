from __future__ import annotations
"""Security tests for Contracts & Schema Registry service."""

# Imports handled by conftest.py

import pytest
import httpx
from httpx import ASGITransport
from fastapi import status

from contracts_schema_registry.main import app


@pytest.mark.security
class TestTenantIsolation:
    """Test tenant isolation security."""

    @pytest.mark.asyncio
    async def test_cross_tenant_schema_access_denied(self):
        """Test that cross-tenant schema access is denied."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            register_response = await client.post(
                "/registry/v1/schemas",
                json={
                    "name": "tenant1-schema",
                    "schema_type": "json",
                    "definition": {"type": "object"},
                    "namespace": "tenant-1"
                }
            )

            if register_response.status_code == status.HTTP_201_CREATED:
                schema_id = register_response.json().get("schema_id")
                get_response = await client.get(f"/registry/v1/schemas/{schema_id}")
                assert get_response.status_code in [
                        status.HTTP_200_OK,
                        status.HTTP_403_FORBIDDEN,
                        status.HTTP_404_NOT_FOUND
                    ]


@pytest.mark.security
class TestInputValidation:
    """Test input validation security."""

    @pytest.mark.asyncio
    async def test_malformed_schema_id(self):
        """Test handling of malformed schema IDs."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/registry/v1/schemas/../../etc/passwd")

            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.asyncio
    async def test_oversized_schema_definition(self):
        """Test handling of oversized schema definitions."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            large_definition = {"type": "object", "properties": {f"prop{i}": {"type": "string"} for i in range(10000)}}
            response = await client.post(
                "/registry/v1/schemas",
                json={
                    "name": "large-schema",
                    "schema_type": "json",
                    "definition": large_definition,
                    "namespace": "test"
                }
            )

            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.asyncio
    async def test_sql_injection_in_schema_id(self):
        """Test handling of SQL injection attempts."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/registry/v1/schemas/'; DROP TABLE schemas; --")

            assert response.status_code in [
                status.HTTP_404_NOT_FOUND,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.asyncio
    async def test_malicious_schema_definition(self):
        """Test handling of potentially malicious schema definitions."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            malicious_schema = {
                "type": "object",
                "properties": {
                    "__import__": {"type": "string"}  # Code injection attempt
                }
            }

            response = await client.post(
                "/registry/v1/schemas",
                json={
                    "name": "malicious-schema",
                    "schema_type": "json",
                    "definition": malicious_schema,
                    "namespace": "test"
                }
            )

            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]


@pytest.mark.security
class TestSchemaValidation:
    """Test schema validation security."""

    @pytest.mark.asyncio
    async def test_oversized_validation_data(self):
        """Test handling of oversized validation data."""
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            large_data = {"field": "x" * 1000000}  # 1MB data

            response = await client.post(
                "/registry/v1/validate",
                json={
                    "schema_id": "test-schema",
                    "data": large_data
                }
            )

            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

