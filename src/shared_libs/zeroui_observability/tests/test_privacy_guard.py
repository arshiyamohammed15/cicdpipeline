"""
Tests for Privacy Guard processor (OBS-06).

Tests redaction enforcement, violation detection, and audit event emission.
"""

import json
import unittest
from datetime import datetime

from ..collector.processors.privacy_guard.privacy_guard_processor import (
    PrivacyGuardProcessor,
    PrivacyCheckResult,
)
from ..contracts.event_types import EventType


class TestPrivacyGuard(unittest.TestCase):
    """Test Privacy Guard processor."""

    def setUp(self):
        """Set up Privacy Guard processor."""
        self.processor = PrivacyGuardProcessor(enabled=True)

    def test_check_privacy_safe_payload(self):
        """Test privacy check on safe payload (metadata-only)."""
        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.PERF_SAMPLE.value,
            "severity": "info",
            "source": {"component": "backend", "channel": "backend"},
            "correlation": {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"},
            "payload": {
                "operation": "decision",
                "latency_ms": 150,
                "component": "backend",
                "channel": "backend",
                "redaction_applied": True,
            },
        }
        result = self.processor.check_privacy(event)
        self.assertTrue(result.is_safe)
        self.assertIsNone(result.violation_type)

    def test_check_privacy_unsafe_payload(self):
        """Test privacy check on unsafe payload (deny-listed content)."""
        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.ERROR_CAPTURED.value,
            "severity": "error",
            "source": {"component": "backend", "channel": "backend"},
            "correlation": {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"},
            "payload": {
                "error_class": "security",
                "error_code": "ERR_SEC_001",
                "stage": "validation",
                "message_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
                "input_fingerprint": "b4g6f9c2d5e7a8f0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6",
                "output_fingerprint": "c5h7g0d3e6f8b9g1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5",
                "internal_state_fingerprint": "d6i8h1e4f7g9c0h2d4e6f8g0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8",
                "component": "backend",
                "channel": "backend",
                "api_key": "REDACTED_KEY_PLACEHOLDER",  # Deny-listed field
                "redaction_applied": False,
            },
        }
        result = self.processor.check_privacy(event)
        self.assertFalse(result.is_safe)
        self.assertIsNotNone(result.violation_type)

    def test_check_privacy_missing_redaction_flag(self):
        """Test privacy check on payload without redaction_applied flag."""
        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.PERF_SAMPLE.value,
            "severity": "info",
            "source": {"component": "backend", "channel": "backend"},
            "correlation": {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"},
            "payload": {
                "operation": "decision",
                "latency_ms": 150,
                "component": "backend",
                "channel": "backend",
                # Missing redaction_applied
            },
        }
        result = self.processor.check_privacy(event)
        # Should trigger audit event even if safe
        self.assertTrue(result.should_emit_audit)

    def test_create_audit_event(self):
        """Test creation of privacy.audit.v1 event."""
        original_event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.ERROR_CAPTURED.value,
            "severity": "error",
            "source": {"component": "backend", "channel": "backend"},
            "correlation": {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"},
            "payload": {
                "error_class": "security",
                "api_key": "REDACTED_KEY_PLACEHOLDER",
            },
        }
        check_result = PrivacyCheckResult(
            is_safe=False,
            violation_type="deny_listed_fields",
            blocked_fields=["api_key"],
            policy_version="v1.0",
            should_emit_audit=True,
        )
        audit_event = self.processor.create_audit_event(original_event, check_result)
        self.assertEqual(audit_event["event_type"], EventType.PRIVACY_AUDIT.value)
        self.assertEqual(audit_event["payload"]["violation_type"], "deny_listed_fields")
        self.assertIn("api_key", audit_event["payload"]["blocked_fields"])

    def test_process_log_record_safe(self):
        """Test processing safe log record."""
        log_record = {
            "body": json.dumps({
                "event_id": "evt_123",
                "event_time": datetime.utcnow().isoformat() + "Z",
                "event_type": EventType.PERF_SAMPLE.value,
                "severity": "info",
                "source": {"component": "backend", "channel": "backend"},
                "correlation": {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"},
                "payload": {
                    "operation": "decision",
                    "latency_ms": 150,
                    "component": "backend",
                    "channel": "backend",
                    "redaction_applied": True,
                },
            }),
        }
        should_accept, reason, audit_event = self.processor.process_log_record(log_record)
        self.assertTrue(should_accept)
        self.assertIsNone(reason)

    def test_process_log_record_unsafe(self):
        """Test processing unsafe log record."""
        log_record = {
            "body": json.dumps({
                "event_id": "evt_123",
                "event_time": datetime.utcnow().isoformat() + "Z",
                "event_type": EventType.ERROR_CAPTURED.value,
                "severity": "error",
                "source": {"component": "backend", "channel": "backend"},
                "correlation": {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"},
                "payload": {
                    "error_class": "security",
                    "error_code": "ERR_SEC_001",
                    "stage": "validation",
                    "message_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
                    "input_fingerprint": "b4g6f9c2d5e7a8f0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6",
                    "output_fingerprint": "c5h7g0d3e6f8b9g1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5",
                    "internal_state_fingerprint": "d6i8h1e4f7g9c0h2d4e6f8g0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8",
                    "component": "backend",
                    "channel": "backend",
                    "api_key": "REDACTED_KEY_PLACEHOLDER",  # Deny-listed
                    "redaction_applied": False,
                },
            }),
        }
        should_accept, reason, audit_event = self.processor.process_log_record(log_record)
        self.assertFalse(should_accept)
        self.assertIsNotNone(reason)
        self.assertIsNotNone(audit_event)  # Audit event should be created


if __name__ == "__main__":
    unittest.main()
