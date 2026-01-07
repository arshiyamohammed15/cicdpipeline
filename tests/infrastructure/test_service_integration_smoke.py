"""
Service Integration Smoke Test

Minimal integration harness that exercises validator/integrations/api_service.py
and edge/vscode storage flows together (no external calls), ensuring adapters
and rule counts stay synchronized before adding functional modules.
"""

import unittest
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import json

@pytest.mark.smoke
@pytest.mark.unit
class TestServiceIntegrationSmoke(unittest.TestCase):
    """Smoke test for service integration."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.zu_root = self.temp_dir / 'zu_root'
        self.zu_root.mkdir()

        import os
        self.original_zu_root = os.environ.get('ZU_ROOT')
        os.environ['ZU_ROOT'] = str(self.zu_root)

    def tearDown(self):
        """Clean up test environment."""
        import os
        if self.original_zu_root:
            os.environ['ZU_ROOT'] = self.original_zu_root
        elif 'ZU_ROOT' in os.environ:
            del os.environ['ZU_ROOT']

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_validator_integration_rule_counts_synchronized(self):
        """Test that validator and integrations use same rule counts."""
        from validator.integrations.api_service import hook_manager
        from config.constitution.rule_count_loader import get_rule_counts
        from validator.shared_health_stats import get_shared_rule_counts

        # Get rule counts from all sources
        api_enabled = hook_manager.total_rules
        loader_counts = get_rule_counts()
        shared_counts = get_shared_rule_counts()

        loader_enabled = loader_counts.get('enabled_rules', 0)
        shared_enabled = shared_counts.get('enabled_rules', 0)

        # Verify enabled rule counts agree
        self.assertEqual(api_enabled, loader_enabled,
                        "API service enabled rule count must match loader")
        self.assertEqual(api_enabled, shared_enabled,
                        "API service enabled rule count must match shared helper")
        self.assertEqual(loader_enabled, shared_enabled,
                        "Loader and shared helper enabled counts must agree")

        # Verify totals including disabled are also aligned
        api_total = getattr(hook_manager, "total_rules_including_disabled", api_enabled)
        loader_total = loader_counts.get('total_rules', loader_enabled)
        shared_total = shared_counts.get('total_rules', shared_enabled)
        self.assertEqual(len(set([api_total, loader_total, shared_total])), 1,
                        "Total rule counts (including disabled) must be synchronized")

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_validator_health_endpoint_parity(self):
        """Test that validator health endpoint uses shared helper."""
        from validator.health import get_health_endpoint
        from validator.shared_health_stats import get_health_response

        health_status = get_health_endpoint()
        shared_health = get_health_response(include_backend=True)

        # Verify rule counts match
        health_rules = health_status.get('summary', {}).get('total_rules', 0)
        shared_rules = shared_health.get('rule_counts', {}).get('total_rules', 0)

        self.assertEqual(health_rules, shared_rules,
                        "Health endpoint rule count must match shared helper")

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_integrations_stats_endpoint_parity(self):
        """Test that integrations stats endpoint uses shared helper."""
        from validator.integrations.api_service import app
        from validator.shared_health_stats import get_stats_response

        with app.test_client() as client:
            response = client.get('/stats')
            self.assertEqual(response.status_code, 200)
            stats_data = json.loads(response.data)

        shared_stats = get_stats_response(include_backend=True)

        # Verify rule counts match
        api_rules = stats_data.get('total_rules', 0)
        shared_rules = shared_stats.get('total_rules', 0)
        api_total = stats_data.get('total_rules_including_disabled', api_rules)
        shared_total = shared_stats.get('total_rules_including_disabled', shared_rules)

        self.assertEqual(api_rules, shared_rules,
                        "Stats endpoint rule count must match shared helper")
        self.assertEqual(api_total, shared_total,
                        "Stats endpoint total rules (including disabled) must match shared helper")

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_storage_resolver_contract(self):
        """Test that storage operations use BaseStoragePathResolver."""
        # Skip if BaseStoragePathResolver is not available
        import sys
        project_root = Path(__file__).resolve().parents[2]
        storage_path = project_root / 'src' / 'shared' / 'storage'
        
        if not (storage_path / 'BaseStoragePathResolver.py').exists():
            self.skipTest("BaseStoragePathResolver not found")
        
        sys.path.insert(0, str(storage_path))
        try:
            from BaseStoragePathResolver import BaseStoragePathResolver

            resolver = BaseStoragePathResolver(str(self.zu_root))

            # Test all resolver methods
            ide_path = resolver.resolveIdePath('test/path')
            tenant_path = resolver.resolveTenantPath('test/path')
            product_path = resolver.resolveProductPath('test/path')
            shared_path = resolver.resolveSharedPath('test/path')

            # Verify paths are constructed correctly
            self.assertIn('ide', ide_path)
            self.assertIn('tenant', tenant_path)
            self.assertIn('product', product_path)
            self.assertIn('shared', shared_path)

            # Verify ZU_ROOT is used
            self.assertIn(str(self.zu_root), ide_path)
        except ImportError:
            self.skipTest("BaseStoragePathResolver not available")

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_receipt_storage_flow(self):
        """Test receipt storage flow through resolver."""
        # Skip if BaseStoragePathResolver is not available
        import sys
        project_root = Path(__file__).resolve().parents[2]
        storage_path = project_root / 'src' / 'shared' / 'storage'
        
        if not (storage_path / 'BaseStoragePathResolver.py').exists():
            self.skipTest("BaseStoragePathResolver not found")
        
        sys.path.insert(0, str(storage_path))
        try:
            from BaseStoragePathResolver import BaseStoragePathResolver
            from datetime import datetime

            resolver = BaseStoragePathResolver(str(self.zu_root))
            year = datetime.utcnow().year
            month = datetime.utcnow().month

            receipt_path = resolver.resolveReceiptPath('test-repo', year, month)
            receipt_dir = Path(receipt_path)
            receipt_dir.mkdir(parents=True, exist_ok=True)

            # Verify path structure
            self.assertIn('receipts', receipt_path)
            self.assertIn('test-repo', receipt_path)
            self.assertTrue(receipt_dir.exists())
        except ImportError:
            self.skipTest("BaseStoragePathResolver not available")

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_backend_sync_status_in_health(self):
        """Test that health endpoints include backend sync status."""
        from validator.health import get_health_endpoint
        from validator.shared_health_stats import get_backend_status

        health_status = get_health_endpoint()
        backend_status = get_backend_status()

        # Verify backend status is included
        health_backend = health_status.get('checks', {}).get('backend_sync', {})
        self.assertIsNotNone(health_backend,
                            "Health endpoint must include backend sync status")

        # Verify synchronized status matches
        health_synced = health_backend.get('synchronized', False)
        backend_synced = backend_status.get('synchronized', False)

        self.assertEqual(health_synced, backend_synced,
                        "Health endpoint backend sync status must match shared helper")

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_rule_count_consistency_across_services(self):
        """Test that rule counts are consistent across all service layers."""
        from validator.integrations.api_service import hook_manager
        from config.constitution.rule_count_loader import get_rule_counts
        from validator.shared_health_stats import get_shared_rule_counts
        from validator.health import HealthChecker

        # Get counts from all sources
        api_enabled = hook_manager.total_rules
        loader_counts = get_rule_counts()
        shared_counts = get_shared_rule_counts()

        loader_enabled = loader_counts.get('enabled_rules', 0)
        shared_enabled = shared_counts.get('enabled_rules', 0)

        checker = HealthChecker()
        health_status = checker.get_health_status()
        health_enabled = health_status.get('summary', {}).get('total_rules', 0)

        # All enabled counts must agree
        counts = [api_enabled, loader_enabled, shared_enabled, health_enabled]
        self.assertEqual(len(set(counts)), 1,
                        f"Enabled rule counts must be consistent: API={api_enabled}, "
                        f"Loader={loader_enabled}, Shared={shared_enabled}, Health={health_enabled}")

        # Total (including disabled) counts should also agree for observability
        api_total = getattr(hook_manager, "total_rules_including_disabled", api_enabled)
        loader_total = loader_counts.get('total_rules', loader_enabled)
        shared_total = shared_counts.get('total_rules', shared_enabled)
        health_total = health_status.get('summary', {}).get('total_rules_including_disabled', health_enabled)

        totals = [api_total, loader_total, shared_total, health_total]
        self.assertEqual(len(set(totals)), 1,
                        f"Total rule counts must be consistent: API={api_total}, "
                        f"Loader={loader_total}, Shared={shared_total}, Health={health_total}")


if __name__ == '__main__':
    unittest.main()

