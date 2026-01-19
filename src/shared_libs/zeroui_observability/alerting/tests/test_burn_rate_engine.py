"""
Tests for OBS-11: Burn-rate Alert Engine (Multi-window) - Ticket Mode.
"""

import unittest

from ..alert_config import AlertConfig, BurnRateConfig, MinTrafficConfig, RoutingConfig, WindowConfig
from ..burn_rate_engine import AlertEvaluationResult, BurnRateAlertEngine, BurnRateResult


class TestBurnRateAlertEngine(unittest.TestCase):
    """Test BurnRateAlertEngine."""

    def setUp(self):
        """Set up test fixtures."""
        windows = WindowConfig(short="PT5M", mid="PT30M", long="PT2H")
        burn_rate = BurnRateConfig(fast=14.4, fast_confirm=6.0, slow=1.0, slow_confirm=1.0)
        min_traffic = MinTrafficConfig(min_total_events=100)
        routing = RoutingConfig(mode="ticket", target="zeroui-oncall-tickets")

        self.config = AlertConfig(
            alert_id="A1",
            slo_id="SLI-A",
            objective="Test SLO",
            windows=windows,
            burn_rate=burn_rate,
            min_traffic=min_traffic,
            routing=routing,
        )

        self.engine = BurnRateAlertEngine(self.config)

    def test_compute_burn_rate(self):
        """Test burn rate computation."""
        error_rate, burn_rate = self.engine.compute_burn_rate(
            error_count=10,
            total_count=100,
            slo_objective=0.99,
        )

        self.assertEqual(error_rate, 0.1)  # 10/100
        # burn_rate = error_rate / error_budget = 0.1 / 0.01 = 10.0
        self.assertAlmostEqual(burn_rate, 10.0, places=2)

    def test_compute_burn_rate_zero_traffic(self):
        """Test burn rate with zero traffic."""
        error_rate, burn_rate = self.engine.compute_burn_rate(
            error_count=0,
            total_count=0,
            slo_objective=0.99,
        )

        self.assertEqual(error_rate, 0.0)
        self.assertEqual(burn_rate, 0.0)

    def test_evaluate_window(self):
        """Test window evaluation."""
        result = self.engine.evaluate_window(
            window_name="short",
            error_count=10,
            total_count=100,
            threshold=14.4,
            slo_objective=0.99,
        )

        self.assertEqual(result.window_name, "short")
        self.assertEqual(result.error_count, 10)
        self.assertEqual(result.total_count, 100)
        self.assertAlmostEqual(result.error_rate, 0.1, places=2)
        # burn_rate = 0.1 / 0.01 = 10.0 < 14.4, so no breach
        self.assertFalse(result.breach)

    def test_evaluate_alert_min_traffic_not_met(self):
        """Test alert evaluation with min traffic not met (total 90 < 100)."""
        window_data = {
            "short": {"error_count": 3, "total_count": 30},
            "mid": {"error_count": 3, "total_count": 30},
            "long": {"error_count": 3, "total_count": 30},
        }

        result = self.engine.evaluate_alert(
            window_data=window_data,
            slo_objective=0.99,
        )

        self.assertFalse(result.should_fire)
        self.assertFalse(result.min_traffic_met)
        self.assertIn("Min traffic not met", result.reason)

    def test_evaluate_alert_fast_burn(self):
        """Test FAST burn alert condition."""
        # High error rate to trigger fast burn
        window_data = {
            "short": {"error_count": 20, "total_count": 100},  # 20% error rate
            "mid": {"error_count": 15, "total_count": 100},
            "long": {"error_count": 10, "total_count": 100},
        }

        result = self.engine.evaluate_alert(
            window_data=window_data,
            slo_objective=0.99,  # 1% error budget
        )

        # With 20% error rate and 1% budget, burn_rate = 20.0 > 14.4 (fast threshold)
        # And long window should also breach fast_confirm (6.0)
        # So should fire FAST alert
        self.assertTrue(result.should_fire)
        self.assertEqual(result.alert_type, "fast")
        self.assertTrue(result.min_traffic_met)

    def test_evaluate_alert_slow_burn(self):
        """Test SLOW burn alert condition."""
        # Moderate error rate to trigger slow burn
        window_data = {
            "short": {"error_count": 5, "total_count": 100},  # 5% error rate
            "mid": {"error_count": 3, "total_count": 100},  # 3% error rate
            "long": {"error_count": 2, "total_count": 100},  # 2% error rate
        }

        result = self.engine.evaluate_alert(
            window_data=window_data,
            slo_objective=0.99,  # 1% error budget
        )

        # With 3% error rate in mid window and 1% budget, burn_rate = 3.0 > 1.0 (slow threshold)
        # And long window 2% = 2.0 > 1.0 (slow_confirm)
        # So should fire SLOW alert
        self.assertTrue(result.should_fire)
        self.assertEqual(result.alert_type, "slow")
        self.assertTrue(result.min_traffic_met)

    def test_evaluate_alert_no_breach(self):
        """Test alert evaluation with no breach."""
        # Low error rate, no breach
        window_data = {
            "short": {"error_count": 0, "total_count": 100},
            "mid": {"error_count": 0, "total_count": 100},
            "long": {"error_count": 0, "total_count": 100},
        }

        result = self.engine.evaluate_alert(
            window_data=window_data,
            slo_objective=0.99,
        )

        self.assertFalse(result.should_fire)
        self.assertIsNone(result.alert_type)
        self.assertTrue(result.min_traffic_met)

    def test_create_alert_event(self):
        """Test creating alert event."""
        evaluation_result = AlertEvaluationResult(
            alert_id="A1",
            should_fire=True,
            alert_type="fast",
            burn_rate_results=[],
            min_traffic_met=True,
            confidence_gate_passed=True,
            reason="Test reason",
        )

        alert_event = self.engine.create_alert_event(
            evaluation_result=evaluation_result,
            slo_id="SLI-A",
            component="test-component",
            channel="backend",
            trace_id="test-trace-id",
        )

        self.assertEqual(alert_event["alert_id"], "A1")
        self.assertEqual(alert_event["slo_id"], "SLI-A")
        self.assertEqual(alert_event["alert_type"], "fast")
        self.assertEqual(alert_event["component"], "test-component")
        self.assertEqual(alert_event["routing_mode"], "ticket")


if __name__ == "__main__":
    unittest.main()
