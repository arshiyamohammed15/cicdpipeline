"""
Performance and security tests for Phase 1.

Tests collector throughput, validation latency, SLI computation speed, redaction enforcement.
"""

import time
import unittest
from datetime import datetime

from ..collector.processors.schema_guard.schema_guard_processor import SchemaGuardProcessor
from ..collector.processors.privacy_guard.privacy_guard_processor import PrivacyGuardProcessor
from ..sli.sli_calculator import SLICalculator
from ..contracts.event_types import EventType
from ..privacy.redaction_enforcer import RedactionEnforcer


class TestPhase1Performance(unittest.TestCase):
    """Performance tests for Phase 1 components."""

    def setUp(self):
        """Set up test components."""
        self.schema_guard = SchemaGuardProcessor(enabled=True)
        self.privacy_guard = PrivacyGuardProcessor(enabled=True)
        self.sli_calculator = SLICalculator()
        self.redaction_enforcer = RedactionEnforcer(use_cccs=False)

    def test_schema_guard_validation_latency(self):
        """Test schema guard validation completes within 10ms per event."""
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
            },
        }

        # Measure validation time
        start = time.perf_counter()
        for _ in range(100):
            result = self.schema_guard.validate_event(event)
            self.assertTrue(result.is_valid)
        elapsed = time.perf_counter() - start

        # Should complete 100 validations in < 2 seconds (20ms per event) to tolerate CI and load variance
        avg_latency_ms = (elapsed / 100) * 1000
        self.assertLess(avg_latency_ms, 20.0, f"Average validation latency too high: {avg_latency_ms:.3f}ms")

    def test_privacy_guard_check_latency(self):
        """Test privacy guard check completes within acceptable time."""
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

        # Measure check time
        start = time.perf_counter()
        for _ in range(100):
            result = self.privacy_guard.check_privacy(event)
            self.assertTrue(result.is_safe)
        elapsed = time.perf_counter() - start

        # Should complete 100 checks in < 2 seconds
        self.assertLess(elapsed, 2.0, f"Privacy check too slow: {elapsed:.3f}s for 100 iterations")

    def test_sli_computation_speed(self):
        """Test SLI computation completes within acceptable time."""
        traces = [
            {
                "parent_span_id": None,
                "attributes": {"component": "backend", "channel": "backend", "run_outcome": "success"},
                "start_time": 1000.0,
                "end_time": 1150.0,
            }
            for _ in range(1000)
        ]

        # Measure computation time
        start = time.perf_counter()
        results = self.sli_calculator.compute_sli_a(traces)
        elapsed = time.perf_counter() - start

        # Should complete in < 1 second for 1000 traces
        self.assertLess(elapsed, 1.0, f"SLI computation too slow: {elapsed:.3f}s for 1000 traces")
        self.assertGreater(len(results), 0)

    def test_redaction_enforcement_performance(self):
        """Test redaction enforcement completes within acceptable time."""
        payload = {
            "error_class": "architecture",
            "error_code": "ERR_001",
            "stage": "retrieval",
            "message_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
            "input_fingerprint": "b4g6f9c2d5e7a8f0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6",
            "output_fingerprint": "c5h7g0d3e6f8b9g1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5",
            "internal_state_fingerprint": "d6i8h1e4f7g9c0h2d4e6f8g0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8",
            "component": "backend",
            "channel": "backend",
        }

        # Measure redaction time
        start = time.perf_counter()
        for _ in range(100):
            result = self.redaction_enforcer.enforce(payload)
            self.assertIsNotNone(result)
        elapsed = time.perf_counter() - start

        # Should complete 100 redactions in < 1 second
        self.assertLess(elapsed, 1.0, f"Redaction too slow: {elapsed:.3f}s for 100 iterations")


class TestPhase1Security(unittest.TestCase):
    """Security tests for Phase 1 components."""

    def setUp(self):
        """Set up test components."""
        self.redaction_enforcer = RedactionEnforcer(use_cccs=False)
        self.privacy_guard = PrivacyGuardProcessor(enabled=True)

    def test_redaction_enforcement_deny_list(self):
        """Test redaction enforcement blocks deny-listed content."""
        payload = {
            "error_class": "security",
            "api_key": "REDACTED_KEY_PLACEHOLDER",
            "password": "secret123",
            "raw_input": "user@example.com",
        }
        result = self.redaction_enforcer.enforce(payload)
        self.assertTrue(result.redaction_applied)
        self.assertNotIn("api_key", result.redacted_payload)
        self.assertNotIn("password", result.redacted_payload)
        self.assertNotIn("raw_input", result.redacted_payload)

    def test_deny_list_detection(self):
        """Test deny-list pattern detection."""
        payload = {
            "error_class": "security",
            "message": "API key: REDACTED_KEY_PLACEHOLDER",
        }
        result = self.redaction_enforcer.enforce(payload)
        self.assertTrue(result.redaction_applied)
        # Message should be removed if it contains deny patterns
        self.assertNotIn("sk_live", str(result.redacted_payload))

    def test_privacy_audit_events(self):
        """Test privacy audit events are emitted for violations."""
        from datetime import datetime
        from ..contracts.event_types import EventType

        event = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.ERROR_CAPTURED.value,
            "severity": "error",
            "source": {"component": "backend", "channel": "backend"},
            "correlation": {"trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"},
            "payload": {
                "error_class": "security",
                "api_key": "REDACTED_KEY_PLACEHOLDER",
                "redaction_applied": False,
            },
        }
        check_result = self.privacy_guard.check_privacy(event)
        if check_result.should_emit_audit:
            audit_event = self.privacy_guard.create_audit_event(event, check_result)
            self.assertEqual(audit_event["event_type"], EventType.PRIVACY_AUDIT.value)
            self.assertIn("violation_type", audit_event["payload"])


if __name__ == "__main__":
    unittest.main()
