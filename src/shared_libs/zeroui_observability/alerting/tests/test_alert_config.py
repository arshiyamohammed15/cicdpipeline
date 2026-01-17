"""
Tests for OBS-10: Alert Config Contract + Loader.
"""

import json
import tempfile
import unittest
from pathlib import Path

from ..alert_config import (
    AlertConfig,
    AlertConfigLoader,
    BurnRateConfig,
    ConfidenceGateConfig,
    MinTrafficConfig,
    RoutingConfig,
    WindowConfig,
    load_alert_config,
)


class TestAlertConfig(unittest.TestCase):
    """Test AlertConfig dataclass."""

    def test_alert_config_from_dict(self):
        """Test creating AlertConfig from dictionary."""
        config_dict = {
            "alert_id": "A1",
            "slo_id": "SLI-A",
            "objective": "Test objective",
            "windows": {
                "short": "PT5M",
                "mid": "PT30M",
                "long": "PT2H",
            },
            "burn_rate": {
                "fast": 14.4,
                "fast_confirm": 6.0,
                "slow": 1.0,
                "slow_confirm": 1.0,
            },
            "min_traffic": {
                "min_total_events": 100,
            },
            "routing": {
                "mode": "ticket",
                "target": "zeroui-oncall-tickets",
            },
        }

        config = AlertConfig.from_dict(config_dict)
        self.assertEqual(config.alert_id, "A1")
        self.assertEqual(config.slo_id, "SLI-A")
        self.assertEqual(config.windows.short, "PT5M")
        self.assertEqual(config.burn_rate.fast, 14.4)
        self.assertEqual(config.routing.mode, "ticket")

    def test_alert_config_with_confidence_gate(self):
        """Test AlertConfig with confidence gate."""
        config_dict = {
            "alert_id": "A6",
            "slo_id": "SLI-F",
            "objective": "Bias detection",
            "windows": {
                "short": "PT10M",
                "mid": "PT1H",
                "long": "PT6H",
            },
            "burn_rate": {
                "fast": 14.4,
                "fast_confirm": 6.0,
                "slow": 1.0,
                "slow_confirm": 1.0,
            },
            "min_traffic": {
                "min_total_events": 20,
            },
            "confidence_gate": {
                "enabled": True,
                "min_confidence": 0.8,
            },
            "routing": {
                "mode": "ticket",
                "target": "zeroui-bias-review-tickets",
            },
        }

        config = AlertConfig.from_dict(config_dict)
        self.assertIsNotNone(config.confidence_gate)
        self.assertTrue(config.confidence_gate.enabled)
        self.assertEqual(config.confidence_gate.min_confidence, 0.8)

    def test_alert_config_to_dict(self):
        """Test converting AlertConfig to dictionary."""
        windows = WindowConfig(short="PT5M", mid="PT30M", long="PT2H")
        burn_rate = BurnRateConfig(fast=14.4, fast_confirm=6.0, slow=1.0, slow_confirm=1.0)
        min_traffic = MinTrafficConfig(min_total_events=100)
        routing = RoutingConfig(mode="ticket", target="zeroui-oncall-tickets")

        config = AlertConfig(
            alert_id="A1",
            slo_id="SLI-A",
            objective="Test objective",
            windows=windows,
            burn_rate=burn_rate,
            min_traffic=min_traffic,
            routing=routing,
        )

        config_dict = config.to_dict()
        self.assertEqual(config_dict["alert_id"], "A1")
        self.assertEqual(config_dict["windows"]["short"], "PT5M")
        self.assertEqual(config_dict["routing"]["mode"], "ticket")


class TestAlertConfigLoader(unittest.TestCase):
    """Test AlertConfigLoader."""

    def setUp(self):
        """Set up test fixtures."""
        self.loader = AlertConfigLoader()

    def test_validate_valid_config(self):
        """Test validating a valid config."""
        config_dict = {
            "alert_id": "A1",
            "slo_id": "SLI-A",
            "objective": "Test objective",
            "windows": {
                "short": "PT5M",
                "mid": "PT30M",
                "long": "PT2H",
            },
            "burn_rate": {
                "fast": 14.4,
                "fast_confirm": 6.0,
                "slow": 1.0,
                "slow_confirm": 1.0,
            },
            "min_traffic": {
                "min_total_events": 100,
            },
            "routing": {
                "mode": "ticket",
                "target": "zeroui-oncall-tickets",
            },
        }

        is_valid, error_msg = self.loader.validate_config(config_dict)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_invalid_config_missing_required(self):
        """Test validating config with missing required fields."""
        config_dict = {
            "alert_id": "A1",
            # Missing slo_id, objective, etc.
        }

        is_valid, error_msg = self.loader.validate_config(config_dict)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error_msg)

    def test_load_from_dict(self):
        """Test loading config from dictionary."""
        config_dict = {
            "alert_id": "A1",
            "slo_id": "SLI-A",
            "objective": "Test objective",
            "windows": {
                "short": "PT5M",
                "mid": "PT30M",
                "long": "PT2H",
            },
            "burn_rate": {
                "fast": 14.4,
                "fast_confirm": 6.0,
                "slow": 1.0,
                "slow_confirm": 1.0,
            },
            "min_traffic": {
                "min_total_events": 100,
            },
            "routing": {
                "mode": "ticket",
                "target": "zeroui-oncall-tickets",
            },
        }

        config = self.loader.load_from_dict(config_dict)
        self.assertEqual(config.alert_id, "A1")
        self.assertEqual(config.slo_id, "SLI-A")

    def test_load_from_file(self):
        """Test loading config from file."""
        config_dict = {
            "alert_id": "A1",
            "slo_id": "SLI-A",
            "objective": "Test objective",
            "windows": {
                "short": "PT5M",
                "mid": "PT30M",
                "long": "PT2H",
            },
            "burn_rate": {
                "fast": 14.4,
                "fast_confirm": 6.0,
                "slow": 1.0,
                "slow_confirm": 1.0,
            },
            "min_traffic": {
                "min_total_events": 100,
            },
            "routing": {
                "mode": "ticket",
                "target": "zeroui-oncall-tickets",
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_dict, f)
            config_path = Path(f.name)

        try:
            config = self.loader.load_from_file(config_path)
            self.assertEqual(config.alert_id, "A1")
            self.assertEqual(config.slo_id, "SLI-A")
        finally:
            config_path.unlink()

    def test_get_config(self):
        """Test retrieving config by alert_id."""
        config_dict = {
            "alert_id": "A1",
            "slo_id": "SLI-A",
            "objective": "Test objective",
            "windows": {
                "short": "PT5M",
                "mid": "PT30M",
                "long": "PT2H",
            },
            "burn_rate": {
                "fast": 14.4,
                "fast_confirm": 6.0,
                "slow": 1.0,
                "slow_confirm": 1.0,
            },
            "min_traffic": {
                "min_total_events": 100,
            },
            "routing": {
                "mode": "ticket",
                "target": "zeroui-oncall-tickets",
            },
        }

        self.loader.load_from_dict(config_dict)
        config = self.loader.get_config("A1")
        self.assertIsNotNone(config)
        self.assertEqual(config.alert_id, "A1")

        # Non-existent config
        config = self.loader.get_config("A999")
        self.assertIsNone(config)


if __name__ == "__main__":
    unittest.main()
