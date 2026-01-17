"""
Tests for trace context propagation (OBS-03).

Tests W3C Trace Context parsing and generation.
"""

import unittest

from ..correlation.trace_context import (
    TraceContext,
    parse_traceparent,
    generate_traceparent,
    generate_trace_id,
    generate_span_id,
    get_or_create_trace_context,
)


class TestTraceContext(unittest.TestCase):
    """Test trace context utilities."""

    def test_generate_trace_id(self):
        """Test trace ID generation."""
        trace_id = generate_trace_id()
        self.assertEqual(len(trace_id), 32)
        self.assertTrue(all(c in "0123456789abcdef" for c in trace_id.lower()))

    def test_generate_span_id(self):
        """Test span ID generation."""
        span_id = generate_span_id()
        self.assertEqual(len(span_id), 16)
        self.assertTrue(all(c in "0123456789abcdef" for c in span_id.lower()))

    def test_parse_valid_traceparent(self):
        """Test parsing valid traceparent."""
        traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        ctx = parse_traceparent(traceparent)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.trace_id, "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(ctx.span_id, "00f067aa0ba902b7")
        self.assertEqual(ctx.trace_flags, "01")

    def test_parse_invalid_traceparent(self):
        """Test parsing invalid traceparent."""
        invalid_cases = [
            "",
            "invalid",
            "00-invalid",
            "00-4bf92f3577b34da6a3ce929d0e0e4736-invalid-01",
            "01-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",  # Unsupported version
        ]
        for invalid in invalid_cases:
            ctx = parse_traceparent(invalid)
            self.assertIsNone(ctx, f"Should fail for: {invalid}")

    def test_generate_traceparent(self):
        """Test traceparent generation."""
        trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
        parent_span_id = "00f067aa0ba902b7"
        trace_flags = "01"
        traceparent = generate_traceparent(trace_id, parent_span_id, trace_flags)
        self.assertEqual(
            traceparent, "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        )

    def test_generate_traceparent_defaults(self):
        """Test traceparent generation with defaults."""
        traceparent = generate_traceparent()
        parts = traceparent.split("-")
        self.assertEqual(len(parts), 4)
        self.assertEqual(parts[0], "00")  # Version
        self.assertEqual(len(parts[1]), 32)  # Trace ID
        self.assertEqual(len(parts[2]), 16)  # Parent span ID
        self.assertEqual(parts[3], "01")  # Trace flags (sampled)

    def test_trace_context_to_traceparent(self):
        """Test TraceContext to traceparent conversion."""
        ctx = TraceContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            parent_span_id="a1b2c3d4e5f6g7h8",
            trace_flags="01"
        )
        traceparent = ctx.to_traceparent()
        self.assertEqual(
            traceparent, "00-4bf92f3577b34da6a3ce929d0e0e4736-a1b2c3d4e5f6g7h8-01"
        )

    def test_trace_context_from_traceparent(self):
        """Test TraceContext from traceparent."""
        traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        ctx = TraceContext.from_traceparent(traceparent)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.trace_id, "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(ctx.span_id, "00f067aa0ba902b7")

    def test_create_child_context(self):
        """Test creating child trace context."""
        parent = TraceContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            trace_flags="01"
        )
        child = parent.create_child()
        self.assertEqual(child.trace_id, parent.trace_id)
        self.assertNotEqual(child.span_id, parent.span_id)
        self.assertEqual(child.parent_span_id, parent.span_id)

    def test_get_or_create_trace_context_with_header(self):
        """Test get_or_create_trace_context with traceparent header."""
        traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        ctx = get_or_create_trace_context(traceparent=traceparent)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.trace_id, "4bf92f3577b34da6a3ce929d0e0e4736")

    def test_get_or_create_trace_context_new(self):
        """Test get_or_create_trace_context creates new when no header."""
        ctx = get_or_create_trace_context(traceparent=None)
        self.assertIsNotNone(ctx)
        self.assertEqual(len(ctx.trace_id), 32)
        self.assertEqual(len(ctx.span_id), 16)

    def test_trace_context_normalization(self):
        """Test trace context values are normalized to lowercase."""
        traceparent = "00-4BF92F3577B34DA6A3CE929D0E0E4736-00F067AA0BA902B7-01"
        ctx = parse_traceparent(traceparent)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.trace_id, "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(ctx.span_id, "00f067aa0ba902b7")
        self.assertEqual(ctx.trace_flags, "01")


if __name__ == "__main__":
    unittest.main()
