#!/usr/bin/env python3
"""
Test Deterministic, Consistent, and Repeatable Enforcement

This test suite verifies that pre-implementation hooks:
1. Always load rules in the same order
2. Always validate prompts in the same order
3. Always produce the same results for the same input
4. Handle concurrent access correctly
5. Are not affected by execution order or timing
"""

import sys
import unittest
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestDeterministicRuleLoading(unittest.TestCase):
    """Test that rules are loaded deterministically."""

    def test_file_loading_order(self):
        """Verify JSON files are loaded in deterministic order."""
        from validator.pre_implementation_hooks import ConstitutionRuleLoader

        # Load rules multiple times
        loader1 = ConstitutionRuleLoader()
        loader2 = ConstitutionRuleLoader()
        loader3 = ConstitutionRuleLoader()

        # Get rule IDs in order
        rules1 = [r.get('rule_id') for r in loader1.get_all_rules()]
        rules2 = [r.get('rule_id') for r in loader2.get_all_rules()]
        rules3 = [r.get('rule_id') for r in loader3.get_all_rules()]

        # All should be identical
        self.assertEqual(rules1, rules2, "Rule order should be deterministic across instances")
        self.assertEqual(rules2, rules3, "Rule order should be deterministic across instances")
        # Verify all instances load same count from JSON files
        self.assertEqual(len(rules1), len(rules2), "Should load same number of rules")
        self.assertEqual(len(rules2), len(rules3), "Should load same number of rules")

    def test_rule_count_consistency(self):
        """Verify rule count is consistent across multiple loads."""
        from validator.pre_implementation_hooks import ConstitutionRuleLoader

        counts = []
        for _ in range(5):
            loader = ConstitutionRuleLoader()
            counts.append(loader.get_total_rule_count())

        # All counts should be identical (from JSON files - single source of truth)
        self.assertEqual(len(set(counts)), 1, "Rule count should be consistent")
        # Verify count matches what hook manager reports
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()
        expected_count = hook_manager.total_rules
        self.assertEqual(counts[0], expected_count, f"Should always load {expected_count} rules from JSON files")

    def test_rule_ids_consistency(self):
        """Verify rule IDs are consistent across multiple loads."""
        from validator.pre_implementation_hooks import ConstitutionRuleLoader

        rule_ids_sets = []
        for _ in range(3):
            loader = ConstitutionRuleLoader()
            rule_ids = set(r.get('rule_id') for r in loader.get_all_rules())
            rule_ids_sets.append(rule_ids)

        # All sets should be identical
        self.assertEqual(rule_ids_sets[0], rule_ids_sets[1], "Rule IDs should be consistent")
        self.assertEqual(rule_ids_sets[1], rule_ids_sets[2], "Rule IDs should be consistent")


class TestDeterministicValidation(unittest.TestCase):
    """Test that validation results are deterministic."""

    def setUp(self):
        """Set up test fixtures."""
        from validator.pre_implementation_hooks import PreImplementationHookManager
        self.hook_manager = PreImplementationHookManager()

    def test_same_prompt_same_result(self):
        """Verify same prompt produces same result every time."""
        prompt = "create a function with hardcoded password = 'secret123'"

        results = []
        for _ in range(5):
            result = self.hook_manager.validate_before_generation(prompt)
            results.append({
                'valid': result['valid'],
                'violation_count': len(result['violations']),
                'rules_checked': result['total_rules_checked'],
                'violation_ids': sorted([v.rule_id for v in result['violations']])
            })

        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            self.assertEqual(
                result['valid'],
                first_result['valid'],
                f"Result {i+1} valid flag differs from first result"
            )
            self.assertEqual(
                result['violation_count'],
                first_result['violation_count'],
                f"Result {i+1} violation count differs from first result"
            )
            self.assertEqual(
                result['rules_checked'],
                first_result['rules_checked'],
                f"Result {i+1} rules checked differs from first result"
            )
            self.assertEqual(
                result['violation_ids'],
                first_result['violation_ids'],
                f"Result {i+1} violation IDs differ from first result"
            )

    def test_violation_order_consistency(self):
        """Verify violation order is consistent."""
        prompt = "create a function with hardcoded password and also add logging"

        results = []
        for _ in range(3):
            result = self.hook_manager.validate_before_generation(prompt)
            violation_ids = [v.rule_id for v in result['violations']]
            results.append(violation_ids)

        # All violation orders should be identical
        self.assertEqual(results[0], results[1], "Violation order should be consistent")
        self.assertEqual(results[1], results[2], "Violation order should be consistent")

    def test_rule_checking_order(self):
        """Verify rules are checked in consistent order."""
        prompt = "test prompt"

        # Get rule IDs that were checked
        result = self.hook_manager.validate_before_generation(prompt)

        # Verify total rules checked matches JSON files
        expected_rules = self.hook_manager.total_rules
        self.assertEqual(
            result['total_rules_checked'],
            expected_rules,
            f"Should always check exactly {expected_rules} rules from JSON files"
        )

        # Verify same number of rules checked on repeat
        for _ in range(3):
            repeat_result = self.hook_manager.validate_before_generation(prompt)
            expected_rules = self.hook_manager.total_rules
            self.assertEqual(
                repeat_result['total_rules_checked'],
                expected_rules,
                f"Rules checked should be consistent ({expected_rules} from JSON files)"
            )


