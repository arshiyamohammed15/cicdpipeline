"""
Tests for collector pipeline (OBS-04).

Tests collector configuration loading, validation, and storage path resolution.
"""

import os
import unittest
from pathlib import Path

from ..collector.collector_utils import (
    load_collector_config,
    resolve_storage_path,
    validate_collector_config,
)


class TestCollectorPipeline(unittest.TestCase):
    """Test collector pipeline configuration and utilities."""

    def setUp(self):
        """Set up test environment."""
        # Set ZU_ROOT for tests
        os.environ["ZU_ROOT"] = "D:\\ZeroUI\\test"

    def test_load_collector_config(self):
        """Test loading collector configuration."""
        config = load_collector_config()
        self.assertIsInstance(config, dict)
        self.assertIn("receivers", config)
        self.assertIn("processors", config)
        self.assertIn("exporters", config)
        self.assertIn("service", config)

    def test_resolve_storage_path_ide(self):
        """Test storage path resolution for IDE plane."""
        path = resolve_storage_path("ide", "metrics", date="2026-01-17")
        self.assertIn("ide/telemetry/metrics", path)
        self.assertIn("dt=2026-01-17", path)

    def test_resolve_storage_path_tenant(self):
        """Test storage path resolution for tenant plane."""
        path = resolve_storage_path(
            "tenant", "traces", tenant_id="tenant-123", region="us-east-1", date="2026-01-17"
        )
        self.assertIn("tenant/tenant-123/us-east-1/telemetry/traces", path)
        self.assertIn("dt=2026-01-17", path)

    def test_resolve_storage_path_product(self):
        """Test storage path resolution for product plane."""
        path = resolve_storage_path("product", "logs", region="us-east-1", date="2026-01-17")
        self.assertIn("product/us-east-1/telemetry/logs", path)
        self.assertIn("dt=2026-01-17", path)

    def test_resolve_storage_path_shared(self):
        """Test storage path resolution for shared plane."""
        path = resolve_storage_path(
            "shared", "metrics", org_id="org-456", region="us-east-1", date="2026-01-17"
        )
        self.assertIn("shared/org-456/us-east-1/telemetry/metrics", path)
        self.assertIn("dt=2026-01-17", path)

    def test_resolve_storage_path_invalid_plane(self):
        """Test storage path resolution with invalid plane."""
        with self.assertRaises(ValueError):
            resolve_storage_path("invalid", "metrics")

    def test_resolve_storage_path_missing_tenant_id(self):
        """Test storage path resolution for tenant plane without tenant_id."""
        with self.assertRaises(ValueError):
            resolve_storage_path("tenant", "metrics")

    def test_resolve_storage_path_missing_org_id(self):
        """Test storage path resolution for shared plane without org_id."""
        with self.assertRaises(ValueError):
            resolve_storage_path("shared", "metrics")

    def test_validate_collector_config_valid(self):
        """Test validation of valid collector config."""
        config = {
            "receivers": {"otlp": {}},
            "processors": {"batch": {}},
            "exporters": {"otlp/traces": {}},
            "service": {
                "pipelines": {
                    "traces": {
                        "receivers": ["otlp"],
                        "exporters": ["otlp/traces"],
                    },
                    "metrics": {
                        "receivers": ["otlp"],
                        "exporters": ["otlp/metrics"],
                    },
                    "logs": {
                        "receivers": ["otlp"],
                        "exporters": ["otlp/logs"],
                    },
                }
            },
        }
        is_valid, error = validate_collector_config(config)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_collector_config_missing_section(self):
        """Test validation of config with missing section."""
        config = {
            "receivers": {"otlp": {}},
            # Missing processors, exporters, service
        }
        is_valid, error = validate_collector_config(config)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_collector_config_missing_pipeline(self):
        """Test validation of config with missing pipeline."""
        config = {
            "receivers": {"otlp": {}},
            "processors": {"batch": {}},
            "exporters": {"otlp/traces": {}},
            "service": {
                "pipelines": {
                    "traces": {
                        "receivers": ["otlp"],
                        "exporters": ["otlp/traces"],
                    },
                    # Missing metrics and logs pipelines
                }
            },
        }
        is_valid, error = validate_collector_config(config)
        self.assertFalse(is_valid)
        self.assertIn("Missing required pipeline", error or "")


if __name__ == "__main__":
    unittest.main()
