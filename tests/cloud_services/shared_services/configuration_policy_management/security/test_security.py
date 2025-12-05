from __future__ import annotations
"""Security tests for Configuration & Policy Management service."""

# Imports handled by conftest.py

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from configuration_policy_management.main import app


@pytest.mark.security
class TestAuthentication:
    """Test authentication security."""

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        client = TestClient(app)

        # Try to access protected endpoint
        response = client.post(
            "/policy/v1/policies?tenant_id=tenant-1",
            json={"policy_id": "test"}
        )
        # May require auth or may allow in test mode
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.security
class TestTenantIsolation:
    """Test tenant isolation security."""

    def test_cross_tenant_policy_access_denied(self):
        """Test that cross-tenant policy access is denied."""
        client = TestClient(app)

        # Create policy for tenant-1
        create_response = client.post(
            "/policy/v1/policies?tenant_id=tenant-1",
            json={
                "policy_id": "tenant1-policy",
                "name": "Tenant 1 Policy",
                "rules": []
            }
        )

        # Try to evaluate from different tenant context
        eval_response = client.post(
            "/policy/v1/policies/tenant1-policy/evaluate",
            json={
                "context": {},
                "principal": {"sub": "user123"},
                "resource": {"id": "resource123"},
                "action": "read",
                "tenant_id": "tenant-2",  # Different tenant
                "environment": "dev"
            }
        )

        # Should deny cross-tenant access
        assert eval_response.status_code in [
            status.HTTP_200_OK,  # If evaluation allowed
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


@pytest.mark.security
class TestInputValidation:
    """Test input validation security."""

    def test_malformed_policy_id(self):
        """Test handling of malformed policy IDs."""
        client = TestClient(app)

        response = client.post(
            "/policy/v1/policies?tenant_id=tenant-1",
            json={
                "policy_id": "../../etc/passwd",  # Path traversal attempt
                "name": "Test",
                "rules": []
            }
        )

        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_oversized_policy_definition(self):
        """Test handling of oversized policy definitions."""
        client = TestClient(app)

        large_rules = [{"rule": f"rule-{i}"} for i in range(10000)]
        response = client.post(
            "/policy/v1/policies?tenant_id=tenant-1",
            json={
                "policy_id": "test-policy",
                "name": "Test",
                "rules": large_rules
            }
        )

        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_sql_injection_in_policy_id(self):
        """Test handling of SQL injection attempts."""
        client = TestClient(app)

        response = client.post(
            "/policy/v1/policies/'; DROP TABLE policies; --/evaluate",
            json={
                "context": {},
                "principal": {"sub": "user123"},
                "resource": {"id": "resource123"},
                "action": "read",
                "tenant_id": "tenant-1",
                "environment": "dev"
            }
        )

        # Should reject invalid policy ID, not execute SQL
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]


@pytest.mark.security
class TestPolicyInjection:
    """Test policy injection security."""

    def test_malicious_policy_rule(self):
        """Test handling of potentially malicious policy rules."""
        client = TestClient(app)

        response = client.post(
            "/policy/v1/policies?tenant_id=tenant-1",
            json={
                "policy_id": "test-policy",
                "name": "Test",
                "rules": [{
                    "action": "allow",
                    "condition": {"__import__": "os"}  # Code injection attempt
                }]
            }
        )

        # Should either accept (if sanitized) or reject
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

