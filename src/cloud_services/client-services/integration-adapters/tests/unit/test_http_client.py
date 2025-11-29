"""
Unit tests for HTTP client with retries and rate limiting.

What: Test retry logic, backoff, rate limit handling, error classification
Why: Ensure HTTP client handles failures correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
import time
from unittest.mock import Mock, patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from adapters.http_client import HTTPClient, ErrorType


class TestHTTPClient:
    """Test HTTP client."""

    def test_http_client_initialization(self):
        """Test HTTP client initialization."""
        client = HTTPClient(base_url="https://api.example.com")
        assert client.base_url == "https://api.example.com"
        assert client.max_retries == 3
        assert client.initial_backoff == 1.0

    def test_backoff_calculation(self):
        """Test exponential backoff calculation."""
        client = HTTPClient(base_url="https://api.example.com")
        
        backoff1 = client._calculate_backoff(0)
        backoff2 = client._calculate_backoff(1)
        backoff3 = client._calculate_backoff(2)
        
        assert backoff1 < backoff2 < backoff3
        assert backoff1 >= client.initial_backoff
        assert backoff3 <= client.max_backoff

    def test_backoff_with_jitter(self):
        """Test backoff includes jitter."""
        client = HTTPClient(base_url="https://api.example.com", jitter=True)
        
        backoffs = [client._calculate_backoff(1) for _ in range(10)]
        # Jitter should add variation
        assert len(set(backoffs)) > 1

    def test_backoff_without_jitter(self):
        """Test backoff without jitter is deterministic."""
        client = HTTPClient(base_url="https://api.example.com", jitter=False)
        
        backoff1 = client._calculate_backoff(1)
        backoff2 = client._calculate_backoff(1)
        
        assert backoff1 == backoff2

    def test_parse_retry_after_header(self):
        """Test parsing Retry-After header."""
        client = HTTPClient(base_url="https://api.example.com")
        
        headers = {"Retry-After": "5"}
        retry_after = client._parse_retry_after(headers)
        assert retry_after == 5.0
        
        headers_no_retry = {}
        retry_after = client._parse_retry_after(headers_no_retry)
        assert retry_after is None

    def test_error_classification(self):
        """Test error classification."""
        client = HTTPClient(base_url="https://api.example.com")
        
        assert client._classify_error(429) == ErrorType.RATE_LIMIT
        assert client._classify_error(400) == ErrorType.CLIENT
        assert client._classify_error(404) == ErrorType.CLIENT
        assert client._classify_error(408) == ErrorType.RATE_LIMIT
        assert client._classify_error(500) == ErrorType.SERVER
        assert client._classify_error(503) == ErrorType.SERVER

    @patch('adapters.http_client.httpx.Client')
    def test_request_success(self, mock_client_class):
        """Test successful request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = HTTPClient(base_url="https://api.example.com")
        client.client = mock_client
        
        response = client.request("GET", "/test")
        assert response.status_code == 200
        mock_client.request.assert_called_once()

    @patch('adapters.http_client.httpx.Client')
    def test_request_retry_on_server_error(self, mock_client_class):
        """Test retry on server error."""
        mock_response_500 = Mock()
        mock_response_500.status_code = 500
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.request.side_effect = [mock_response_500, mock_response_200]
        mock_client_class.return_value = mock_client
        
        client = HTTPClient(base_url="https://api.example.com", max_retries=1)
        client.client = mock_client
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = client.request("GET", "/test")
            assert response.status_code == 200
            assert mock_client.request.call_count == 2

    @patch('adapters.http_client.httpx.Client')
    def test_request_no_retry_on_client_error(self, mock_client_class):
        """Test no retry on client error (4xx)."""
        mock_response = Mock()
        mock_response.status_code = 400
        
        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = HTTPClient(base_url="https://api.example.com")
        client.client = mock_client
        
        response = client.request("GET", "/test")
        assert response.status_code == 400
        mock_client.request.assert_called_once()

    @patch('adapters.http_client.httpx.Client')
    def test_request_idempotency_key(self, mock_client_class):
        """Test idempotency key injection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        
        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        client = HTTPClient(base_url="https://api.example.com")
        client.client = mock_client
        
        client.request("POST", "/test", idempotency_key="key-123")
        
        call_args = mock_client.request.call_args
        assert "Idempotency-Key" in call_args[1]["headers"]
        assert call_args[1]["headers"]["Idempotency-Key"] == "key-123"

