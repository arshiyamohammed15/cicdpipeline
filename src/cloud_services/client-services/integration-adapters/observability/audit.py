"""
Audit logging for Integration Adapters Module.

What: Structured logging with correlation IDs, tenant tagging per FR-12
Why: Audit trail and debugging
Reads/Writes: Logs (structured JSON)
Contracts: PRD FR-12 (Observability & Diagnostics), FR-15 (Security & Privacy)
Risks: PII/secrets in logs, log volume
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Structured audit logger with redaction.
    
    Redacts secrets and PII before logging per FR-15.
    """

    # Patterns for secret detection
    SECRET_PATTERNS = [
        r"password['\"]?\s*[:=]\s*['\"]?([^'\"]+)",
        r"token['\"]?\s*[:=]\s*['\"]?([^'\"]+)",
        r"secret['\"]?\s*[:=]\s*['\"]?([^'\"]+)",
        r"api[_-]?key['\"]?\s*[:=]\s*['\"]?([^'\"]+)",
        r"authorization['\"]?\s*[:=]\s*['\"]?([^'\"]+)",
    ]

    def __init__(self):
        """Initialize audit logger."""
        self.logger = logging.getLogger("integration_adapters.audit")

    def log_webhook_received(
        self,
        provider_id: str,
        connection_id: str,
        tenant_id: str,
        event_type: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Log webhook received event.
        
        Args:
            provider_id: Provider identifier
            connection_id: Connection ID
            tenant_id: Tenant ID
            event_type: Event type
            correlation_id: Optional correlation ID
        """
        self.logger.info(
            json.dumps({
                "event": "webhook_received",
                "provider_id": provider_id,
                "connection_id": connection_id,
                "tenant_id": tenant_id,
                "event_type": event_type,
                "correlation_id": correlation_id,
            })
        )

    def log_event_normalized(
        self,
        provider_id: str,
        connection_id: str,
        tenant_id: str,
        signal_type: str,
        signal_id: str,
    ) -> None:
        """
        Log event normalization.
        
        Args:
            provider_id: Provider identifier
            connection_id: Connection ID
            tenant_id: Tenant ID
            signal_type: Canonical signal type
            signal_id: Signal ID
        """
        self.logger.info(
            json.dumps({
                "event": "event_normalized",
                "provider_id": provider_id,
                "connection_id": connection_id,
                "tenant_id": tenant_id,
                "signal_type": signal_type,
                "signal_id": signal_id,
            })
        )

    def log_action_executed(
        self,
        provider_id: str,
        connection_id: str,
        tenant_id: str,
        action_type: str,
        action_id: str,
        status: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Log action execution.
        
        Args:
            provider_id: Provider identifier
            connection_id: Connection ID
            tenant_id: Tenant ID
            action_type: Action type
            action_id: Action ID
            status: Execution status
            correlation_id: Optional correlation ID
        """
        self.logger.info(
            json.dumps({
                "event": "action_executed",
                "provider_id": provider_id,
                "connection_id": connection_id,
                "tenant_id": tenant_id,
                "action_type": action_type,
                "action_id": action_id,
                "status": status,
                "correlation_id": correlation_id,
            })
        )

    def log_error(
        self,
        provider_id: str,
        connection_id: str,
        tenant_id: str,
        error_type: str,
        error_message: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Log error event.
        
        Args:
            provider_id: Provider identifier
            connection_id: Connection ID
            tenant_id: Tenant ID
            error_type: Error type (auth, network, provider, config)
            error_message: Error message (redacted)
            correlation_id: Optional correlation ID
        """
        redacted_message = self._redact_secrets(error_message)
        self.logger.error(
            json.dumps({
                "event": "error",
                "provider_id": provider_id,
                "connection_id": connection_id,
                "tenant_id": tenant_id,
                "error_type": error_type,
                "error_message": redacted_message,
                "correlation_id": correlation_id,
            })
        )

    def _redact_secrets(self, text: str) -> str:
        """
        Redact secrets from text per FR-15.
        
        Args:
            text: Text to redact
            
        Returns:
            Redacted text
        """
        redacted = text
        for pattern in self.SECRET_PATTERNS:
            # Replace the captured secret value with REDACTED
            redacted = re.sub(pattern, lambda m: m.group(0).replace(m.group(1), "***REDACTED***"), redacted, flags=re.IGNORECASE)
        return redacted


# Global audit logger
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance."""
    return _audit_logger

