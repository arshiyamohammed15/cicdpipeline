from __future__ import annotations
"""
Unit tests for KMS client.

What: Test secret retrieval, token refresh
Why: Ensure KMS integration works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from unittest.mock import Mock, patch

# Module setup handled by root conftest.py

from integration_adapters.integrations.kms_client import KMSClient

class TestKMSClient:
    """Test KMSClient."""

    def test_kms_client_initialization(self):
        """Test KMS client initialization."""
        client = KMSClient()
        assert client.base_url is not None

    @patch('integrations.kms_client.httpx.Client')
    def test_get_secret_success(self, mock_client_class):
        """Test successful secret retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"secret_value": "secret-123"}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = KMSClient()
        client.client = mock_client

        secret = client.get_secret("secret-id-123", "tenant-123")
        assert secret == "secret-123"

    @patch('integrations.kms_client.httpx.Client')
    def test_get_secret_failure(self, mock_client_class):
        """Test secret retrieval failure."""
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        client = KMSClient()
        client.client = mock_client

        secret = client.get_secret("secret-id-123", "tenant-123")
        assert secret is None

    @patch('integrations.kms_client.httpx.Client')
    def test_refresh_token_success(self, mock_client_class):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"secret_value": "refreshed-token"}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = KMSClient()
        client.client = mock_client

        token = client.refresh_token("secret-id-123", "tenant-123")
        assert token == "refreshed-token"

