"""
Test for OBS-10: Hot-reload functionality for alert configs.

Tests runtime reload support for alert configurations.
"""

import json
import tempfile
import unittest
from pathlib import Path

from ..alert_config import AlertConfigLoader


class TestAlertConfigHotReload(unittest.TestCase):
    """Test hot-reload functionality for alert configs."""

    def test_reload_config_runtime_update(self):
        """Test that reload_config updates config at runtime."""
        loader = AlertConfigLoader()

        # Initial config
        initial_config_dict = {
            "alert_id": "A1",
            "slo_id": "SLI-A",
            "objective": "Initial objective",
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

        # Create initial config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(initial_config_dict, f)
            config_path = Path(f.name)

        try:
            # Load initial config
            initial_config = loader.load_from_file(config_path)
            self.assertEqual(initial_config.objective, "Initial objective")
            self.assertEqual(initial_config.min_traffic.min_total_events, 100)

            # Update config file
            updated_config_dict = initial_config_dict.copy()
            updated_config_dict["objective"] = "Updated objective"
            updated_config_dict["min_traffic"]["min_total_events"] = 200

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(updated_config_dict, f)

            # Reload config
            reloaded_config = loader.reload_config("A1", config_path)
            self.assertEqual(reloaded_config.objective, "Updated objective")
            self.assertEqual(reloaded_config.min_traffic.min_total_events, 200)

            # Verify config is updated in loader
            retrieved_config = loader.get_config("A1")
            self.assertIsNotNone(retrieved_config)
            self.assertEqual(retrieved_config.objective, "Updated objective")
            self.assertEqual(retrieved_config.min_traffic.min_total_events, 200)

        finally:
            config_path.unlink()

    def test_reload_config_alert_id_mismatch(self):
        """Test that reload_config raises error on alert_id mismatch."""
        loader = AlertConfigLoader()

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
            # Load initial config
            loader.load_from_file(config_path)

            # Try to reload with wrong alert_id
            with self.assertRaises(ValueError) as context:
                loader.reload_config("A999", config_path)

            self.assertIn("alert_id mismatch", str(context.exception))

        finally:
            config_path.unlink()

    def test_reload_config_invalid_file(self):
        """Test that reload_config validates config on reload."""
        loader = AlertConfigLoader()

        # Create invalid config file
        invalid_config_dict = {
            "alert_id": "A1",
            # Missing required fields
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(invalid_config_dict, f)
            config_path = Path(f.name)

        try:
            # Try to reload invalid config
            with self.assertRaises(ValueError) as context:
                loader.reload_config("A1", config_path)

            self.assertIn("Invalid alert config", str(context.exception))

        finally:
            config_path.unlink()


if __name__ == "__main__":
    unittest.main()
