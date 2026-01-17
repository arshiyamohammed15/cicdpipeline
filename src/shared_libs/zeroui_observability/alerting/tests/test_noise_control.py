"""
Tests for OBS-12: Noise Control (Dedup, Rate-limit, Suppression) + FPR SLI.
"""

import unittest
from datetime import datetime, timedelta

from ..noise_control import AlertFingerprint, NoiseControlProcessor


class TestNoiseControlProcessor(unittest.TestCase):
    """Test NoiseControlProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = NoiseControlProcessor(
            dedup_window_seconds=900,  # 15 minutes
            rate_limit_window_seconds=3600,  # 1 hour
            max_alerts_per_window=5,
        )

    def test_compute_fingerprint(self):
        """Test fingerprint computation."""
        fingerprint = self.processor.compute_fingerprint(
            alert_id="A1",
            component="test-component",
            channel="backend",
            slo_id="SLI-A",
        )

        self.assertIsNotNone(fingerprint.fingerprint)
        self.assertEqual(len(fingerprint.fingerprint), 16)  # SHA256 truncated to 16 chars
        self.assertEqual(fingerprint.components["alert_id"], "A1")
        self.assertEqual(fingerprint.components["component"], "test-component")

    def test_compute_fingerprint_deterministic(self):
        """Test that fingerprint is deterministic."""
        fp1 = self.processor.compute_fingerprint(
            alert_id="A1",
            component="test-component",
            channel="backend",
        )

        fp2 = self.processor.compute_fingerprint(
            alert_id="A1",
            component="test-component",
            channel="backend",
        )

        self.assertEqual(fp1.fingerprint, fp2.fingerprint)

    def test_should_dedup_first_alert(self):
        """Test dedup check for first alert (should not dedup)."""
        fingerprint = self.processor.compute_fingerprint(
            alert_id="A1",
            component="test-component",
        )

        should_dedup, reason = self.processor.should_dedup(fingerprint)
        self.assertFalse(should_dedup)
        self.assertIsNone(reason)

    def test_should_dedup_duplicate_alert(self):
        """Test dedup check for duplicate alert (should dedup)."""
        fingerprint = self.processor.compute_fingerprint(
            alert_id="A1",
            component="test-component",
        )

        # First alert
        should_dedup1, _ = self.processor.should_dedup(fingerprint)
        self.assertFalse(should_dedup1)

        # Duplicate within window
        should_dedup2, reason = self.processor.should_dedup(fingerprint)
        self.assertTrue(should_dedup2)
        self.assertEqual(reason, "dedup")

    def test_should_rate_limit(self):
        """Test rate limit check."""
        fingerprint = self.processor.compute_fingerprint(
            alert_id="A1",
            component="test-component",
        )

        # Send max_alerts_per_window alerts
        for i in range(self.processor.max_alerts_per_window):
            should_rate_limit, _ = self.processor.should_rate_limit(fingerprint)
            self.assertFalse(should_rate_limit)
            # Add to history manually
            now = datetime.utcnow()
            if fingerprint.fingerprint not in self.processor._fingerprint_history:
                self.processor._fingerprint_history[fingerprint.fingerprint] = []
            self.processor._fingerprint_history[fingerprint.fingerprint].append(now)

        # Next one should be rate limited
        should_rate_limit, reason = self.processor.should_rate_limit(fingerprint)
        self.assertTrue(should_rate_limit)
        self.assertEqual(reason, "rate_limited")

    def test_process_alert_allow(self):
        """Test processing alert that should be allowed."""
        alert_event = {
            "alert_id": "A1",
            "component": "test-component",
            "channel": "backend",
        }

        decision, noise_control_event = self.processor.process_alert(alert_event)

        self.assertEqual(decision, "allow")
        self.assertEqual(noise_control_event["decision"], "allow")
        self.assertEqual(noise_control_event["alert_id"], "A1")

    def test_process_alert_dedup(self):
        """Test processing duplicate alert (should dedup)."""
        alert_event = {
            "alert_id": "A1",
            "component": "test-component",
            "channel": "backend",
        }

        # First alert
        decision1, _ = self.processor.process_alert(alert_event)
        self.assertEqual(decision1, "allow")

        # Duplicate alert
        decision2, noise_control_event = self.processor.process_alert(alert_event)
        self.assertEqual(decision2, "dedup")
        self.assertEqual(noise_control_event["decision"], "dedup")

    def test_record_false_positive(self):
        """Test recording false positive feedback."""
        fingerprint = self.processor.compute_fingerprint(
            alert_id="A1",
            component="test-component",
        )

        # Should not raise
        self.processor.record_false_positive(
            fingerprint=fingerprint,
            is_false_positive=True,
            human_validator="test-validator",
        )

    def test_get_fpr_data(self):
        """Test getting FPR data."""
        fpr_data = self.processor.get_fpr_data(
            detector_type="test-detector",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
        )

        self.assertIn("false_positive", fpr_data)
        self.assertIn("true_positive", fpr_data)
        self.assertEqual(fpr_data["detector_type"], "test-detector")


if __name__ == "__main__":
    unittest.main()
