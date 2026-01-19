"""
Performance tests for ZeroUI Observability Layer Phase 0.

Tests performance characteristics: schema validation speed, redaction speed.
"""

import json
import time
import unittest
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from ..contracts.payloads.schema_loader import validate_payload
from ..privacy.redaction_enforcer import RedactionEnforcer

# Schema directory
_SCHEMA_DIR = Path(__file__).parent.parent / "contracts"
_FIXTURES_DIR = _SCHEMA_DIR / "payloads" / "fixtures" / "valid"


class TestPerformance(unittest.TestCase):
    """Performance tests for observability layer."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        if not JSONSCHEMA_AVAILABLE:
            raise unittest.SkipTest("jsonschema not available")

        cls.redaction_enforcer = RedactionEnforcer(use_cccs=False)

    def test_schema_validation_performance(self):
        """Test schema validation completes within acceptable time."""
        fixture_path = _FIXTURES_DIR / "error_captured_v1.json"
        if not fixture_path.exists():
            self.skipTest("Fixture not found")

        with open(fixture_path, "r", encoding="utf-8") as f:
            payload = json.load(f)

        # Measure validation time
        start = time.perf_counter()
        for _ in range(100):
            is_valid, _ = validate_payload("error.captured.v1", payload)
            self.assertTrue(is_valid)
        elapsed = time.perf_counter() - start

        # Should complete 100 validations in < 5 seconds (allows for schema loading and CI/load variance)
        self.assertLess(elapsed, 5.0, f"Validation too slow: {elapsed:.3f}s for 100 iterations")

    def test_redaction_performance(self):
        """Test redaction completes within acceptable time."""
        payload = {
            "error_class": "architecture",
            "error_code": "ERR_001",
            "stage": "retrieval",
            "message_fingerprint": "a3f5e8b2c1d4f6a7e9b1c3d5f7a9b2c4d6e8f0a1b3c5d7e9f1a3b5c7d9e1f3a5",
            "input_fingerprint": "b4g6f9c2d5e7a8f0b2c4d6e8f0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6",
            "output_fingerprint": "c5h7g0d3e6f8b9g1c3d5e7f9a1b3c5d7e9f1a3b5c7d9e1f3a5b7c9d1e3f5",
            "internal_state_fingerprint": "d6i8h1e4f7g9c0h2d4e6f8g0a2b4c6d8e0f2a4b6c8d0e2f4a6b8c0d2e4f6a8",
            "component": "edge_agent",
            "channel": "ide"
        }

        # Measure redaction time
        start = time.perf_counter()
        for _ in range(100):
            result = self.redaction_enforcer.enforce(payload)
            self.assertIsNotNone(result)
        elapsed = time.perf_counter() - start

        # Should complete 100 redactions in < 1 second
        self.assertLess(elapsed, 1.0, f"Redaction too slow: {elapsed:.3f}s for 100 iterations")

    def test_trace_context_generation_performance(self):
        """Test trace context generation completes within acceptable time."""
        from ..correlation.trace_context import generate_traceparent, parse_traceparent

        # Measure generation time
        start = time.perf_counter()
        traceparents = []
        for _ in range(1000):
            traceparent = generate_traceparent()
            traceparents.append(traceparent)
        elapsed = time.perf_counter() - start

        # Should complete 1000 generations in < 0.1 seconds
        self.assertLess(elapsed, 0.1, f"Generation too slow: {elapsed:.3f}s for 1000 iterations")

        # Measure parsing time
        start = time.perf_counter()
        for traceparent in traceparents:
            ctx = parse_traceparent(traceparent)
            self.assertIsNotNone(ctx)
        elapsed = time.perf_counter() - start

        # Should complete 1000 parsings in < 0.1 seconds
        self.assertLess(elapsed, 0.1, f"Parsing too slow: {elapsed:.3f}s for 1000 iterations")

    def test_large_payload_redaction(self):
        """Test redaction performance with large payload."""
        # Create large payload
        payload = {
            "error_class": "architecture",
            "error_code": "ERR_001",
            "stage": "retrieval",
            "component": "edge_agent",
            "channel": "ide",
            "large_field": "x" * 10000,  # 10KB field
            "many_fields": {f"field_{i}": f"value_{i}" for i in range(100)}
        }

        # Measure redaction time
        start = time.perf_counter()
        result = self.redaction_enforcer.enforce(payload)
        elapsed = time.perf_counter() - start

        # Should complete in < 0.1 seconds
        self.assertLess(elapsed, 0.1, f"Large payload redaction too slow: {elapsed:.3f}s")
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
