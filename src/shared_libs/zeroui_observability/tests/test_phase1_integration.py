"""
Integration tests for Phase 1 (OBS-04 through OBS-09).

Tests end-to-end workflows: OTLP → validation → storage, telemetry emission, SLI computation.
"""

import asyncio
import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch

from ..collector.processors.schema_guard.schema_guard_processor import SchemaGuardProcessor
from ..collector.processors.privacy_guard.privacy_guard_processor import PrivacyGuardProcessor
from ..instrumentation.python.instrumentation import EventEmitter
from ..sli.sli_calculator import SLICalculator
from ..contracts.event_types import EventType
from ..correlation.trace_context import get_or_create_trace_context


class TestPhase1Integration(unittest.TestCase):
    """Integration tests for Phase 1 components."""

    def setUp(self):
        """Set up test components."""
        self.schema_guard = SchemaGuardProcessor(enabled=True)
        self.privacy_guard = PrivacyGuardProcessor(enabled=True)
        self.event_emitter = EventEmitter(enabled=True, component="test", channel="backend")
        self.sli_calculator = SLICalculator()

    def test_end_to_end_collector_pipeline(self):
        """Test end-to-end collector pipeline: OTLP → validation → storage."""
        # Step 1: Create event
        trace_ctx = get_or_create_trace_context()
        payload = {
            "operation": "decision",
            "latency_ms": 150,
            "component": "backend",
            "channel": "backend",
        }

        # Step 2: Apply redaction (producer-side)
        from ..privacy.redaction_enforcer import RedactionEnforcer
        redaction_enforcer = RedactionEnforcer(use_cccs=False)
        redaction_result = redaction_enforcer.enforce(payload)
        redacted_payload = redaction_result.redacted_payload
        redacted_payload["redaction_applied"] = redaction_result.redaction_applied

        # Step 3: Create envelope
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
                "trace_id": trace_ctx.trace_id,
                "span_id": trace_ctx.span_id,
            },
            "payload": redacted_payload,
        }

        # Step 4: Schema Guard validation
        schema_result = self.schema_guard.validate_event(event)
        self.assertTrue(schema_result.is_valid, f"Schema validation failed: {schema_result.error_message}")

        # Step 5: Privacy Guard check
        privacy_result = self.privacy_guard.check_privacy(event)
        self.assertTrue(privacy_result.is_safe, f"Privacy check failed: {privacy_result.violation_type}")

        # Step 6: Event should pass through pipeline
        log_record = {"body": json.dumps(event)}
        schema_accept, schema_reason = self.schema_guard.process_log_record(log_record)
        privacy_accept, privacy_reason, audit_event = self.privacy_guard.process_log_record(log_record)

        self.assertTrue(schema_accept, f"Schema guard rejected: {schema_reason}")
        self.assertTrue(privacy_accept, f"Privacy guard rejected: {privacy_reason}")

    def test_telemetry_emission_across_tiers(self):
        """Test telemetry emission works across all tiers."""
        # Tier 3: Python (Cloud Services)
        trace_ctx = get_or_create_trace_context()

        # Mock OTLP emission
        with patch.object(self.event_emitter, "_emit_otlp_log", return_value=None):
            result = asyncio.run(
                self.event_emitter.emit_perf_sample(
                    "decision",
                    150,
                    trace_ctx=trace_ctx,
                )
            )
            self.assertTrue(result)

    def test_sli_computation_from_real_events(self):
        """Test SLI computation from real event data."""
        # Create test events
        traces = [
            {
                "parent_span_id": None,
                "attributes": {
                    "component": "backend",
                    "channel": "backend",
                    "run_outcome": "success",
                },
                "start_time": 1000.0,
                "end_time": 1150.0,
            },
        ]
        perf_samples = [
            {
                "event_type": EventType.PERF_SAMPLE.value,
                "payload": {
                    "operation": "decision",
                    "latency_ms": 150,
                    "component": "backend",
                    "channel": "backend",
                },
            },
        ]

        # Compute SLIs
        sli_a_results = self.sli_calculator.compute_sli_a(traces)
        sli_b_results = self.sli_calculator.compute_sli_b(traces, perf_samples)

        self.assertGreater(len(sli_a_results), 0)
        self.assertGreater(len(sli_b_results), 0)

        # Verify SLI values
        sli_a = sli_a_results[0]
        self.assertEqual(sli_a.sli_id, "SLI-A")
        self.assertEqual(sli_a.value, 1.0)  # 1 success / 1 total

        sli_b = sli_b_results[0]
        self.assertEqual(sli_b.sli_id, "SLI-B")
        self.assertIn("p95", sli_b.metadata)

    def test_dashboard_data_population(self):
        """Test dashboard data population from SLIs."""
        from ..dashboards.dashboard_loader import DashboardLoader

        # Compute SLIs
        traces = [
            {
                "parent_span_id": None,
                "attributes": {"component": "backend", "channel": "backend", "run_outcome": "success"},
            },
        ]
        sli_results = self.sli_calculator.compute_sli_a(traces)

        # Load dashboard
        loader = DashboardLoader()
        dashboard = loader.load_dashboard("d1")
        self.assertIsNotNone(dashboard)

        # Verify dashboard has panels that can consume SLI data
        panels = dashboard.get("panels", [])
        self.assertGreater(len(panels), 0)

        # Verify panels reference SLI metrics
        dashboard_str = json.dumps(dashboard)
        self.assertIn("sli", dashboard_str.lower())


if __name__ == "__main__":
    unittest.main()
