"""
Tests for Schema Guard processor (OBS-05).

Tests schema validation, rejection handling, and metrics.
"""

import json
import unittest
from datetime import datetime

from ..collector.processors.schema_guard.schema_guard_processor import (
    SchemaGuardProcessor,
    ValidationResult,
)
from ..contracts.event_types import EventType


class TestSchemaGuard(unittest.TestCase):
    """Test Schema Guard processor."""

    def setUp(self):
        """Set up Schema Guard processor."""
        self.processor = SchemaGuardProcessor(enabled=True)

    def test_validate_valid_event(self):
        """Test validation of valid event."""
        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.PERF_SAMPLE.value,
            "severity": "info",
            "source": {
                "component": "backend",
                "channel": "backend",
                "version": "1.0.0",
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            },
            "payload": {
                "operation": "decision",
                "latency_ms": 150,
                "component": "backend",
                "channel": "backend",
            },
        }
        result = self.processor.validate_event(event)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.reason_code)

    def test_validate_invalid_envelope(self):
        """Test validation of event with invalid envelope."""
        event = {
            "event_id": "evt_123",
            # Missing required fields: event_time, event_type, severity, source, correlation, payload
        }
        result = self.processor.validate_event(event)
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.reason_code)

    def test_validate_missing_event_type(self):
        """Test validation of event with missing event_type."""
        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            # Missing event_type
            "severity": "info",
            "source": {
                "component": "backend",
                "channel": "backend",
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            },
            "payload": {},
        }
        result = self.processor.validate_event(event)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "missing_event_type")

    def test_validate_unknown_event_type(self):
        """Test validation of event with unknown event_type."""
        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": "unknown.event.type",
            "severity": "info",
            "source": {
                "component": "backend",
                "channel": "backend",
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            },
            "payload": {},
        }
        result = self.processor.validate_event(event)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "unknown_event_type")

    def test_validate_invalid_payload(self):
        """Test validation of event with invalid payload."""
        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.PERF_SAMPLE.value,
            "severity": "info",
            "source": {
                "component": "backend",
                "channel": "backend",
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            },
            "payload": {
                # Missing required fields: operation, latency_ms, component, channel
            },
        }
        result = self.processor.validate_event(event)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "invalid_payload")

    def test_process_log_record_valid(self):
        """Test processing valid log record."""
        log_record = {
            "body": json.dumps({
                "event_id": "evt_123",
                "event_time": datetime.utcnow().isoformat() + "Z",
                "event_type": EventType.PERF_SAMPLE.value,
                "severity": "info",
                "source": {
                    "component": "backend",
                    "channel": "backend",
                },
                "correlation": {
                    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
                },
                "payload": {
                    "operation": "decision",
                    "latency_ms": 150,
                    "component": "backend",
                    "channel": "backend",
                },
            }),
        }
        should_accept, reason = self.processor.process_log_record(log_record)
        self.assertTrue(should_accept)
        self.assertIsNone(reason)

    def test_process_log_record_invalid(self):
        """Test processing invalid log record."""
        log_record = {
            "body": json.dumps({
                "event_id": "evt_123",
                # Missing required fields
            }),
        }
        should_accept, reason = self.processor.process_log_record(log_record)
        self.assertFalse(should_accept)
        self.assertIsNotNone(reason)

    def test_get_metrics(self):
        """Test getting validation metrics."""
        # Process some events to generate metrics
        valid_event = {
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
            },
        }
        self.processor.validate_event(valid_event)

        metrics = self.processor.get_metrics()
        self.assertIn("zeroui_obsv_events_validated_total", metrics)
        self.assertIn("zeroui_obsv_events_rejected_total", metrics)


if __name__ == "__main__":
    unittest.main()
