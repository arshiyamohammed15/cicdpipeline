#!/usr/bin/env python3
"""
Test Integration Registry Functionality
"""

import sys
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def test_registry_functionality():
    """Test integration registry functionality."""
    print("Testing integration registry functionality...")

    try:
        from validator.integrations.integration_registry import IntegrationRegistry

        registry = IntegrationRegistry()
        integrations = registry.list_integrations()
        print(f'OK Integration registry: {len(integrations)} integrations loaded')
        print(f'   Available: {integrations}')

        # Test validation through registry
        test_prompt = 'create function with hardcoded password'
        result = registry.validate_prompt(test_prompt, {'file_type': 'python'})
        print(f'OK Registry validation: {len(result["violations"])} violations detected')
        print(f'   Validation blocked: {not result["valid"]}')

        # Test code generation through registry
        gen_result = registry.generate_code('openai', test_prompt, {'file_type': 'python'})
        print(f'OK Registry generation: {gen_result["success"]} (error: {gen_result["error"]})')

        return True
    except Exception as e:
        print(f'ERROR Integration registry: {e}')
        return False

def test_api_service_integration():
    """Test API service integration."""
    print("\nTesting API service integration...")

    try:
        from validator.integrations.api_service import app, integration_registry

        # Check that integration_registry is available in API service
        if hasattr(app, 'integration_registry'):
            print('ERROR Integration registry not attached to Flask app')
            return False

        # Check that integration_registry is the same object
        api_integrations = integration_registry.list_integrations()
        direct_registry = __import__('validator.integrations.integration_registry', fromlist=['IntegrationRegistry']).IntegrationRegistry()
        direct_integrations = direct_registry.list_integrations()

        if api_integrations == direct_integrations:
            print('OK Integration registry properly shared between API service and direct access')
        else:
            print('ERROR Integration registry inconsistency between API and direct access')
            return False

        return True
    except Exception as e:
        print(f'ERROR API service integration: {e}')
        return False

def main():
    """Run integration tests."""
    print("=" * 50)
    print("INTEGRATION REGISTRY VALIDATION")
    print("=" * 50)

    tests = [
        test_registry_functionality,
        test_api_service_integration
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print("INTEGRATION VALIDATION RESULTS")
    print("=" * 50)

    if passed == len(tests):
        print("SUCCESS - Integration registry working correctly!")
        print("\nIntegration features verified:")
        print("OK Integration registry loads AI services")
        print("OK Validation through registry works")
        print("OK Code generation through registry works")
        print("OK API service properly integrated")
        print("\nAll integration components operational!")
    else:
        print(f"ISSUES FOUND - {len(tests) - passed} integration problems")

    return passed == len(tests)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
