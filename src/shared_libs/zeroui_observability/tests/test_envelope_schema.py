"""
Tests for event envelope schema (OBS-00).

Validates envelope_schema.json against JSON Schema Draft 2020-12.
"""

import json
import unittest
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception  # type: ignore

from ..contracts.event_types import EventType

# Schema directory
_SCHEMA_DIR = Path(__file__).parent.parent / "contracts"


class TestEnvelopeSchema(unittest.TestCase):
    """Test event envelope schema validation."""

    @classmethod
    def setUpClass(cls):
        """Load envelope schema."""
        if not JSONSCHEMA_AVAILABLE:
            raise unittest.SkipTest("jsonschema not available")

        schema_path = _SCHEMA_DIR / "envelope_schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            cls.schema = json.load(f)

    def test_valid_envelope(self):
        """Test valid envelope passes validation."""
        envelope = {
            "event_id": "evt_123",
            "event_time": "2026-01-17T10:00:00Z",
            "event_type": "error.captured.v1",
            "severity": "error",
            "source": {
                "component": "edge_agent",
                "channel": "ide",
                "version": "1.0.0"
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
                "span_id": "00f067aa0ba902b7"
            },
            "payload": {}
        }
        validate(instance=envelope, schema=self.schema)

    def test_missing_required_fields(self):
        """Test missing required fields fail validation."""
        envelope = {
            "event_id": "evt_123",
            "event_time": "2026-01-17T10:00:00Z",
            # Missing: event_type, severity, source, correlation, payload
        }
        with self.assertRaises(ValidationError):
            validate(instance=envelope, schema=self.schema)

    def test_invalid_severity(self):
        """Test invalid severity enum fails validation."""
        envelope = {
            "event_id": "evt_123",
            "event_time": "2026-01-17T10:00:00Z",
            "event_type": "error.captured.v1",
            "severity": "invalid",  # Invalid enum value
            "source": {
                "component": "edge_agent",
                "channel": "ide"
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
            },
            "payload": {}
        }
        with self.assertRaises(ValidationError):
            validate(instance=envelope, schema=self.schema)

    def test_invalid_channel(self):
        """Test invalid channel enum fails validation."""
        envelope = {
            "event_id": "evt_123",
            "event_time": "2026-01-17T10:00:00Z",
            "event_type": "error.captured.v1",
            "severity": "error",
            "source": {
                "component": "edge_agent",
                "channel": "invalid"  # Invalid enum value
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
            },
            "payload": {}
        }
        with self.assertRaises(ValidationError):
            validate(instance=envelope, schema=self.schema)

    def test_all_severity_values(self):
        """Test all valid severity enum values pass."""
        for severity in ["debug", "info", "warn", "error", "critical"]:
            envelope = {
                "event_id": "evt_123",
                "event_time": "2026-01-17T10:00:00Z",
                "event_type": "error.captured.v1",
                "severity": severity,
                "source": {
                    "component": "edge_agent",
                    "channel": "ide"
                },
                "correlation": {
                    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
                },
                "payload": {}
            }
            validate(instance=envelope, schema=self.schema)

    def test_all_channel_values(self):
        """Test all valid channel enum values pass."""
        for channel in ["ide", "edge_agent", "backend", "ci", "other"]:
            envelope = {
                "event_id": "evt_123",
                "event_time": "2026-01-17T10:00:00Z",
                "event_type": "error.captured.v1",
                "severity": "error",
                "source": {
                    "component": "edge_agent",
                    "channel": channel
                },
                "correlation": {
                    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
                },
                "payload": {}
            }
            validate(instance=envelope, schema=self.schema)

    def test_optional_confidence(self):
        """Test optional confidence field."""
        envelope = {
            "event_id": "evt_123",
            "event_time": "2026-01-17T10:00:00Z",
            "event_type": "error.captured.v1",
            "severity": "error",
            "source": {
                "component": "edge_agent",
                "channel": "ide"
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
            },
            "confidence": 0.95,
            "payload": {}
        }
        validate(instance=envelope, schema=self.schema)

    def test_invalid_confidence_range(self):
        """Test confidence outside valid range fails."""
        envelope = {
            "event_id": "evt_123",
            "event_time": "2026-01-17T10:00:00Z",
            "event_type": "error.captured.v1",
            "severity": "error",
            "source": {
                "component": "edge_agent",
                "channel": "ide"
            },
            "correlation": {
                "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
            },
            "confidence": 1.5,  # Invalid: > 1.0
            "payload": {}
        }
        with self.assertRaises(ValidationError):
            validate(instance=envelope, schema=self.schema)


class TestEventTypes(unittest.TestCase):
    """Test event type registry."""

    def test_all_event_types_exist(self):
        """Test all 12 required event types are defined."""
        expected_types = [
            "error.captured.v1",
            "prompt.validation.result.v1",
            "memory.access.v1",
            "memory.validation.v1",
            "evaluation.result.v1",
            "user.flag.v1",
            "bias.scan.result.v1",
            "retrieval.eval.v1",
            "failure.replay.bundle.v1",
            "perf.sample.v1",
            "privacy.audit.v1",
            "alert.noise_control.v1",
        ]
        for event_type in expected_types:
            self.assertIn(event_type, EventType.all_event_types())

    def test_is_valid_event_type(self):
        """Test event type validation."""
        self.assertTrue(EventType.is_valid_event_type("error.captured.v1"))
        self.assertFalse(EventType.is_valid_event_type("invalid.event.type"))

    def test_get_event_type(self):
        """Test get_event_type function."""
        from ..contracts.event_types import get_event_type

        self.assertEqual(get_event_type("error.captured.v1"), EventType.ERROR_CAPTURED)
        self.assertIsNone(get_event_type("invalid.event.type"))


if __name__ == "__main__":
    unittest.main()
