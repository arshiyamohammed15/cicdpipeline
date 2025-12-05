from __future__ import annotations
"""
Unit tests for audit logging.

What: Test structured logging with redaction
Why: Ensure logs are formatted correctly and secrets are redacted
Coverage Target: 100%
"""

# Imports handled by conftest.py

import pytest

# Module setup handled by root conftest.py

from integration_adapters.observability.audit import AuditLogger, get_audit_logger

class TestAuditLogger:
    """Test AuditLogger."""

    def test_audit_logger_initialization(self):
        """Test audit logger initialization."""
        logger = AuditLogger()
        assert logger is not None

    def test_redact_secrets_password(self):
        """Test redacting password from logs."""
        logger = AuditLogger()

        message = 'password="secret123"'
        redacted = logger._redact_secrets(message)

        assert "secret123" not in redacted
        assert "***REDACTED***" in redacted

    def test_redact_secrets_token(self):
        """Test redacting token from logs."""
        logger = AuditLogger()

        message = 'token="abc123"'
        redacted = logger._redact_secrets(message)

        assert "abc123" not in redacted

    def test_redact_secrets_api_key(self):
        """Test redacting API key from logs."""
        logger = AuditLogger()

        message = 'api_key="key456"'
        redacted = logger._redact_secrets(message)

        assert "key456" not in redacted

    def test_preserve_non_secrets(self):
        """Test preserving non-secret data."""
        logger = AuditLogger()

        message = 'user="john" action="create"'
        redacted = logger._redact_secrets(message)

        assert "john" in redacted
        assert "create" in redacted

    def test_log_webhook_received(self):
        """Test logging webhook received event."""
        logger = AuditLogger()

        # Should not raise exception
        logger.log_webhook_received(
            "github",
            "connection-123",
            "tenant-123",
            "pull_request",
            "correlation-456",
        )

    def test_log_event_normalized(self):
        """Test logging event normalization."""
        logger = AuditLogger()

        logger.log_event_normalized(
            "github",
            "connection-123",
            "tenant-123",
            "pr_opened",
            "signal-789",
        )

    def test_log_action_executed(self):
        """Test logging action execution."""
        logger = AuditLogger()

        logger.log_action_executed(
            "github",
            "connection-123",
            "tenant-123",
            "comment_on_pr",
            "action-123",
            "completed",
            "correlation-456",
        )

    def test_log_error(self):
        """Test logging error event."""
        logger = AuditLogger()

        logger.log_error(
            "github",
            "connection-123",
            "tenant-123",
            "network",
            'Error: password="secret"',
            "correlation-456",
        )

    def test_get_global_logger(self):
        """Test getting global audit logger."""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()

        assert logger1 is logger2

