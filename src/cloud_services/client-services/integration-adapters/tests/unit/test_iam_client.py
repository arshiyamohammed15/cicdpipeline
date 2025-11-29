"""
Unit tests for IAM client.

What: Test token verification, role checking, tenant extraction
Why: Ensure IAM integration works correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from integrations.iam_client import IAMClient


class TestIAMClient:
    """Test IAMClient."""

    def test_iam_client_initialization(self):
        """Test IAM client initialization."""
        client = IAMClient()
        assert client.base_url is not None

    @patch('integrations.iam_client.httpx.Client')
    def test_verify_token_success(self, mock_client_class):
        """Test successful token verification."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tenant_id": "tenant-123",
            "user_id": "user-456",
            "roles": ["admin"],
        }
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = IAMClient()
        client.client = mock_client
        
        claims = client.verify_token("token-123")
        assert claims is not None
        assert claims["tenant_id"] == "tenant-123"

    @patch('integrations.iam_client.httpx.Client')
    def test_verify_token_failure(self, mock_client_class):
        """Test token verification failure."""
        mock_client = Mock()
        mock_client.post.side_effect = Exception("Invalid token")
        mock_client_class.return_value = mock_client
        
        client = IAMClient()
        client.client = mock_client
        
        claims = client.verify_token("invalid-token")
        assert claims is None

    @patch('integrations.iam_client.httpx.Client')
    def test_get_tenant_id(self, mock_client_class):
        """Test extracting tenant ID from token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tenant_id": "tenant-123"}
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = IAMClient()
        client.client = mock_client
        
        tenant_id = client.get_tenant_id("token-123")
        assert tenant_id == "tenant-123"

    @patch('integrations.iam_client.httpx.Client')
    def test_check_role(self, mock_client_class):
        """Test role checking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"roles": ["admin", "user"]}
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = IAMClient()
        client.client = mock_client
        
        has_role = client.check_role("token-123", "admin")
        assert has_role is True
        
        has_role = client.check_role("token-123", "superadmin")
        assert has_role is False

