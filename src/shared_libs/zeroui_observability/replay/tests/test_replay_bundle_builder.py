"""
Tests for ReplayBundleBuilder.

OBS-15: Failure Replay Bundle Builder tests.
"""

import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from ..replay_bundle_builder import ReplayBundle, ReplayBundleBuilder
from ...contracts.event_types import EventType


class TestReplayBundleBuilder(unittest.TestCase):
    """Test ReplayBundleBuilder."""

    def setUp(self):
        """Set up test fixtures."""
        self.builder = ReplayBundleBuilder()

    def test_build_from_trace_id_success(self):
        """Test building bundle from trace_id."""
        trace_id = "a" * 32
        events = [
            {
                "event_id": "event_001",
                "event_type": EventType.ERROR_CAPTURED.value,
                "event_time": datetime.now(timezone.utc).isoformat(),
                "severity": "error",
                "source": {"component": "test", "channel": "backend"},
                "correlation": {"trace_id": trace_id, "span_id": "span_001"},
                "payload": {"error_code": "E001", "message_fingerprint": "fp1"},
            },
            {
                "event_id": "event_002",
                "event_type": EventType.PERF_SAMPLE.value,
                "event_time": datetime.now(timezone.utc).isoformat(),
                "severity": "info",
                "source": {"component": "test", "channel": "backend"},
                "correlation": {"trace_id": trace_id, "span_id": "span_002"},
                "payload": {},
            },
        ]

        # Mock event retriever
        self.builder._event_retriever = MagicMock()
        self.builder._event_retriever.get_events_by_trace_id.return_value = events

        # Build bundle
        bundle = self.builder.build_from_trace_id(trace_id, tenant_id="tenant_001")

        # Verify bundle
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle.trace_id, trace_id)
        self.assertEqual(bundle.trigger_event_id, "event_001")  # First error event
        self.assertEqual(len(bundle.included_event_ids), 2)
        self.assertIn("event_001", bundle.included_event_ids)
        self.assertIn("event_002", bundle.included_event_ids)
        self.assertIsNotNone(bundle.checksum)
        self.assertEqual(len(bundle.checksum), 64)  # SHA-256 hex

    def test_build_from_trace_id_invalid(self):
        """Test building bundle with invalid trace_id."""
        with self.assertRaises(ValueError):
            self.builder.build_from_trace_id("invalid")

    def test_build_from_trace_id_no_events(self):
        """Test building bundle with no events."""
        trace_id = "a" * 32
        self.builder._event_retriever = MagicMock()
        self.builder._event_retriever.get_events_by_trace_id.return_value = []

        with self.assertRaises(ValueError):
            self.builder.build_from_trace_id(trace_id)

    def test_build_from_run_id_success(self):
        """Test building bundle from run_id."""
        run_id = "run_001"
        trace_id = "a" * 32
        events = [
            {
                "event_id": "event_001",
                "event_type": EventType.ERROR_CAPTURED.value,
                "event_time": datetime.now(timezone.utc).isoformat(),
                "severity": "error",
                "source": {"component": "test", "channel": "backend"},
                "correlation": {"trace_id": trace_id, "span_id": "span_001", "request_id": run_id},
                "payload": {"error_code": "E001"},
            },
        ]

        # Mock event retriever
        self.builder._event_retriever = MagicMock()
        self.builder._event_retriever.get_events_by_run_id.return_value = events

        # Build bundle
        bundle = self.builder.build_from_run_id(run_id, tenant_id="tenant_001")

        # Verify bundle
        self.assertIsNotNone(bundle)
        self.assertEqual(bundle.run_id, run_id)
        self.assertEqual(bundle.trace_id, trace_id)
        self.assertEqual(bundle.trigger_event_id, "event_001")
        self.assertIsNotNone(bundle.checksum)

    def test_build_from_run_id_invalid(self):
        """Test building bundle with invalid run_id."""
        with self.assertRaises(ValueError):
            self.builder.build_from_run_id("")

    def test_find_trigger_event(self):
        """Test finding trigger event."""
        events = [
            {
                "event_id": "event_001",
                "event_type": EventType.PERF_SAMPLE.value,
            },
            {
                "event_id": "event_002",
                "event_type": EventType.ERROR_CAPTURED.value,
            },
        ]

        trigger_id = self.builder._find_trigger_event(events)
        self.assertEqual(trigger_id, "event_002")  # First error event

    def test_find_trigger_event_fallback(self):
        """Test finding trigger event with fallback to first event."""
        events = [
            {
                "event_id": "event_001",
                "event_type": EventType.PERF_SAMPLE.value,
            },
        ]

        trigger_id = self.builder._find_trigger_event(events)
        self.assertEqual(trigger_id, "event_001")  # Fallback to first

    def test_compute_checksum(self):
        """Test checksum computation."""
        payload = {"key": "value"}
        checksum = self.builder._compute_checksum(payload)
        self.assertEqual(len(checksum), 64)  # SHA-256 hex
        self.assertIsInstance(checksum, str)

    def test_to_event_payload(self):
        """Test converting bundle to event payload."""
        bundle = ReplayBundle(
            replay_id="replay_001",
            trigger_event_id="event_001",
            included_event_ids=["event_001", "event_002"],
            checksum="a" * 64,
            storage_ref="path/to/bundle.jsonl",
            trace_id="a" * 32,
        )

        bundle_payload = {"events": []}
        event_payload = self.builder.to_event_payload(bundle, bundle_payload)

        self.assertEqual(event_payload["replay_id"], "replay_001")
        self.assertEqual(event_payload["trigger_event_id"], "event_001")
        self.assertEqual(len(event_payload["included_event_ids"]), 2)
        self.assertEqual(event_payload["checksum"], "a" * 64)
        self.assertEqual(event_payload["storage_ref"], "path/to/bundle.jsonl")


if __name__ == "__main__":
    unittest.main()
