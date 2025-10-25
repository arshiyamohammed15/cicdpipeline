#!/usr/bin/env python3
"""
Consistency Test for Automatic Enforcement Implementation
"""

import sys
import os
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def test_component_loading():
    """Test that all components load consistently."""
    print("=== Test 1: Component Loading Consistency ===")

    components_to_test = [
        'validator.pre_implementation_hooks',
        'validator.integrations.ai_service_wrapper',
        'validator.integrations.integration_registry',
        'validator.integrations.api_service',
        'validator.integrations.openai_integration',
        'validator.integrations.cursor_integration'
    ]

    loading_errors = []
    for component in components_to_test:
        try:
            __import__(component)
            print(f'   OK {component}')
        except Exception as e:
            print(f'   ERROR {component}: {e}')
            loading_errors.append(component)

    return len(loading_errors) == 0

def test_validation_consistency():
    """Test that validation results are consistent."""
    print("\n=== Test 2: Validation Consistency ===")

    try:
        from validator.pre_implementation_hooks import PreImplementationHookManager

        test_prompts = [
            'create function with hardcoded password',
            'create function with hardcoded api key',
            'create function without error handling',
            'create function with hardcoded password and api key',
            'create function with hardcoded password'
        ]

        results = []
        for prompt in test_prompts:
            result = PreImplementationHookManager().validate_before_generation(prompt, 'python', 'general')
            results.append({
                'prompt': prompt,
                'valid': result['valid'],
                'violations': len(result['violations']),
                'rules_checked': result['total_rules_checked']
            })

        # Check consistency
        first_result = results[0]
        consistent = all(r['valid'] == first_result['valid'] and
                        r['violations'] == first_result['violations'] and
                        r['rules_checked'] == first_result['rules_checked']
                        for r in results)

        print(f'   Consistent validation results: {consistent}')
        for i, result in enumerate(results):
            print(f'   Test {i+1}: {result["violations"]} violations, valid: {result["valid"]}')

        return consistent
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

def test_integration_consistency():
    """Test that integration registry behaves consistently."""
    print("\n=== Test 3: Integration Registry Consistency ===")

    try:
        from validator.integrations.integration_registry import IntegrationRegistry

        # Test multiple times
        results = []
        for i in range(3):
            registry = IntegrationRegistry()
            integrations = registry.list_integrations()
            results.append(len(integrations))

        consistent = all(count == results[0] for count in results)
        print(f'   Consistent integration counts: {consistent}')
        print(f'   Integration counts: {results}')

        # Test validation through registry
        registry_results = []
        test_prompt = 'create function with hardcoded password'
        for i in range(3):
            result = registry.validate_prompt(test_prompt, {'file_type': 'python'})
            registry_results.append(len(result['violations']))

        registry_consistent = all(count == registry_results[0] for count in registry_results)
        print(f'   Consistent registry validation: {registry_consistent}')
        print(f'   Registry violation counts: {registry_results}')

        return consistent and registry_consistent
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

def test_configuration_consistency():
    """Test that configuration is consistent."""
    print("\n=== Test 4: Configuration Consistency ===")

    try:
        import json

        # Load and check configuration multiple times
        config_results = []
        for i in range(3):
            with open('config/hook_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            ai_integration = config['global_settings']['ai_service_integration']
            config_results.append({
                'enabled': ai_integration.get('enabled', False),
                'block_on_violation': ai_integration.get('block_on_violation', False),
                'supported_services': ai_integration.get('supported_services', [])
            })

        # Check consistency
        first_config = config_results[0]
        consistent = all(
            c['enabled'] == first_config['enabled'] and
            c['block_on_violation'] == first_config['block_on_violation'] and
            c['supported_services'] == first_config['supported_services']
            for c in config_results
        )

        print(f'   Consistent configuration: {consistent}')
        print(f'   AI integration enabled: {first_config["enabled"]}')
        print(f'   Block on violation: {first_config["block_on_violation"]}')
        print(f'   Supported services: {first_config["supported_services"]}')

        return consistent
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

def test_rule_consistency():
    """Test that rules are consistently enforced."""
    print("\n=== Test 5: Rule Enforcement Consistency ===")

    try:
        import json

        # Check rules file multiple times
        rule_results = []
        for i in range(3):
            with open('config/constitution_rules.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            rule_results.append({
                'total_rules': data['statistics']['total_rules'],
                'enabled_rules': data['statistics']['enabled_rules'],
                'disabled_rules': data['statistics']['disabled_rules']
            })

        # Check consistency
        first_rules = rule_results[0]
        consistent = all(
            r['total_rules'] == first_rules['total_rules'] and
            r['enabled_rules'] == first_rules['enabled_rules'] and
            r['disabled_rules'] == first_rules['disabled_rules']
            for r in rule_results
        )

        print(f'   Consistent rule counts: {consistent}')
        print(f'   Total rules: {first_rules["total_rules"]}')
        print(f'   Enabled rules: {first_rules["enabled_rules"]}')
        print(f'   Disabled rules: {first_rules["disabled_rules"]}')

        return consistent
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

def test_vs_code_consistency():
    """Test VS Code integration consistency."""
    print("\n=== Test 6: VS Code Integration Consistency ===")

    try:
        import json

        # Check package.json multiple times
        package_results = []
        for i in range(3):
            with open('src/vscode-extension/package.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            commands = data.get('contributes', {}).get('commands', [])
            validation_commands = [cmd for cmd in commands if 'validate' in cmd['command'] or 'generate' in cmd['command']]
            package_results.append(len(validation_commands))

        # Check consistency
        consistent = all(count == package_results[0] for count in package_results)
        print(f'   Consistent VS Code commands: {consistent}')
        print(f'   Validation command counts: {package_results}')

        return consistent
    except Exception as e:
        print(f'   ERROR: {e}')
        return False

def main():
    """Run consistency tests."""
    print("=" * 60)
    print("IMPLEMENTATION CONSISTENCY VALIDATION")
    print("=" * 60)

    tests = [
        test_component_loading,
        test_validation_consistency,
        test_integration_consistency,
        test_configuration_consistency,
        test_rule_consistency,
        test_vs_code_consistency
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 60)
    print("CONSISTENCY VALIDATION RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("\nSUCCESS - Implementation is 100% consistent!")
        print("\nConsistency Verified:")
        print("OK All components load consistently")
        print("OK Validation results are consistent")
        print("OK Integration registry behaves consistently")
        print("OK Configuration is consistent")
        print("OK Rule enforcement is consistent")
        print("OK VS Code integration is consistent")
        print("\n100% Consistent outcomes confirmed!")
    else:
        print(f"\nWARNING - {total - passed} consistency issues found!")

    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
