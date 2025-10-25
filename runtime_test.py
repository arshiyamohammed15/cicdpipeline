#!/usr/bin/env python3
"""
Runtime Test for Actual Errors
"""

import sys
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def test_validation_service():
    """Test validation service startup."""
    print("Testing validation service startup...")

    try:
        from tools.start_validation_service import main
        print("   Validation service startup function available")
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_enhanced_cli():
    """Test enhanced CLI."""
    print("\nTesting enhanced CLI...")

    try:
        from tools.enhanced_cli import EnhancedCLI
        cli = EnhancedCLI()
        print("   Enhanced CLI class instantiated successfully")
        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_actual_validation():
    """Test actual validation with problematic input."""
    print("\nTesting actual validation...")

    try:
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()

        # Test with a problematic prompt
        test_prompt = 'create function with hardcoded password and api key'
        result = hook_manager.validate_before_generation(test_prompt, 'python', 'security')

        print(f"   Validation result: {result['valid']}")
        print(f"   Violations: {len(result['violations'])}")
        if result['violations']:
            for i, v in enumerate(result['violations']):
                print(f"     {i+1}. {v.rule_id}: {v.message}")

        return True
    except Exception as e:
        print(f"   ERROR during validation: {e}")
        return False

def test_integration_registry():
    """Test integration registry."""
    print("\nTesting integration registry...")

    try:
        from validator.integrations.integration_registry import IntegrationRegistry
        registry = IntegrationRegistry()

        # Test validation through registry
        result = registry.validate_prompt('test prompt', {'file_type': 'python'})
        print(f"   Registry validation: {len(result['violations'])} violations")

        # Test integration loading
        integrations = registry.list_integrations()
        print(f"   Integrations loaded: {len(integrations)}")

        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def test_api_service():
    """Test API service."""
    print("\nTesting API service...")

    try:
        from validator.integrations.api_service import app
        print("   Flask app created successfully")

        # Check routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"   Routes configured: {len(routes)}")

        return True
    except Exception as e:
        print(f"   ERROR: {e}")
        return False

def main():
    """Run runtime tests."""
    print("=" * 50)
    print("RUNTIME ERROR DETECTION")
    print("=" * 50)

    tests = [
        test_validation_service,
        test_enhanced_cli,
        test_actual_validation,
        test_integration_registry,
        test_api_service
    ]

    passed = 0
    errors = []

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                errors.append(test.__name__)
        except Exception as e:
            errors.append(f"{test.__name__}: {e}")

    print("\n" + "=" * 50)
    print("RUNTIME TEST RESULTS")
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")

    if errors:
        print(f"\nERRORS FOUND ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nSUCCESS - No runtime errors detected!")

    return len(errors) == 0

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

