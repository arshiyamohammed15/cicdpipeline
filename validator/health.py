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


class HealthChecker:
    """Health check service for pre-implementation hooks."""
    
    def __init__(self, constitution_dir: str = "docs/constitution"):
        self.constitution_dir = Path(constitution_dir)
        self.hook_manager = PreImplementationHookManager(constitution_dir)
    
    def check_rule_count_consistency(self) -> Dict[str, Any]:
        """
        Verify rule count matches JSON files (single source of truth).
        
        Returns:
            Dict with 'healthy', 'expected_count', 'actual_count', 'json_files'
        """
        # Count from JSON files
        json_files = sorted(list(self.constitution_dir.glob("*.json")))
        expected_count = 0
        file_counts = {}
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    rules = data.get('constitution_rules', [])
                    enabled = sum(1 for r in rules if r.get('enabled', True))
                    expected_count += enabled
                    file_counts[json_file.name] = enabled
            except Exception as e:
                return {
                    'healthy': False,
                    'error': f"Failed to read {json_file.name}: {e}",
                    'expected_count': None,
                    'actual_count': None,
                    'json_files': []
                }
        
        # Get count from hook manager
        actual_count = self.hook_manager.total_rules
        
        healthy = (expected_count == actual_count)
        
        return {
            'healthy': healthy,
            'expected_count': expected_count,
            'actual_count': actual_count,
            'json_files': {
                'count': len(json_files),
                'files': list(file_counts.keys()),
                'rules_per_file': file_counts
            },
            'message': 'Rule count matches JSON files' if healthy else f'Rule count mismatch: expected {expected_count}, got {actual_count}'
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
        
        overall_healthy = (
            rule_count_check['healthy'] and
            json_files_check['healthy'] and
            hook_manager_check['healthy']
        )
        
        return {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'checks': {
                'rule_count_consistency': rule_count_check,
                'json_files_accessible': json_files_check,
                'hook_manager_functional': hook_manager_check
            },
            'summary': {
                'total_rules': self.hook_manager.total_rules,
                'json_files_count': json_files_check['total_files'],
                'constitution_dir': str(self.constitution_dir)
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

