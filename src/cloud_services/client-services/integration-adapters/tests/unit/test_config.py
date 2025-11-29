"""
Unit tests for configuration.

What: Test configuration loading and validation
Why: Ensure configuration works correctly
Coverage Target: 100%
"""

from __future__ import annotations

import pytest
import os
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from config import Config


class TestConfig:
    """Test Config."""

    def test_config_defaults(self):
        """Test configuration default values."""
        config = Config()
        
        assert config.DATABASE_URL is not None
        assert config.PM3_SERVICE_URL is not None
        assert config.KMS_SERVICE_URL is not None
        assert config.HTTP_TIMEOUT == 30.0
        assert config.HTTP_MAX_RETRIES == 3

    def test_config_from_environment(self):
        """Test configuration from environment variables."""
        with patch.dict(os.environ, {
            "INTEGRATION_ADAPTERS_DATABASE_URL": "postgresql://test",
            "PM3_SERVICE_URL": "http://pm3:8000",
            "HTTP_TIMEOUT": "60.0",
        }):
            config = Config()
            assert config.DATABASE_URL == "postgresql://test"
            assert config.PM3_SERVICE_URL == "http://pm3:8000"
            assert config.HTTP_TIMEOUT == 60.0

    def test_config_validation(self):
        """Test configuration validation."""
        config = Config()
        assert config.validate() is True

