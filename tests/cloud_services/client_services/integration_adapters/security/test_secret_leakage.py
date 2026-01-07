from __future__ import annotations
"""
Security test: Secret Leakage (SEC-IA-01).

What: Ensure logs never contain access tokens or raw secrets
Why: Prevent secret exposure in logs
Coverage Target: All logging paths
"""

# Imports handled by conftest.py

import pytest
import re

# Module setup handled by root conftest.py

from integration_adapters.observability.audit import AuditLogger

@pytest.mark.security
class TestSecretLeakage:
    """Test secret leakage prevention."""

    @pytest.mark.security
    def test_audit_logger_redacts_secrets(self):
        """Test that audit logger redacts secrets."""
        logger = AuditLogger()

        message = 'password="secret123" token="abc123" api_key="key456"'
        redacted = logger._redact_secrets(message)

        assert "secret123" not in redacted
        assert "abc123" not in redacted
        assert "key456" not in redacted
        assert "***REDACTED***" in redacted

    @pytest.mark.security
    def test_audit_logger_redacts_authorization(self):
        """Test that audit logger redacts authorization headers."""
        logger = AuditLogger()

        message = 'authorization="Bearer token123"'
        redacted = logger._redact_secrets(message)

        assert "token123" not in redacted
        assert "***REDACTED***" in redacted

    @pytest.mark.security
    def test_audit_logger_preserves_non_secrets(self):
        """Test that audit logger preserves non-secret data."""
        logger = AuditLogger()

        message = 'user="john" action="create" status="success"'
        redacted = logger._redact_secrets(message)

        assert "john" in redacted
        assert "create" in redacted
        assert "success" in redacted

