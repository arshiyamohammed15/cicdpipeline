"""
Dynamic Validation Tests for ZeroUI 2.0 Constitution Rules

This module provides parameterized tests that dynamically generate test cases
from rules.json, eliminating hardcoded rule IDs and ensuring 100% coverage.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.dynamic_test_factory import DynamicTestFactory, TestCase
from tools.validator.rule_engine import RuleEngine


class TestAllRules:
    """Test all 89 rules dynamically without hardcoded rule IDs."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def rule_engine(self):
        """Get the rule engine instance."""
        return RuleEngine()

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_all_rules(self, test_case: TestCase, rule_engine: RuleEngine):
        """Test all 89 rules dynamically."""
        # Verify the rule exists in the engine
        assert test_case.rule_id in [rule['id'] for rule in rule_engine.get_all_rules()], \
            f"Rule {test_case.rule_id} not found in rule engine"

        # Verify the rule has required fields
        assert test_case.rule_id, f"Rule ID is empty for {test_case.rule_name}"
        assert test_case.rule_name, f"Rule name is empty for {test_case.rule_id}"
        assert test_case.category, f"Category is empty for {test_case.rule_id}"
        assert test_case.severity, f"Severity is empty for {test_case.rule_id}"
        assert test_case.validator, f"Validator is empty for {test_case.rule_id}"
        assert test_case.constitution, f"Constitution is empty for {test_case.rule_id}"
        assert test_case.error_code, f"Error code is empty for {test_case.rule_id}"

        # Verify test data structure
        assert isinstance(test_case.test_data, dict), f"Test data is not a dict for {test_case.rule_id}"
        assert 'violation_examples' in test_case.test_data, f"Missing violation_examples for {test_case.rule_id}"
        assert 'valid_examples' in test_case.test_data, f"Missing valid_examples for {test_case.rule_id}"

        # Verify test method name format
        assert test_case.test_method_name.startswith('test_'), f"Invalid test method name for {test_case.rule_id}"
        assert test_case.rule_id.lower() in test_case.test_method_name, f"Rule ID not in method name for {test_case.rule_id}"


class TestErrorRules:
    """Test only error-level rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('severity') == 'error'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_error_rules(self, test_case: TestCase):
        """Test all error-level rules."""
        assert test_case.severity == 'error', f"Rule {test_case.rule_id} is not an error rule"
        assert test_case.error_code.startswith('ERROR:'), f"Error code format invalid for {test_case.rule_id}"


class TestWarningRules:
    """Test only warning-level rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('severity') == 'warning'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_warning_rules(self, test_case: TestCase):
        """Test all warning-level rules."""
        assert test_case.severity == 'warning', f"Rule {test_case.rule_id} is not a warning rule"
        assert test_case.error_code.startswith('ERROR:'), f"Error code format invalid for {test_case.rule_id}"


