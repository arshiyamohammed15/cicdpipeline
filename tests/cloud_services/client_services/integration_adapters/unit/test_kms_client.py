from __future__ import annotations
"""
Unit tests for KMS client.

What: Test secret retrieval, token refresh
Why: Ensure KMS integration works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from unittest.mock import Mock

# Module setup handled by root conftest.py

from integration_adapters.integrations.kms_client import KMSClient

pytestmark = pytest.mark.filterwarnings("ignore::ResourceWarning")

@pytest.mark.unit
class TestKMSClient:
    """Test KMSClient."""

    @pytest.mark.unit
    def test_kms_client_initialization(self):
        """Test KMS client initialization."""
        client = KMSClient()
        assert client.base_url is not None
        client.close()

    @pytest.mark.unit
    def test_get_secret_success(self):
        """Test successful secret retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"secret_value": "secret-123"}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get.return_value = mock_response

        client = KMSClient.__new__(KMSClient)
        client.base_url = "http://kms.test"
        client.client = mock_client

        secret = client.get_secret("secret-id-123", "tenant-123")
        assert secret == "secret-123"
        client.close()

    @pytest.mark.unit
    def test_get_secret_failure(self):
        """Test secret retrieval failure."""
        mock_client = Mock()
        mock_client.get.side_effect = Exception("Network error")

        client = KMSClient.__new__(KMSClient)
        client.base_url = "http://kms.test"
        client.client = mock_client

        secret = client.get_secret("secret-id-123", "tenant-123")
        assert secret is None
        client.close()

    @pytest.mark.unit
    def test_refresh_token_success(self):
        """Test successful token refresh."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"secret_value": "refreshed-token"}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response

        client = KMSClient.__new__(KMSClient)
        client.base_url = "http://kms.test"
        client.client = mock_client

        token = client.refresh_token("secret-id-123", "tenant-123")
        assert token == "refreshed-token"
        client.close()

