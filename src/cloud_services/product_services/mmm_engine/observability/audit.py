"""
Security audit logging for MMM Engine.

Per PRD Section NFR-7, implements security audit logging for all admin mutations
with redacted before/after state.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Separate audit logger
audit_logger = logging.getLogger("mmm_audit")
audit_logger.setLevel(logging.INFO)

# Configure audit log handler (file or external service)
# Lazy initialization to avoid errors if directory doesn't exist
_audit_handler_initialized = False


def _ensure_audit_handler():
    """Ensure audit handler is initialized (lazy initialization)."""
    global _audit_handler_initialized
    if _audit_handler_initialized:
        return

    audit_log_file = os.getenv("MMM_AUDIT_LOG_FILE", "/var/log/mmm_engine/audit.log")
    
    # Create directory if it doesn't exist
    log_dir = os.path.dirname(audit_log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except (OSError, PermissionError):
            # If we can't create the directory, use a fallback location
            audit_log_file = os.path.join(os.getcwd(), "logs", "mmm_engine_audit.log")
            log_dir = os.path.dirname(audit_log_file)
            os.makedirs(log_dir, exist_ok=True)

    try:
        audit_handler = logging.FileHandler(audit_log_file)
        audit_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [AUDIT] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S UTC",
            )
        )
        audit_logger.addHandler(audit_handler)
        _audit_handler_initialized = True
    except (OSError, PermissionError):
        # If file handler fails, use NullHandler (no-op)
        audit_logger.addHandler(logging.NullHandler())
        _audit_handler_initialized = True


class AuditLogger:
    """Security audit logger for admin mutations per PRD NFR-7."""

    @staticmethod
    def _redact_state(state: Any) -> Dict[str, Any]:
        """
        Redact sensitive fields from state before logging.

        Per PRD NFR-7, redacts:
        - actor_id (hash only)
        - email addresses
        - names
        - source code snippets
        """
        if not isinstance(state, dict):
            return {"redacted": "non-dict state"}

        redacted = {}
        for key, value in state.items():
            if key in ["actor_id", "user_id", "email", "name"]:
                # Hash sensitive identifiers
                if isinstance(value, str):
                    import hashlib
                    redacted[key] = f"hash-{hashlib.sha256(value.encode()).hexdigest()[:8]}"
                else:
                    redacted[key] = "[redacted]"
            elif key in ["payload", "content", "body"]:
                # Redact content fields
                redacted[key] = "[content redacted]"
            elif isinstance(value, dict):
                redacted[key] = AuditLogger._redact_state(value)
            elif isinstance(value, list):
                redacted[key] = [AuditLogger._redact_state(item) if isinstance(item, dict) else item for item in value]
            else:
                redacted[key] = value

        return redacted

    @staticmethod
    def log_admin_action(
        admin_user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log admin action to security audit log.

        Per PRD NFR-7:
        - Logs: timestamp, admin_user_id, action, resource_id, before_state (redacted), after_state (redacted)
        - Writes to security audit log file or external audit service
        """
        _ensure_audit_handler()
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "admin_user_id": admin_user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "before_state": AuditLogger._redact_state(before_state) if before_state else None,
            "after_state": AuditLogger._redact_state(after_state) if after_state else None,
        }

        audit_logger.info(json.dumps(audit_entry))

