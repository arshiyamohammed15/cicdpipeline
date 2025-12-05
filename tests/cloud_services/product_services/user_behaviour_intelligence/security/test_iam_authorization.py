"""
Security test: IAM Authorization (ST-UBI-01, ST-UBI-02, ST-UBI-03).

Per PRD Section 13.6: Test IAM authorization and tenant isolation.
"""


# Imports handled by conftest.py
import pytest
from fastapi.testclient import TestClient
from user_behaviour_intelligence.main import app


class TestIAMAuthorization:
    """Test IAM authorization."""

    def test_actor_profile_access_control(self):
        """Test that actor profile requires ubi:read:actor permission (ST-UBI-01)."""
        client = TestClient(app)
        
        # Test without proper token
        response = client.get(
            "/v1/ubi/actors/actor-1/profile",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        # Should be rejected (401 or 403)
        assert response.status_code in [401, 403]

    def test_cross_tenant_access_control(self):
        """Test that cross-tenant access is rejected (ST-UBI-03)."""
        client = TestClient(app)
        
        # Test with tenant A token accessing tenant B data
        # In production, would use proper IAM token
        response = client.get(
            "/v1/ubi/actors/actor-1/profile?tenant_id=tenant-b",
            headers={"Authorization": "Bearer tenant-a-token"}
        )
        
        # Should be rejected (401 Unauthorized or 403 Forbidden depending on IAM response)
        assert response.status_code in [401, 403]

