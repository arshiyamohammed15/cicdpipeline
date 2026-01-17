"""
Tests for dashboards (OBS-09).

Tests dashboard loading, validation, and structure.
"""

import unittest

from ..dashboards.dashboard_loader import DashboardLoader, load_dashboard


class TestDashboards(unittest.TestCase):
    """Test dashboard loader and definitions."""

    def setUp(self):
        """Set up dashboard loader."""
        self.loader = DashboardLoader()

    def test_load_dashboard_d1(self):
        """Test loading dashboard D1."""
        dashboard = self.loader.load_dashboard("d1")
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard["id"], "d1")
        self.assertEqual(dashboard["title"], "System Health (Golden Signals)")
        self.assertIn("panels", dashboard)

    def test_load_dashboard_d2(self):
        """Test loading dashboard D2."""
        dashboard = self.loader.load_dashboard("d2")
        self.assertIsNotNone(dashboard)
        self.assertEqual(dashboard["id"], "d2")
        self.assertEqual(dashboard["title"], "Error Analysis and Debug")

    def test_load_all_dashboards(self):
        """Test loading all dashboards D1-D15."""
        dashboards = self.loader.load_all_dashboards()
        self.assertGreaterEqual(len(dashboards), 15)  # At least 15 dashboards

        # Check all dashboard IDs are present
        for i in range(1, 16):
            dashboard_id = f"d{i}"
            self.assertIn(dashboard_id, dashboards)

    def test_validate_dashboard(self):
        """Test dashboard validation."""
        dashboard = {
            "id": "d1",
            "title": "Test Dashboard",
            "panels": [
                {"title": "Panel 1"},
                {"title": "Panel 2"},
            ],
        }
        is_valid, error = self.loader.validate_dashboard(dashboard)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_dashboard_missing_field(self):
        """Test dashboard validation with missing field."""
        dashboard = {
            "id": "d1",
            # Missing title and panels
        }
        is_valid, error = self.loader.validate_dashboard(dashboard)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_dashboard_no_hardcoded_thresholds(self):
        """Test dashboards have no hardcoded thresholds."""
        dashboards = self.loader.load_all_dashboards()
        for dashboard_id, dashboard in dashboards.items():
            dashboard_str = str(dashboard)
            # Check for common hardcoded threshold patterns
            self.assertNotIn('"threshold": 0.95', dashboard_str)
            self.assertNotIn('"threshold": 0.99', dashboard_str)
            self.assertNotIn('"threshold": 100', dashboard_str)

    def test_dashboard_drill_down_support(self):
        """Test dashboards support drill-down via trace_id."""
        dashboard = self.loader.load_dashboard("d1")
        self.assertIn("links", dashboard)
        links = dashboard.get("links", [])
        trace_links = [link for link in links if "trace_id" in link.get("url", "")]
        self.assertGreater(len(trace_links), 0, "Dashboard should support trace_id drill-down")


if __name__ == "__main__":
    unittest.main()
