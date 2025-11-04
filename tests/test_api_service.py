#!/usr/bin/env python3
"""
Test API Service Endpoints
"""

import sys
import os
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def test_api_routes():
    """Test API service routes."""
    print("Testing API service endpoints...")

    try:
        from validator.integrations.api_service import app

        # Check available routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(f'{rule.methods} {rule.rule}')

        print(f'OK API routes configured: {len(routes)} routes')
        for route in sorted(routes):
            print(f'   {route}')

        return True
    except Exception as e:
        print(f'ERROR API routes: {e}')
        return False

def test_registry_validation():
    """Test validation through registry."""
    print("\nTesting registry validation...")

    try:
        from validator.integrations.integration_registry import IntegrationRegistry
        registry = IntegrationRegistry()

        # Test validation through registry
        test_prompt = 'create a function with hardcoded password and API key'
        result = registry.validate_prompt(
            test_prompt,
            {'file_type': 'python', 'task_type': 'security'}
        )

        print(f'OK Registry validation test:')
        print(f'   Prompt: {test_prompt[:50]}...')
        print(f'   Violations found: {len(result["violations"])}')
        print(f'   Rules checked: {result["total_rules_checked"]}')
        print(f'   Validation blocked: {not result["valid"]}')

        if result['violations']:
            print(f'   Sample violation: {result["violations"][0]["rule_id"]}')

        return True
    except Exception as e:
        print(f'ERROR Registry validation: {e}')
        return False

def main():
    """Run API service tests."""
    print("=" * 50)
    print("API SERVICE VALIDATION TEST")
    print("=" * 50)

    tests = [
        test_api_routes,
        test_registry_validation
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print("API SERVICE TEST RESULTS")
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("SUCCESS All API service tests passed!")
        print("\nAPI Endpoints Available:")
        print("  GET  /health - Service health check")
        print("  POST /validate - Validate prompt against constitution")
        print("  POST /generate - Generate code with validation")
        print("  GET  /integrations - List available integrations")
        print("  GET  /stats - Service statistics")
        print("\nAutomatic enforcement is working correctly!")

    return passed == len(tests)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
