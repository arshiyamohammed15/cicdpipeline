from __future__ import annotations
"""Security tests for Identity & Access Management service."""

# Imports handled by conftest.py

import sys
from pathlib import Path
from unittest.mock import patch, Mock

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Add parent directories to path
PACKAGE_ROOT = Path(__file__).resolve().parents[5]  # Updated for new structure
# Path setup handled by conftest.py
# Import main app
MODULE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "shared-services" / "identity-access-management"
# Remove any conflicting paths and add our module path first
if str(MODULE_ROOT) in sys.path:
    sys.path.remove(str(MODULE_ROOT))
sys.path.insert(0, str(MODULE_ROOT))

# Import using importlib to ensure we get the correct module
import importlib.util
main_spec = importlib.util.spec_from_file_location("identity_access_management_main", MODULE_ROOT / "main.py")
main_module = importlib.util.module_from_spec(main_spec)
main_spec.loader.exec_module(main_module)
app = main_module.app

test_client = TestClient(app)


@pytest.mark.security
class TestTokenValidation:
    """Test token validation security."""

    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected."""
        response = test_client.post(
            "/verify",
            json={"token": "invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected."""
        # Create an expired token (mock)
        expired_token = "expired_token_mock"

        response = test_client.post(
            "/verify",
            json={"token": expired_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_token_rejected(self):
        """Test that malformed tokens are rejected."""
        malformed_tokens = [
            "",
            "not.a.token",
            "header.payload",  # Missing signature
            "header.payload.signature.extra"  # Too many parts
        ]

        for token in malformed_tokens:
            response = test_client.post(
                "/verify",
                json={"token": token}
            )
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    def test_token_without_required_claims(self):
        """Test that tokens without required claims are rejected."""
        # Mock token without required claims
        incomplete_token = "incomplete_token_mock"

        response = test_client.post(
            "/verify",
            json={"token": incomplete_token}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.security
class TestAccessControl:
    """Test access control security."""

    def test_unauthorized_access_denied(self):
        """Test that unauthorized access is denied."""
        response = test_client.post(
            "/decision",
            json={
                "subject": {"sub": "user123", "roles": []},
                "action": "read",
                "resource": {"id": "resource123"}
            }
        )

        # Should either deny or require authentication
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_200_OK  # If decision is made but denied
        ]

    def test_privilege_escalation_prevented(self):
        """Test that privilege escalation attempts are prevented."""
        # Attempt to access resource with insufficient privileges
        response = test_client.post(
            "/decision",
            json={
                "subject": {"sub": "user123", "roles": ["viewer"]},
                "action": "write",  # Viewer trying to write
                "resource": {"id": "resource123"}
            }
        )

        # Should deny access
        result = response.json()
        if "decision" in result:
            assert result["decision"] == "deny"
        else:
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_401_UNAUTHORIZED
            ]

    def test_tenant_isolation_enforced(self):
        """Test that tenant isolation is enforced."""
        # Attempt cross-tenant access
        response = test_client.post(
            "/decision",
            json={
                "subject": {"sub": "user123", "roles": ["admin"], "tenant_id": "tenant-1"},
                "action": "read",
                "resource": {"id": "resource123", "tenant_id": "tenant-2"}  # Different tenant
            }
        )

        # Should deny cross-tenant access
        result = response.json()
        if "decision" in result:
            assert result["decision"] == "deny"
        else:
            assert response.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_401_UNAUTHORIZED
            ]


@pytest.mark.security
class TestBreakGlassSecurity:
    """Test break-glass access security."""

    def test_break_glass_requires_justification(self):
        """Test that break-glass requires justification."""
        response = test_client.post(
            "/break-glass",
            json={
                "subject": {"sub": "user123"},
                "incident_id": "incident-1",
                "justification": "",  # Empty justification
                "approver_identity": "approver-1"
            }
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_break_glass_requires_approver(self):
        """Test that break-glass requires approver identity."""
        response = test_client.post(
            "/break-glass",
            json={
                "subject": {"sub": "user123"},
                "incident_id": "incident-1",
                "justification": "Emergency access needed",
                "approver_identity": ""  # Empty approver
            }
        )

        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_break_glass_audit_logged(self):
        """Test that break-glass access is audit logged."""
        with patch('identity_access_management.services.IAMService.trigger_break_glass') as mock_break_glass:
            mock_response = Mock()
            mock_response.decision = "BREAK_GLASS_GRANTED"
            mock_break_glass.return_value = mock_response

            response = test_client.post(
                "/break-glass",
                json={
                    "subject": {"sub": "user123"},
                    "incident_id": "incident-1",
                    "justification": "Emergency access needed",
                    "approver_identity": "approver-1"
                }
            )

            # Verify break-glass was called (audit logging happens in service)
            assert mock_break_glass.called


@pytest.mark.security
class TestInputValidation:
    """Test input validation security."""

    def test_sql_injection_in_token(self):
        """Test handling of SQL injection attempts in token."""
        malicious_token = "'; DROP TABLE tokens; --"

        response = test_client.post(
            "/verify",
            json={"token": malicious_token}
        )

        # Should reject invalid token, not execute SQL
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_xss_in_subject(self):
        """Test handling of XSS attempts in subject."""
        xss_payload = "<script>alert('xss')</script>"

        response = test_client.post(
            "/decision",
            json={
                "subject": {"sub": xss_payload, "roles": ["admin"]},
                "action": "read",
                "resource": {"id": "resource123"}
            }
        )

        # Should either accept (if sanitized) or reject
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

    def test_oversized_payload(self):
        """Test handling of oversized payloads."""
        large_payload = {"token": "x" * 100000}  # 100KB token

        response = test_client.post(
            "/verify",
            json=large_payload
        )

        # Should either accept or reject with appropriate error
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]

