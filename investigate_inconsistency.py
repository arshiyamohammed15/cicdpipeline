#!/usr/bin/env python3
"""
Investigate Validation Inconsistency
"""

import sys
sys.path.insert(0, 'D:/Projects/ZeroUI2.0')

def investigate_validation():
    """Investigate why validation results are inconsistent."""
    print("Investigating validation inconsistency...")

    from validator.pre_implementation_hooks import PreImplementationHookManager

    test_prompts = [
        'create function with hardcoded password',
        'create function with hardcoded api key',
        'create function without error handling',
        'create function with hardcoded password and api key',
        'create function with hardcoded password'
    ]

    print('Detailed violation analysis:')
    for i, prompt in enumerate(test_prompts, 1):
        result = PreImplementationHookManager().validate_before_generation(prompt, 'python', 'general')
        violations = result['violations']
        print(f'\nTest {i}: {prompt}')
        print(f'  Valid: {result["valid"]}')
        print(f'  Total violations: {len(violations)}')
        print(f'  Rules checked: {result["total_rules_checked"]}')
        for j, violation in enumerate(violations):
            print(f'    {j+1}. {violation.rule_id}: {violation.message}')

def check_rule_coverage():
    """Check if all rule categories are being validated consistently."""
    print("\nChecking rule category coverage...")

    from validator.pre_implementation_hooks import PreImplementationHookManager

    # Test each category specifically
    category_tests = {
        'basic_work': 'do exactly what is asked',
        'security_privacy': 'protect people privacy',
        'logging': 'keep good logs',
        'error_handling': 'handle errors gracefully',
        'typescript': 'use proper types',
        'storage_governance': 'manage storage properly'
    }

    for category, prompt in category_tests.items():
        result = PreImplementationHookManager().validate_before_generation(prompt, 'python', category)
        violations = len(result['violations'])
        print(f'  {category}: {violations} violations')

def check_validation_logic():
    """Check if the validation logic itself is consistent."""
    print("\nChecking validation logic consistency...")

    from validator.pre_implementation_hooks import PreImplementationHookManager

    # Same prompt validated multiple times
    prompt = 'create function with hardcoded password and api key'

    results = []
    for i in range(5):
        result = PreImplementationHookManager().validate_before_generation(prompt, 'python', 'security')
        results.append({
            'valid': result['valid'],
            'violations': len(result['violations']),
            'rules_checked': result['total_rules_checked']
        })

    # Check if results are identical
    first = results[0]
    consistent = all(
        r['valid'] == first['valid'] and
        r['violations'] == first['violations'] and
        r['rules_checked'] == first['rules_checked']
        for r in results
    )

    print(f'  Same prompt validated 5 times: {consistent}')
    for i, result in enumerate(results):
        print(f'    Run {i+1}: {result["violations"]} violations, valid: {result["valid"]}')

def main():
    """Run investigation."""
    print("=" * 50)
    print("VALIDATION INCONSISTENCY INVESTIGATION")
    print("=" * 50)

    investigate_validation()
    check_rule_coverage()
    check_validation_logic()

    print("\nInvestigation complete!")

if __name__ == '__main__':
    main()
