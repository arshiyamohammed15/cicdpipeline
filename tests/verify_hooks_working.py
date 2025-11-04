#!/usr/bin/env python3
"""
Quick Verification Script for Pre-Implementation Hooks

This script provides a quick way to verify that pre-implementation hooks
are working correctly. Run this before any code generation to ensure hooks are active.

Usage:
    python tests/verify_hooks_working.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def verify_rule_loading():
    """Verify that all rules are loaded."""
    print("1. Verifying rule loading...")
    try:
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()
        
        if hook_manager.total_rules == 424:
            print(f"   [OK] Loaded {hook_manager.total_rules} enabled rules")
            return True
        else:
            print(f"   [FAIL] Expected 424 rules, got {hook_manager.total_rules}")
            return False
    except Exception as e:
        print(f"   [FAIL] Error loading rules: {e}")
        return False


def verify_violation_detection():
    """Verify that violations are detected."""
    print("\n2. Verifying violation detection...")
    try:
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()
        
        # Test with known violation
        test_prompt = "create a function with hardcoded password = 'secret123'"
        result = hook_manager.validate_before_generation(test_prompt)
        
        if not result['valid'] and len(result['violations']) > 0:
            print(f"   [OK] Detected {len(result['violations'])} violations")
            print(f"   [OK] Rules checked: {result['total_rules_checked']}")
            return True
        else:
            print(f"   [FAIL] Failed to detect violations")
            return False
    except Exception as e:
        print(f"   [FAIL] Error detecting violations: {e}")
        return False


def verify_blocking():
    """Verify that generation is blocked when violations are found."""
    print("\n3. Verifying blocking behavior...")
    try:
        from validator.integrations.integration_registry import IntegrationRegistry
        registry = IntegrationRegistry()
        
        invalid_prompt = "create function with hardcoded password"
        result = registry.validate_prompt(
            invalid_prompt,
            {'file_type': 'python', 'task_type': 'general'}
        )
        
        if not result['valid']:
            print(f"   [OK] Generation blocked for invalid prompt")
            return True
        else:
            print(f"   [FAIL] Generation not blocked for invalid prompt")
            return False
    except Exception as e:
        print(f"   [FAIL] Error verifying blocking: {e}")
        return False


def verify_integration_points():
    """Verify all integration points are active."""
    print("\n4. Verifying integration points...")
    try:
        from validator.integrations.ai_service_wrapper import AIServiceIntegration
        from validator.integrations.openai_integration import OpenAIIntegration
        from validator.integrations.cursor_integration import CursorIntegration
        from validator.integrations.api_service import app
        
        # Check OpenAI integration
        openai_integration = OpenAIIntegration()
        if hasattr(openai_integration, 'hook_manager'):
            print("   [OK] OpenAI integration has hook manager")
        else:
            print("   [FAIL] OpenAI integration missing hook manager")
            return False
        
        # Check Cursor integration
        cursor_integration = CursorIntegration()
        if hasattr(cursor_integration, 'hook_manager'):
            print("   [OK] Cursor integration has hook manager")
        else:
            print("   [FAIL] Cursor integration missing hook manager")
            return False
        
        # Check API routes
        routes = [str(rule.rule) for rule in app.url_map.iter_rules()]
        if '/validate' in routes and '/generate' in routes:
            print("   [OK] API service has validation endpoints")
        else:
            print("   [FAIL] API service missing validation endpoints")
            return False
        
        return True
    except Exception as e:
        print(f"   [FAIL] Error verifying integration points: {e}")
        return False


def verify_rule_count_accuracy():
    """Verify rule count matches JSON files."""
    print("\n5. Verifying rule count accuracy...")
    try:
        import json
        from pathlib import Path
        
        constitution_dir = Path("docs/constitution")
        json_files = list(constitution_dir.glob("*.json"))
        
        total_enabled = 0
        for json_file in json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rules = data.get('constitution_rules', [])
                enabled = sum(1 for r in rules if r.get('enabled', True))
                total_enabled += enabled
        
        if total_enabled == 424:
            print(f"   [OK] JSON files have {total_enabled} enabled rules")
            return True
        else:
            print(f"   [FAIL] JSON files have {total_enabled} enabled rules, expected 424")
            return False
    except Exception as e:
        print(f"   [FAIL] Error verifying rule count: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 80)
    print("PRE-IMPLEMENTATION HOOKS VERIFICATION")
    print("=" * 80)
    print()
    
    checks = [
        verify_rule_loading,
        verify_violation_detection,
        verify_blocking,
        verify_integration_points,
        verify_rule_count_accuracy
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print()
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nChecks passed: {passed}/{total}")
    
    if passed == total:
        print("\n[SUCCESS] All verification checks passed!")
        print("  Pre-implementation hooks are working correctly.")
        print("  Code generation will be blocked when violations are detected.")
        return True
    else:
        print(f"\n[FAILURE] {total - passed} checks failed!")
        print("  Review the output above to identify issues.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