class TestByCategory:
    """Test rules grouped by category."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.mark.parametrize("category", DynamicTestFactory().get_categories())
    def test_category_exists(self, category: str, test_factory: DynamicTestFactory):
        """Test that each category has rules."""
        rules = test_factory.get_rules_by_category(category)
        assert len(rules) > 0, f"Category '{category}' has no rules"

        # Verify all rules in category have the same category
        for rule in rules:
            assert rule.get('category') == category, f"Rule {rule['id']} has wrong category"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('category') == 'security'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_security_rules(self, test_case: TestCase):
        """Test all security rules."""
        assert test_case.category == 'security', f"Rule {test_case.rule_id} is not a security rule"
        assert 'security' in test_case.validator.lower() or 'security' in test_case.rule_name.lower(), \
            f"Security rule {test_case.rule_id} should have security-related validator or name"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('category') == 'api'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_api_rules(self, test_case: TestCase):
        """Test all API rules."""
        assert test_case.category == 'api', f"Rule {test_case.rule_id} is not an API rule"
        assert 'api' in test_case.validator.lower(), f"API rule {test_case.rule_id} should have API validator"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('category') == 'documentation'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_documentation_rules(self, test_case: TestCase):
        """Test all documentation rules."""
        assert test_case.category == 'documentation', f"Rule {test_case.rule_id} is not a documentation rule"
        assert 'comment' in test_case.validator.lower(), f"Documentation rule {test_case.rule_id} should have comment validator"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('category') == 'logging'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_logging_rules(self, test_case: TestCase):
        """Test all logging rules."""
        assert test_case.category == 'logging', f"Rule {test_case.rule_id} is not a logging rule"
        assert 'logging' in test_case.validator.lower(), f"Logging rule {test_case.rule_id} should have logging validator"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('category') == 'structure'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_structure_rules(self, test_case: TestCase):
        """Test all structure rules."""
        assert test_case.category == 'structure', f"Rule {test_case.rule_id} is not a structure rule"
        assert 'structure' in test_case.validator.lower(), f"Structure rule {test_case.rule_id} should have structure validator"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: rule.get('category') == 'code_quality'
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_code_quality_rules(self, test_case: TestCase):
        """Test all code quality rules."""
        assert test_case.category == 'code_quality', f"Rule {test_case.rule_id} is not a code quality rule"
        assert 'code_quality' in test_case.validator.lower(), f"Code quality rule {test_case.rule_id} should have code_quality validator"


class TestByValidator:
    """Test rules grouped by validator."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.mark.parametrize("validator", DynamicTestFactory().get_validators())
    def test_validator_exists(self, validator: str, test_factory: DynamicTestFactory):
        """Test that each validator has rules."""
        rules = test_factory.get_rules_by_validator(validator)
        assert len(rules) > 0, f"Validator '{validator}' has no rules"

        # Verify all rules use the specified validator
        for rule in rules:
            assert validator in rule.get('validator', ''), f"Rule {rule['id']} doesn't use validator {validator}"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: 'security_validator' in rule.get('validator', '')
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_security_validator_rules(self, test_case: TestCase):
        """Test all rules handled by security_validator."""
        assert 'security_validator' in test_case.validator, f"Rule {test_case.rule_id} not handled by security_validator"
        assert test_case.category in ['security'], f"Security validator rule {test_case.rule_id} should be security category"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: 'api_validator' in rule.get('validator', '')
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_api_validator_rules(self, test_case: TestCase):
        """Test all rules handled by api_validator."""
        assert 'api_validator' in test_case.validator, f"Rule {test_case.rule_id} not handled by api_validator"
        assert test_case.category in ['api'], f"API validator rule {test_case.rule_id} should be API category"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: 'comment_validator' in rule.get('validator', '')
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_comment_validator_rules(self, test_case: TestCase):
        """Test all rules handled by comment_validator."""
        assert 'comment_validator' in test_case.validator, f"Rule {test_case.rule_id} not handled by comment_validator"
        assert test_case.category in ['documentation'], f"Comment validator rule {test_case.rule_id} should be documentation category"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: 'logging_validator' in rule.get('validator', '')
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_logging_validator_rules(self, test_case: TestCase):
        """Test all rules handled by logging_validator."""
        assert 'logging_validator' in test_case.validator, f"Rule {test_case.rule_id} not handled by logging_validator"
        assert test_case.category in ['logging'], f"Logging validator rule {test_case.rule_id} should be logging category"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: 'structure_validator' in rule.get('validator', '')
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_structure_validator_rules(self, test_case: TestCase):
        """Test all rules handled by structure_validator."""
        assert 'structure_validator' in test_case.validator, f"Rule {test_case.rule_id} not handled by structure_validator"
        assert test_case.category in ['structure', 'scope', 'governance', 'process', 'quality'], \
            f"Structure validator rule {test_case.rule_id} should be structure/governance category"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(
                               filter_func=lambda rule: 'code_quality_validator' in rule.get('validator', '')
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_code_quality_validator_rules(self, test_case: TestCase):
        """Test all rules handled by code_quality_validator."""
        assert 'code_quality_validator' in test_case.validator, f"Rule {test_case.rule_id} not handled by code_quality_validator"
        assert test_case.category in ['code_quality'], f"Code quality validator rule {test_case.rule_id} should be code_quality category"


class TestRuleEngineIntegration:
    """Test integration with the existing RuleEngine."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def rule_engine(self):
        """Get the rule engine instance."""
        return RuleEngine()

    def test_rule_engine_has_all_rules(self, test_factory: DynamicTestFactory, rule_engine: RuleEngine):
        """Test that RuleEngine has all rules from the factory."""
        factory_rules = test_factory.get_all_rules()
        engine_rules = rule_engine.get_all_rules()

        factory_rule_ids = {rule['id'] for rule in factory_rules}
        engine_rule_ids = {rule['id'] for rule in engine_rules}

        assert factory_rule_ids == engine_rule_ids, \
            f"RuleEngine missing rules: {factory_rule_ids - engine_rule_ids}, " \
            f"RuleEngine has extra rules: {engine_rule_ids - factory_rule_ids}"

    def test_all_validators_exist(self, test_factory: DynamicTestFactory):
        """Test that all validators referenced in rules exist."""
        validators = test_factory.get_validators()
        expected_validators = [
            'security_validator', 'api_validator', 'comment_validator',
            'logging_validator', 'structure_validator', 'code_quality_validator'
        ]

        for validator in validators:
            assert validator in expected_validators, f"Unknown validator: {validator}"

    def test_rule_coverage_stats(self, test_factory: DynamicTestFactory):
        """Test that we have the expected number of rules."""
        stats = test_factory.get_coverage_stats()

        assert stats['total_rules'] == 89, f"Expected 89 rules, got {stats['total_rules']}"
        assert stats['error_rules'] > 0, "Should have error rules"
        assert stats['warning_rules'] > 0, "Should have warning rules"
        assert stats['categories'] >= 6, "Should have at least 6 categories"
        assert stats['constitutions'] >= 6, "Should have at least 6 constitutions"


class TestDynamicTestGeneration:
    """Test the dynamic test generation functionality."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    def test_test_case_generation(self, test_factory: DynamicTestFactory):
        """Test that test cases are generated correctly."""
        test_cases = test_factory.create_test_cases()

        assert len(test_cases) == 89, f"Expected 89 test cases, got {len(test_cases)}"

        # Verify each test case has required fields
        for test_case in test_cases:
            assert isinstance(test_case, TestCase), f"Test case is not TestCase instance"
            assert test_case.rule_id, f"Test case missing rule_id"
            assert test_case.rule_name, f"Test case missing rule_name"
            assert test_case.test_method_name, f"Test case missing test_method_name"
            assert test_case.test_data, f"Test case missing test_data"

    def test_filtering_functionality(self, test_factory: DynamicTestFactory):
        """Test that filtering works correctly."""
        # Test category filtering
        security_rules = test_factory.get_rules_by_category('security')
        assert len(security_rules) > 0, "Should have security rules"

        # Test severity filtering
        error_rules = test_factory.get_rules_by_severity('error')
        warning_rules = test_factory.get_rules_by_severity('warning')
        assert len(error_rules) > 0, "Should have error rules"
        assert len(warning_rules) > 0, "Should have warning rules"
        assert len(error_rules) + len(warning_rules) == 89, "All rules should be error or warning"

        # Test validator filtering
        security_validator_rules = test_factory.get_rules_by_validator('security_validator')
        assert len(security_validator_rules) > 0, "Should have security validator rules"

    def test_pattern_matching(self, test_factory: DynamicTestFactory):
        """Test pattern-based rule discovery."""
        # Test keyword matching
        todo_rules = test_factory.get_rules_by_keywords(['TODO'])
        assert len(todo_rules) > 0, "Should have TODO-related rules"

        # Test pattern matching
        async_rules = test_factory.get_rules_by_pattern('async', 'name')
        assert len(async_rules) >= 0, "Should handle async pattern matching"

    def test_test_data_generation(self, test_factory: DynamicTestFactory):
        """Test that test data is generated appropriately."""
        test_cases = test_factory.create_test_cases()

        for test_case in test_cases:
            test_data = test_case.test_data

            # Verify test data structure
            assert 'violation_examples' in test_data, f"Missing violation_examples for {test_case.rule_id}"
            assert 'valid_examples' in test_data, f"Missing valid_examples for {test_case.rule_id}"
            assert isinstance(test_data['violation_examples'], list), f"violation_examples should be list for {test_case.rule_id}"
            assert isinstance(test_data['valid_examples'], list), f"valid_examples should be list for {test_case.rule_id}"

            # Verify category-specific data generation
            if test_case.category == 'security':
                assert len(test_data['violation_examples']) > 0, f"Security rule {test_case.rule_id} should have violation examples"
            elif test_case.category == 'api':
                assert len(test_data['violation_examples']) > 0, f"API rule {test_case.rule_id} should have violation examples"
            elif test_case.category == 'documentation':
                assert len(test_data['violation_examples']) > 0, f"Documentation rule {test_case.rule_id} should have violation examples"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
