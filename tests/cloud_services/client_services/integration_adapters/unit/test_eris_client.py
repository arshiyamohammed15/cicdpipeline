from __future__ import annotations
"""
Unit tests for ERIS client.

What: Test receipt emission to ERIS
Why: Ensure ERIS integration works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from unittest.mock import Mock, patch

# Module setup handled by root conftest.py

from integration_adapters.integrations.eris_client import ERISClient

@pytest.mark.unit
class TestERISClient:
    """Test ERISClient."""

    @pytest.mark.unit
    def test_eris_client_initialization(self):
        """Test ERIS client initialization."""
        client = ERISClient()
        assert client.base_url is not None

    @patch('integrations.eris_client.httpx.Client')
    @pytest.mark.unit
    def test_emit_receipt_success(self, mock_client_class):
        """Test successful receipt emission."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = ERISClient()
        client.client = mock_client

        result = client.emit_receipt(
            tenant_id="tenant-123",
            connection_id="connection-123",
            provider_id="github",
            operation_type="integration.action.github.create_comment",
            request_metadata={"target": {}},
            result={"status": "success"},
            correlation_id="correlation-456",
        )
        assert result is True

    @patch('integrations.eris_client.httpx.Client')
    @pytest.mark.unit
    def test_emit_receipt_failure(self, mock_client_class):
        """Test receipt emission failure."""
        mock_client = Mock()
        mock_client.post.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        client = ERISClient()
        client.client = mock_client

        result = client.emit_receipt(
            tenant_id="tenant-123",
            connection_id="connection-123",
            provider_id="github",
            operation_type="test",
            request_metadata={},
            result={},
        )
        assert result is False

    @patch('integrations.eris_client.httpx.Client')
    @pytest.mark.unit
    def test_emit_receipts_batch(self, mock_client_class):
        """Test batch receipt emission."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = ERISClient()
        client.client = mock_client

        receipts = [{"tenant_id": "tenant-123", "operation_type": "test"} for _ in range(3)]
        result = client.emit_receipts(receipts)
        assert result == 3

