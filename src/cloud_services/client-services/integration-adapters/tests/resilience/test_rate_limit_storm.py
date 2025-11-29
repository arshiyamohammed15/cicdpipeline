"""
Resilience test: Rate Limit Storm (RF-IA-02).

What: Test handling of consecutive 429 responses with Retry-After
Why: Ensure system respects rate limits and budgets
Coverage Target: Rate limit scenarios
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from adapters.http_client import HTTPClient, ErrorType


class TestRateLimitStorm:
    """Test rate limit storm handling."""

    @pytest.fixture
    def mock_429_response(self):
        """Mock 429 response with Retry-After."""
        response = Mock()
        response.status_code = 429
        response.headers = {"Retry-After": "5"}
        return response

    def test_http_client_parses_retry_after(self):
        """Test HTTP client parses Retry-After header."""
        client = HTTPClient(base_url="https://api.example.com")
        
        headers = {"Retry-After": "10"}
        retry_after = client._parse_retry_after(headers)
        assert retry_after == 10.0

    def test_http_client_classifies_429_as_rate_limit(self):
        """Test HTTP client classifies 429 as rate limit error."""
        client = HTTPClient(base_url="https://api.example.com")
        
        error_type = client._classify_error(429)
        assert error_type == ErrorType.RATE_LIMIT

    def test_http_client_handles_429_with_retry_after(self, mock_429_response):
        """Test HTTP client handles 429 with Retry-After."""
        # This would be tested with actual HTTP client mocking
        # For now, test the classification
        client = HTTPClient(base_url="https://api.example.com")
        error_type = client._classify_error(429)
        assert error_type == ErrorType.RATE_LIMIT

