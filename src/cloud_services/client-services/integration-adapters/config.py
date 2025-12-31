"""
Configuration management for Integration Adapters Module.

What: Environment variable loading and validation
Why: Centralized configuration
Reads/Writes: Environment variables
Contracts: Standard configuration patterns
Risks: Configuration errors, missing required values
"""

from __future__ import annotations

import os
from typing import Optional


class Config:
    """Configuration for Integration Adapters Module."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Database
        self.DATABASE_URL: str = os.getenv(
            "INTEGRATION_ADAPTERS_DATABASE_URL",
            "sqlite:///./integration_adapters.db"
        )

        # External Services
        self.PM3_SERVICE_URL: str = os.getenv(
            "PM3_SERVICE_URL",
            "http://localhost:8000"
        )

        self.KMS_SERVICE_URL: str = os.getenv(
            "KMS_SERVICE_URL",
            "http://localhost:8000"
        )

        self.BUDGET_SERVICE_URL: str = os.getenv(
            "BUDGET_SERVICE_URL",
            "http://localhost:8000"
        )

        self.ERIS_SERVICE_URL: str = os.getenv(
            "ERIS_SERVICE_URL",
            "http://localhost:8000"
        )

        self.IAM_SERVICE_URL: str = os.getenv(
            "IAM_SERVICE_URL",
            "http://localhost:8000"
        )

        # HTTP Client
        self.HTTP_TIMEOUT: float = float(os.getenv("HTTP_TIMEOUT", "30.0"))
        self.HTTP_MAX_RETRIES: int = int(os.getenv("HTTP_MAX_RETRIES", "3"))

        # Tool schema registry
        self.TOOL_SCHEMA_REGISTRY_PATH: str = os.getenv(
            "INTEGRATION_ADAPTERS_TOOL_SCHEMA_REGISTRY_PATH",
            "config/policies/platform_policy.json",
        )

        # Circuit Breaker
        self.CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = int(
            os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")
        )
        self.CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = int(
            os.getenv("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "2")
        )
        self.CIRCUIT_BREAKER_TIMEOUT: float = float(
            os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60.0")
        )

        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"

        # Environment
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")

    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if valid, False otherwise
        """
        # Add validation logic here
        return True


# Global config instance
config = Config()
