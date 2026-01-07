from __future__ import annotations
"""
Unit tests for budget client.

What: Test budget checking, rate limit checking, usage recording
Why: Ensure EPC-13 integration works correctly
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest
from unittest.mock import Mock, patch

# Module setup handled by root conftest.py

from integration_adapters.integrations.budget_client import BudgetClient

@pytest.mark.unit
class TestBudgetClient:
    """Test BudgetClient."""

    @pytest.mark.unit
    def test_budget_client_initialization(self):
        """Test budget client initialization."""
        client = BudgetClient()
        assert client.base_url is not None

    @patch('integrations.budget_client.httpx.Client')
    @pytest.mark.unit
    def test_check_budget_allowed(self, mock_client_class):
        """Test budget check allows operation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True, "budget_info": {}}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = BudgetClient()
        client.client = mock_client

        allowed, info = client.check_budget("tenant-123", "github", "connection-123", 1.0)
        assert allowed is True

    @patch('integrations.budget_client.httpx.Client')
    @pytest.mark.unit
    def test_check_budget_denied(self, mock_client_class):
        """Test budget check denies operation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": False, "budget_info": {"remaining": 0}}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = BudgetClient()
        client.client = mock_client

        allowed, info = client.check_budget("tenant-123", "github", "connection-123", 1.0)
        assert allowed is False

    @patch('integrations.budget_client.httpx.Client')
    @pytest.mark.unit
    def test_check_budget_fail_open(self, mock_client_class):
        """Test budget check fails open on error."""
        mock_client = Mock()
        mock_client.post.side_effect = Exception("Network error")
        mock_client_class.return_value = mock_client

        client = BudgetClient()
        client.client = mock_client

        allowed, info = client.check_budget("tenant-123", "github", "connection-123", 1.0)
        assert allowed is True  # Fail open
        assert info is None

    @patch('integrations.budget_client.httpx.Client')
    @pytest.mark.unit
    def test_check_rate_limit(self, mock_client_class):
        """Test rate limit checking."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"allowed": True}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = BudgetClient()
        client.client = mock_client

        allowed, info = client.check_rate_limit("tenant-123", "github", "connection-123")
        assert allowed is True

    @patch('integrations.budget_client.httpx.Client')
    @pytest.mark.unit
    def test_record_usage(self, mock_client_class):
        """Test usage recording."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = BudgetClient()
        client.client = mock_client

        result = client.record_usage("tenant-123", "github", "connection-123", 1.0)
        assert result is True

