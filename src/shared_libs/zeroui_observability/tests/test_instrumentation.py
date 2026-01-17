"""
Tests for instrumentation (OBS-07).

Tests Python and TypeScript event emission, feature flags, trace context.
"""

import asyncio
import os
import unittest
from unittest.mock import Mock, patch

from ..instrumentation.python.instrumentation import EventEmitter, get_event_emitter
from ..contracts.event_types import EventType
from ..correlation.trace_context import TraceContext


class TestInstrumentation(unittest.TestCase):
    """Test instrumentation for telemetry emission."""

    def setUp(self):
        """Set up test environment."""
        # Disable OTLP for unit tests
        os.environ["ZEROUI_OBSV_ENABLED"] = "true"
        os.environ["OTLP_EXPORTER_ENDPOINT"] = "http://localhost:4317"

    def test_event_emitter_initialization(self):
        """Test EventEmitter initialization."""
        emitter = EventEmitter(
            enabled=True,
            component="test_component",
            channel="backend",
            version="1.0.0",
        )
        self.assertEqual(emitter._component, "test_component")
        self.assertEqual(emitter._channel, "backend")

    def test_feature_flag_check(self):
        """Test feature flag checking."""
        # Enabled
        os.environ["ZEROUI_OBSV_ENABLED"] = "true"
        emitter = EventEmitter()
        self.assertTrue(emitter._enabled)

        # Disabled
        os.environ["ZEROUI_OBSV_ENABLED"] = "false"
        emitter = EventEmitter()
        self.assertFalse(emitter._enabled)

    def test_create_envelope(self):
        """Test event envelope creation."""
        emitter = EventEmitter(component="test", channel="backend")
        trace_ctx = TraceContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
        )
        payload = {"operation": "decision", "latency_ms": 150}

        envelope = emitter._create_envelope(
            EventType.PERF_SAMPLE,
            payload,
            "info",
            trace_ctx,
        )

        self.assertEqual(envelope["event_type"], EventType.PERF_SAMPLE.value)
        self.assertEqual(envelope["severity"], "info")
        self.assertEqual(envelope["correlation"]["trace_id"], trace_ctx.trace_id)
        self.assertEqual(envelope["correlation"]["span_id"], trace_ctx.span_id)
        self.assertEqual(envelope["source"]["component"], "test")
        self.assertEqual(envelope["source"]["channel"], "backend")

    @patch("src.shared_libs.zeroui_observability.instrumentation.python.instrumentation.OTLP_AVAILABLE", False)
    def test_emit_event_disabled(self):
        """Test event emission when disabled."""
        emitter = EventEmitter(enabled=False)
        result = asyncio.run(
            emitter.emit_event(EventType.PERF_SAMPLE, {"operation": "test"}, "info")
        )
        self.assertFalse(result)

    def test_emit_perf_sample(self):
        """Test perf.sample.v1 emission."""
        emitter = EventEmitter(component="test", channel="backend")
        trace_ctx = TraceContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
        )

        # Mock OTLP emission
        with patch.object(emitter, "_emit_otlp_log", return_value=None):
            result = asyncio.run(
                emitter.emit_perf_sample(
                    "decision",
                    150,
                    trace_ctx=trace_ctx,
                    cache_hit=True,
                )
            )
            self.assertTrue(result)

    def test_emit_error_captured(self):
        """Test error.captured.v1 emission."""
        emitter = EventEmitter(component="test", channel="backend")
        trace_ctx = TraceContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
        )

        # Mock OTLP emission
        with patch.object(emitter, "_emit_otlp_log", return_value=None):
            result = asyncio.run(
                emitter.emit_error_captured(
                    "architecture",
                    "ERR_001",
                    "retrieval",
                    trace_ctx=trace_ctx,
                    message="Test error",
                )
            )
            self.assertTrue(result)

    def test_get_event_emitter_singleton(self):
        """Test get_event_emitter returns singleton."""
        emitter1 = get_event_emitter()
        emitter2 = get_event_emitter()
        self.assertIs(emitter1, emitter2)


if __name__ == "__main__":
    unittest.main()
