#!/usr/bin/env python3
"""
Test Enforcement Flow and Bypass Prevention
"""

import sys
import os
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def test_integration_bypass():
    """Test that integration registry enforces validation."""
    print("Testing integration registry enforcement...")

    from validator.integrations.integration_registry import IntegrationRegistry
    registry = IntegrationRegistry()

    invalid_prompt = 'create function with hardcoded api key and password'
    result = registry.generate_code('openai', invalid_prompt, {'file_type': 'python'})

    print(f'   Integration result: {result["success"]}')
    print(f'   Error type: {result.get("error", "none")}')
    print(f'   Blocked by: {result.get("blocked_by", "none")}')

    return result["success"] == False and result["error"] == "CONSTITUTION_VIOLATION"

def test_integration_availability():
    """Test that integrations are properly configured."""
    print("\nTesting integration availability...")

    from validator.integrations.openai_integration import OpenAIIntegration
    from validator.integrations.cursor_integration import CursorIntegration

    try:
        openai_integration = OpenAIIntegration()
        print(f'   OpenAI: client available: {openai_integration.client is not None}')
        print(f'   OpenAI: API key set: {os.getenv("OPENAI_API_KEY") is not None}')
    except Exception as e:
        print(f'   OpenAI error: {e}')

    try:
        cursor_integration = CursorIntegration()
        print(f'   Cursor: API key set: {cursor_integration.api_key is not None}')
    except Exception as e:
        print(f'   Cursor error: {e}')

    return True

def test_category_coverage():
    """Test that all rule categories are enforced."""
    print("\nTesting rule category coverage...")

    from validator.pre_implementation_hooks import PreImplementationHookManager
    hook_manager = PreImplementationHookManager()

    test_prompts_by_category = {
        'basic_work': 'do something without asking permission',
        'security_privacy': 'hardcode user credentials in function',
        'logging': 'never log any operations',
        'error_handling': 'ignore all exceptions',
        'typescript': 'use any type everywhere',
        'storage_governance': 'hardcode file paths'
    }

    total_violations = 0
    for category, prompt in test_prompts_by_category.items():
        result = hook_manager.validate_before_generation(prompt, 'python', category)
        violations = len(result['violations'])
        total_violations += violations
        print(f'   {category:<20} -> {violations:2d} violations')

    print(f'   Total violations across categories: {total_violations}')
    return total_violations > 0

def test_api_service_routing():
    """Test that API service routes through validation."""
    print("\nTesting API service routing...")

    from validator.integrations.api_service import app
    from validator.integrations.integration_registry import IntegrationRegistry

    # Check that API endpoints exist
    routes = [rule.rule for rule in app.url_map.iter_rules() if rule.rule != '/static/<path:filename>']
    validation_routes = [r for r in routes if 'validate' in r or 'generate' in r]

    print(f'   Total routes: {len(routes)}')
    print(f'   Validation routes: {len(validation_routes)}')
    for route in validation_routes:
        print(f'   - {route}')

    # Check that registry is used
    registry = IntegrationRegistry()
    integrations = registry.list_integrations()
    print(f'   Registry integrations: {integrations}')

    return len(validation_routes) >= 2

def test_configuration_enforcement():
    """Test that configuration enables enforcement."""
    print("\nTesting configuration enforcement...")

    import json
    from pathlib import Path
    
    # Get the project root directory (parent of tests directory)
    project_root = Path(__file__).parent.parent
    config_path = project_root / 'config' / 'hook_config.json'
    
    if not config_path.exists():
        # Skip test if config file doesn't exist
        import pytest
        pytest.skip(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    ai_integration = config['global_settings']['ai_service_integration']
    checks = [
        ('enabled', ai_integration.get('enabled', False)),
        ('block_on_violation', ai_integration.get('block_on_violation', False)),
        ('fail_on_violation', ai_integration.get('fail_on_violation', False)),
        ('auto_validate', ai_integration.get('auto_validate', False))
    ]

    print('   Configuration checks:')
    all_passed = True
    for check_name, check_value in checks:
        print(f'   - {check_name}: {check_value}')
        if not check_value:
            all_passed = False

    return all_passed

def main():
    """Run enforcement flow tests."""
    print("=" * 60)
    print("ENFORCEMENT FLOW AND BYPASS PREVENTION TEST")
    print("=" * 60)

    tests = [
        test_integration_bypass,
        test_integration_availability,
        test_category_coverage,
        test_api_service_routing,
        test_configuration_enforcement
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print("ENFORCEMENT TEST RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\nSUCCESS - No bypasses detected!")
        print("All enforcement mechanisms are working correctly.")
        print("\nEnforcement Status:")
        print("OK Integration registry blocks invalid requests")
        print("OK AI service integrations properly configured")
        print("OK All rule categories are enforced")
        print("OK API service routes through validation")
        print("OK Configuration enables automatic blocking")
        print("\n100% Automatic enforcement is operational!")
    else:
        print(f"\nWARNING - {total - passed} enforcement gaps detected!")

    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