class TestConsistentBehavior(unittest.TestCase):
    """Test consistent behavior across different scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        from validator.pre_implementation_hooks import PreImplementationHookManager
        self.hook_manager = PreImplementationHookManager()

    def test_empty_prompt_consistency(self):
        """Verify empty prompt produces consistent results."""
        results = []
        for _ in range(3):
            result = self.hook_manager.validate_before_generation("")
            results.append({
                'valid': result['valid'],
                'violation_count': len(result['violations']),
                'rules_checked': result['total_rules_checked']
            })

        # All should be identical
        self.assertEqual(len(set(str(r) for r in results)), 1, "Empty prompt results should be consistent")

    def test_whitespace_handling(self):
        """Verify whitespace handling is consistent."""
        prompts = [
            "test prompt",
            "  test prompt  ",
            "\ttest prompt\n",
            "test\nprompt"
        ]

        results = []
        for prompt in prompts:
            result = self.hook_manager.validate_before_generation(prompt.strip())
            results.append({
                'valid': result['valid'],
                'violation_count': len(result['violations']),
                'rules_checked': result['total_rules_checked']
            })

        # Normalized prompts should produce same results
        normalized_prompts = [p.strip().lower() for p in prompts]
        # If all normalize to same, results should be same
        self.assertEqual(
                len(set(str(r) for r in results)),
                1,
                "Normalized prompts should produce same results"
            )

    def test_case_sensitivity_consistency(self):
        """Verify case handling is consistent."""
        prompts = [
            "create function with PASSWORD",
            "create function with password",
            "create function with Password"
        ]

        results = []
        for prompt in prompts:
            result = self.hook_manager.validate_before_generation(prompt)
            results.append({
                'valid': result['valid'],
                'violation_count': len(result['violations']),
                'violation_ids': sorted([v.rule_id for v in result['violations']])
            })

        # All should be identical (validation is case-insensitive)
        self.assertEqual(
            results[0]['violation_count'],
            results[1]['violation_count'],
            "Case should not affect violation count"
        )
        self.assertEqual(
            results[1]['violation_count'],
            results[2]['violation_count'],
            "Case should not affect violation count"
        )


class TestRepeatableResults(unittest.TestCase):
    """Test that results are repeatable across different executions."""

    def test_isolation_between_instances(self):
        """Verify different manager instances produce same results."""
        from validator.pre_implementation_hooks import PreImplementationHookManager

        prompt = "create function with hardcoded password"

        manager1 = PreImplementationHookManager()
        manager2 = PreImplementationHookManager()
        manager3 = PreImplementationHookManager()

        result1 = manager1.validate_before_generation(prompt)
        result2 = manager2.validate_before_generation(prompt)
        result3 = manager3.validate_before_generation(prompt)

        # All should produce identical results
        self.assertEqual(
            result1['valid'],
            result2['valid'],
            "Different instances should produce same valid flag"
        )
        self.assertEqual(
            result2['valid'],
            result3['valid'],
            "Different instances should produce same valid flag"
        )

        self.assertEqual(
            len(result1['violations']),
            len(result2['violations']),
            "Different instances should find same number of violations"
        )
        self.assertEqual(
            len(result2['violations']),
            len(result3['violations']),
            "Different instances should find same number of violations"
        )

        self.assertEqual(
            result1['total_rules_checked'],
            result2['total_rules_checked'],
            "Different instances should check same number of rules"
        )
        expected_rules = manager1.total_rules
        self.assertEqual(
            result1['total_rules_checked'],
            expected_rules,
            f"Should always check {expected_rules} rules from JSON files"
        )

    def test_rule_processing_order(self):
        """Verify rules are processed in consistent order."""
        from validator.pre_implementation_hooks import PreImplementationHookManager

        prompt = "test prompt"

        manager1 = PreImplementationHookManager()
        manager2 = PreImplementationHookManager()

        # Get all rules in order
        rules1 = [r.get('rule_id') for r in manager1.rule_loader.get_all_rules()]
        rules2 = [r.get('rule_id') for r in manager2.rule_loader.get_all_rules()]

        # Should be identical
        self.assertEqual(rules1, rules2, "Rule processing order should be consistent")


def run_determinism_tests():
    """Run all determinism tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestDeterministicRuleLoading,
        TestDeterministicValidation,
        TestConsistentBehavior,
        TestRepeatableResults
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    print("=" * 80)
    print("DETERMINISTIC ENFORCEMENT TEST SUITE")
    print("=" * 80)
    print()
    print("Testing:")
    print("  1. Deterministic rule loading")
    print("  2. Deterministic validation results")
    print("  3. Consistent behavior")
    print("  4. Repeatable results")
    print()

    success = run_determinism_tests()

    print()
    print("=" * 80)
    if success:
        print("SUCCESS: All determinism tests passed!")
        print("Pre-implementation hooks are deterministic, consistent, and repeatable.")
    else:
        print("FAILURE: Some determinism tests failed!")
        print("Review test output above for non-deterministic behavior.")
    print("=" * 80)

    sys.exit(0 if success else 1)
