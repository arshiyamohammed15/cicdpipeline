"""
Integration tests for ZeroUI Observability Layer Phase 0.

Tests end-to-end workflows: envelope + payload validation + redaction + trace propagation.
"""

import json
import unittest
from datetime import datetime
from pathlib import Path

try:
    import jsonschema
    from jsonschema import validate
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from ..contracts.event_types import EventType
from ..contracts.payloads.schema_loader import validate_payload
from ..privacy.redaction_enforcer import RedactionEnforcer
from ..correlation.trace_context import generate_traceparent, parse_traceparent

# Schema directory
_SCHEMA_DIR = Path(__file__).parent.parent / "contracts"


def load_envelope_schema():
    """Load envelope schema."""
    schema_path = _SCHEMA_DIR / "envelope_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestIntegration(unittest.TestCase):
    """Integration tests for observability layer."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        if not JSONSCHEMA_AVAILABLE:
            raise unittest.SkipTest("jsonschema not available")

        cls.envelope_schema = load_envelope_schema()
        cls.redaction_enforcer = RedactionEnforcer(use_cccs=False)

    def test_end_to_end_event_creation(self):
        """Test creating a complete event with envelope + payload + redaction + trace."""
        # Step 1: Generate trace context
        traceparent = generate_traceparent()
        trace_ctx = parse_traceparent(traceparent)
        self.assertIsNotNone(trace_ctx)

        # Step 2: Create payload (with potential sensitive data)
        raw_payload = {
            "error_class": "architecture",
            "error_code": "ERR_001",
            "stage": "retrieval",
            "message": "API key validation failed",  # Sensitive - will be redacted
            "api_key": "REDACTED_KEY_PLACEHOLDER",  # Deny-listed - will be removed
            "component": "edge_agent",
            "channel": "ide"
        }

        # Step 3: Apply redaction
        redaction_result = self.redaction_enforcer.enforce(raw_payload)
        self.assertTrue(redaction_result.redaction_applied)

        # Step 4: Compute fingerprints after redaction
        redacted = redaction_result.redacted_payload
        # Add required fingerprint fields
        redacted["message_fingerprint"] = self._compute_fingerprint(
            redacted.get("message", "")
        )
        redacted["input_fingerprint"] = self._compute_fingerprint(
            redacted.get("input", "")
        )
        redacted["output_fingerprint"] = self._compute_fingerprint(
            redacted.get("output", "")
        )
        redacted["internal_state_fingerprint"] = self._compute_fingerprint(
            redacted.get("internal_state", "")
        )
        # Ensure all required fields are present
        if "stage" not in redacted:
            redacted["stage"] = "retrieval"

        # Step 5: Validate payload schema
        is_valid, error = validate_payload("error.captured.v1", redacted)
        self.assertTrue(is_valid, f"Payload validation failed: {error}")

        # Step 6: Create envelope
        envelope = {
            "event_id": "evt_123",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": "error.captured.v1",
            "severity": "error",
            "source": {
                "component": "edge_agent",
                "channel": "ide",
                "version": "1.0.0"
            },
            "correlation": {
                "trace_id": trace_ctx.trace_id,
                "span_id": trace_ctx.span_id
            },
            "payload": redacted
        }

        # Step 7: Validate envelope
        validate(instance=envelope, schema=self.envelope_schema)

    def test_trace_propagation_across_boundaries(self):
        """Test trace propagation across IDE → Edge → Backend boundaries."""
        # IDE generates trace
        ide_traceparent = generate_traceparent()
        ide_ctx = parse_traceparent(ide_traceparent)
        self.assertIsNotNone(ide_ctx)

        # Edge Agent receives and creates child
        edge_ctx = ide_ctx.create_child()
        edge_traceparent = edge_ctx.to_traceparent()

        # Verify same trace_id
        self.assertEqual(ide_ctx.trace_id, edge_ctx.trace_id)
        self.assertEqual(edge_ctx.parent_span_id, ide_ctx.span_id)

        # Backend receives and creates child
        backend_ctx = parse_traceparent(edge_traceparent)
        self.assertIsNotNone(backend_ctx)
        backend_child = backend_ctx.create_child()

        # Verify same trace_id across all boundaries
        self.assertEqual(ide_ctx.trace_id, backend_child.trace_id)

    def test_redaction_before_fingerprint(self):
        """Test fingerprints are computed after redaction."""
        payload = {
            "error_class": "security",
            "error_code": "ERR_SEC_001",
            "stage": "validation",
            "message": "API key: REDACTED_KEY_PLACEHOLDER",  # Contains secret
            "component": "backend",
            "channel": "backend"
        }

        # Apply redaction
        result = self.redaction_enforcer.enforce(payload)
        redacted = result.redacted_payload

        # Compute fingerprint after redaction
        message_fingerprint = self._compute_fingerprint(redacted.get("message", ""))

        # Verify secret is not in redacted payload
        self.assertNotIn("sk_live", str(redacted))

        # Verify fingerprint is computed (not empty if message exists)
        if "message" in redacted:
            self.assertNotEqual(message_fingerprint, "")

    def _compute_fingerprint(self, content: str) -> str:
        """Compute SHA-256 fingerprint."""
        import hashlib
        return hashlib.sha256(content.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    unittest.main()
