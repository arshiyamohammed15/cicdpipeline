from __future__ import annotations
"""
Unit tests for PM-3 client.

What: Test SignalEnvelope forwarding to PM-3
Why: Ensure PM-3 integration works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

# Module setup handled by root conftest.py

from integration_adapters.integrations.pm3_client import PM3Client

@pytest.mark.unit
class TestPM3Client:
    """Test PM3Client."""

    @pytest.mark.unit
    def test_pm3_client_initialization(self):
        """Test PM-3 client initialization."""
        client = PM3Client()
        assert client.base_url is not None

    @pytest.mark.unit
    def test_pm3_client_custom_url(self):
        """Test PM-3 client with custom URL."""
        client = PM3Client(base_url="http://custom-pm3:8000")
        assert client.base_url == "http://custom-pm3:8000"

    @patch('integrations.pm3_client.httpx.Client')
    @pytest.mark.unit
    def test_ingest_signal_success(self, mock_client_class):
        """Test successful signal ingestion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = PM3Client()
        client.client = mock_client

        # Create minimal signal envelope
        signal = Mock()
        signal.model_dump.return_value = {"signal_id": "test-123"}

        result = client.ingest_signal(signal)
        assert result is True
        mock_client.post.assert_called_once()

    @patch('integrations.pm3_client.httpx.Client')
    @pytest.mark.unit
    def test_ingest_signal_failure(self, mock_client_class):
        """Test signal ingestion failure."""
        mock_client = Mock()
        mock_client.post.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        client = PM3Client()
        client.client = mock_client

        signal = Mock()
        signal.model_dump.return_value = {"signal_id": "test-123"}

        result = client.ingest_signal(signal)
        assert result is False

    @patch('integrations.pm3_client.httpx.Client')
    @pytest.mark.unit
    def test_ingest_signals_batch(self, mock_client_class):
        """Test batch signal ingestion."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = PM3Client()
        client.client = mock_client

        signals = [Mock() for _ in range(3)]
        for signal in signals:
            signal.model_dump.return_value = {"signal_id": "test"}

        result = client.ingest_signals(signals)
        assert result == 3

