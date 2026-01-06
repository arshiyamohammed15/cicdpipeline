"""
Health Check Endpoint for Pre-Implementation Hooks

Provides runtime health checks that verify:
- Rule count matches JSON files (single source of truth)
- All JSON files are accessible
- Hook manager is functioning correctly
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from .pre_implementation_hooks import PreImplementationHookManager
from .shared_health_stats import get_shared_rule_counts, get_backend_status
from config.constitution.rule_count_loader import get_rule_counts


class HealthChecker:
    """Health check service for pre-implementation hooks."""

    def __init__(self, constitution_dir: str = "docs/constitution"):
        self.constitution_dir = Path(constitution_dir)
        if not self.constitution_dir.is_absolute():
            repo_root = Path(__file__).resolve().parents[1]
            self.constitution_dir = (repo_root / self.constitution_dir).resolve()
        self.hook_manager = PreImplementationHookManager(constitution_dir)

    def check_rule_count_consistency(self) -> Dict[str, Any]:
        """
        Verify rule count matches JSON files (single source of truth).

        Returns:
            Dict with 'healthy', 'expected_count', 'actual_count', 'json_files'
        """
        # Count from JSON files
        json_files = sorted(list(self.constitution_dir.glob("*.json")))
        enabled_count = 0
        disabled_count = 0
        file_counts = {}

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rules = data.get('constitution_rules', [])
                    total_rules_in_file = len(rules)
                    enabled_in_file = sum(1 for rule in rules if rule.get("enabled", True))
                    disabled_in_file = total_rules_in_file - enabled_in_file

                    enabled_count += enabled_in_file
                    disabled_count += disabled_in_file
                    file_counts[json_file.name] = {
                        'total': total_rules_in_file,
                        'enabled': enabled_in_file,
                        'disabled': disabled_in_file,
                    }
            except Exception as e:
                return {
                    'healthy': False,
                    'error': f"Failed to read {json_file.name}: {e}",
                    'expected_count': None,
                    'actual_count': None,
                    'json_files': []
                }

        # Use rule count loader as authoritative source
        loader_counts = get_rule_counts(str(self.constitution_dir))
        loader_enabled = loader_counts.get('enabled_rules', enabled_count)
        loader_disabled = loader_counts.get('disabled_rules', disabled_count)

        # Get count from hook manager (enabled rules only)
        actual_enabled = self.hook_manager.total_rules
        healthy = (loader_enabled == actual_enabled)

        return {
            'healthy': healthy,
            'expected_count': loader_enabled,
            'actual_count': actual_enabled,
            'json_files': {
                'count': len(json_files),
                'files': list(file_counts.keys()),
                'rules_per_file': file_counts
            },
            'totals': {
                'enabled': loader_enabled,
                'disabled': loader_disabled,
                'all_files_enabled': enabled_count,
                'all_files_disabled': disabled_count,
            },
            'message': 'Rule count matches JSON files' if healthy else f'Rule count mismatch: expected {loader_enabled}, got {actual_enabled}'
        }

    def check_json_files_accessible(self) -> Dict[str, Any]:
        """
        Verify all JSON files in constitution directory are accessible.

        Returns:
            Dict with 'healthy', 'accessible_files', 'missing_files'
        """
        json_files = sorted(list(self.constitution_dir.glob("*.json")))
        accessible = []
        missing = []

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json.load(f)  # Try to parse
                accessible.append(json_file.name)
            except Exception as e:
                missing.append({
                    'file': json_file.name,
                    'error': str(e)
                })

        healthy = len(missing) == 0

        return {
            'healthy': healthy,
            'accessible_files': accessible,
            'missing_files': missing,
            'total_files': len(json_files),
            'message': f'All {len(json_files)} JSON files accessible' if healthy else f'{len(missing)} files have issues'
        }

    def check_hook_manager_functional(self) -> Dict[str, Any]:
        """
        Verify hook manager can validate prompts.

        Returns:
            Dict with 'healthy', 'test_result'
        """
        try:
            # Test with a simple prompt
            test_prompt = "create a function"
            result = self.hook_manager.validate_before_generation(test_prompt)

            # Verify result structure
            required_keys = ['valid', 'violations', 'total_rules_checked', 'recommendations']
            missing_keys = [key for key in required_keys if key not in result]

            if missing_keys:
                return {
                    'healthy': False,
                    'error': f'Missing keys in result: {missing_keys}',
                    'test_result': None
                }

            # Verify total_rules_checked matches hook manager
            if result['total_rules_checked'] != self.hook_manager.total_rules:
                return {
                    'healthy': False,
                    'error': f'Rule count mismatch in validation result',
                    'test_result': result
                }

            return {
                'healthy': True,
                'test_result': {
                    'valid': result['valid'],
                    'violations_count': len(result['violations']),
                    'rules_checked': result['total_rules_checked']
                },
                'message': 'Hook manager is functional'
            }
        except Exception as e:
            return {
                'healthy': False,
                'error': str(e),
                'test_result': None
            }

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status.

        Returns:
            Dict with all health checks and overall status
        """
        rule_count_check = self.check_rule_count_consistency()
        json_files_check = self.check_json_files_accessible()
        hook_manager_check = self.check_hook_manager_functional()
        
        # Use shared rule counts for consistency
        shared_counts = get_shared_rule_counts()
        backend_status = get_backend_status()

        summary_enabled = shared_counts.get('enabled_rules', self.hook_manager.total_rules)
        summary_total = shared_counts.get(
            'total_rules',
            summary_enabled + shared_counts.get('disabled_rules', self.hook_manager.disabled_rules)
        )

        overall_healthy = (
            rule_count_check['healthy'] and
            json_files_check['healthy'] and
            hook_manager_check['healthy'] and
            backend_status.get('synchronized', False)
        )

        return {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'checks': {
                'rule_count_consistency': rule_count_check,
                'json_files_accessible': json_files_check,
                'hook_manager_functional': hook_manager_check,
                'backend_sync': backend_status
            },
            'summary': {
                'total_rules': summary_enabled,
                'total_rules_including_disabled': summary_total,
                'enabled_rules': summary_enabled,
                'disabled_rules': shared_counts.get('disabled_rules', self.hook_manager.disabled_rules),
                'json_files_count': json_files_check['total_files'],
                'constitution_dir': str(self.constitution_dir),
                'backend_synchronized': backend_status.get('synchronized', False)
            }
        }


def get_health_endpoint() -> Dict[str, Any]:
    """
    Health endpoint function for API integration.

    Returns:
        Health status dict
    """
    checker = HealthChecker()
    return checker.get_health_status()
