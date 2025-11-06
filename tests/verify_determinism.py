#!/usr/bin/env python3
"""
Quick Verification: Deterministic Enforcement

Verifies that pre-implementation hooks produce deterministic, consistent,
and repeatable results.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_deterministic_loading():
    """Test that rules load in deterministic order."""
    print("1. Testing deterministic rule loading...")
    
    from validator.pre_implementation_hooks import ConstitutionRuleLoader
    
    loaders = []
    for _ in range(3):
        loader = ConstitutionRuleLoader()
        loaders.append(loader)
    
    # Get rule IDs from each loader
    rule_id_lists = []
    for loader in loaders:
        rule_ids = [r.get('rule_id') for r in loader.get_all_rules()]
        rule_id_lists.append(rule_ids)
    
    # All should be identical
    if rule_id_lists[0] == rule_id_lists[1] == rule_id_lists[2]:
        print("   [OK] Rule loading order is deterministic")
        return True
    else:
        print("   [FAIL] Rule loading order is not deterministic")
        return False


def test_deterministic_validation():
    """Test that validation produces same results."""
    print("\n2. Testing deterministic validation...")
    
    from validator.pre_implementation_hooks import PreImplementationHookManager
    
    manager = PreImplementationHookManager()
    prompt = "create a function with hardcoded password = 'secret123'"
    
    results = []
    for _ in range(5):
        result = manager.validate_before_generation(prompt)
        results.append({
            'valid': result['valid'],
            'violation_count': len(result['violations']),
            'rules_checked': result['total_rules_checked'],
            'violation_ids': tuple(sorted([v.rule_id for v in result['violations']]))
        })
    
    # All should be identical
    first_result = results[0]
    all_same = all(r == first_result for r in results[1:])
    
    if all_same:
        print(f"   [OK] Validation produces same results (5 runs)")
        print(f"   [OK] Valid: {first_result['valid']}")
        print(f"   [OK] Violations: {first_result['violation_count']}")
        print(f"   [OK] Rules checked: {first_result['rules_checked']}")
        return True
    else:
        print("   [FAIL] Validation results differ between runs")
        return False


def test_instance_isolation():
    """Test that different instances produce same results."""
    print("\n3. Testing instance isolation...")
    
    from validator.pre_implementation_hooks import PreImplementationHookManager
    
    prompt = "create a function with hardcoded password"
    
    managers = [PreImplementationHookManager() for _ in range(3)]
    results = []
    
    for manager in managers:
        result = manager.validate_before_generation(prompt)
        results.append({
            'valid': result['valid'],
            'violation_count': len(result['violations']),
            'rules_checked': result['total_rules_checked'],
            'violation_ids': tuple(sorted([v.rule_id for v in result['violations']]))
        })
    
    # All should be identical
    first_result = results[0]
    all_same = all(r == first_result for r in results[1:])
    
    if all_same:
        print("   [OK] Different instances produce same results")
        return True
    else:
        print("   [FAIL] Different instances produce different results")
        return False


def test_violation_order():
    """Test that violation order is deterministic."""
    print("\n4. Testing violation order consistency...")
    
    from validator.pre_implementation_hooks import PreImplementationHookManager
    
    manager = PreImplementationHookManager()
    prompt = "create a function with hardcoded password and also add logging"
    
    violation_id_lists = []
    for _ in range(3):
        result = manager.validate_before_generation(prompt)
        violation_ids = [v.rule_id for v in result['violations']]
        violation_id_lists.append(violation_ids)
    
    # All should be identical (sorted)
    if violation_id_lists[0] == violation_id_lists[1] == violation_id_lists[2]:
        print("   [OK] Violation order is deterministic")
        return True
    else:
        print("   [FAIL] Violation order is not deterministic")
        return False


def test_rule_count_consistency():
    """Test that rule count is always 424."""
    print("\n5. Testing rule count consistency...")
    
    from validator.pre_implementation_hooks import PreImplementationHookManager
    
    manager = PreImplementationHookManager()
    expected_count = manager.total_rules
    
    counts = []
    for _ in range(10):
        result = manager.validate_before_generation("test prompt")
        counts.append(result['total_rules_checked'])
    
    # All counts should be identical and match JSON files
    if len(set(counts)) == 1 and counts[0] == expected_count:
        print(f"   [OK] Rule count is always {expected_count} (from JSON files)")
        return True
    else:
        print(f"   [FAIL] Rule count varies: {set(counts)}, expected {expected_count}")
        return False


def main():
    """Run all determinism verification checks."""
    print("=" * 80)
    print("DETERMINISTIC ENFORCEMENT VERIFICATION")
    print("=" * 80)
    print()
    
    checks = [
        test_deterministic_loading,
        test_deterministic_validation,
        test_instance_isolation,
        test_violation_order,
        test_rule_count_consistency
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
        print("\n[SUCCESS] All determinism checks passed!")
        print("  Pre-implementation hooks are deterministic, consistent, and repeatable.")
        print()
        print("Guarantees:")
        print("  - Rules load in deterministic order")
        print("  - Same prompt produces same result")
        print("  - Different instances produce same results")
        print("  - Violation order is deterministic")
        print("  - Rule count is consistent (from JSON files)")
        return True
    else:
        print(f"\n[FAILURE] {total - passed} checks failed!")
        print("  Review the output above to identify non-deterministic behavior.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

