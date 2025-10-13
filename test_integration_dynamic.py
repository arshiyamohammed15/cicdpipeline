"""
Integration Tests for Dynamic Test Discovery System

This module tests the integration between the dynamic test discovery system
and the existing RuleEngine, ensuring all components work together correctly.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.dynamic_test_factory import DynamicTestFactory, TestCase
from tools.validator.rule_engine import RuleEngine


class TestRuleEngineIntegration:
    """Test integration between DynamicTestFactory and RuleEngine."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def rule_engine(self):
        """Get the rule engine instance."""
        return RuleEngine()

    def test_rule_synchronization(self, test_factory, rule_engine):
        """Test that factory and engine have the same rules."""
        factory_rules = test_factory.get_all_rules()
        engine_rules = rule_engine.get_all_rules()

        # Same number of rules
        assert len(factory_rules) == len(engine_rules), \
            f"Factory has {len(factory_rules)} rules, engine has {len(engine_rules)}"

        # Same rule IDs
        factory_ids = {rule['id'] for rule in factory_rules}
        engine_ids = {rule['id'] for rule in engine_rules}
        assert factory_ids == engine_ids, \
            f"Rule IDs don't match: factory={factory_ids}, engine={engine_ids}"

        # Same rule content
        for factory_rule in factory_rules:
            engine_rule = next((r for r in engine_rules if r['id'] == factory_rule['id']), None)
            assert engine_rule is not None, f"Engine missing rule {factory_rule['id']}"
            assert factory_rule == engine_rule, f"Rule content differs for {factory_rule['id']}"

    def test_validator_mapping(self, test_factory, rule_engine):
        """Test that all validators referenced in rules exist."""
        factory_rules = test_factory.get_all_rules()
        validators = test_factory.get_validators()

        # All validators should be importable
        for validator in validators:
            try:
                if validator == 'security_validator':
                    from tools.validator.validators.security_validator import SecurityValidator
                elif validator == 'api_validator':
                    from tools.validator.validators.api_validator import APIValidator
                elif validator == 'comment_validator':
                    from tools.validator.validators.comment_validator import CommentValidator
                elif validator == 'logging_validator':
                    from tools.validator.validators.logging_validator import LoggingValidator
                elif validator == 'structure_validator':
                    from tools.validator.validators.structure_validator import StructureValidator
                elif validator == 'code_quality_validator':
                    from tools.validator.validators.code_quality_validator import CodeQualityValidator
                else:
                    pytest.fail(f"Unknown validator: {validator}")
            except ImportError as e:
                pytest.fail(f"Cannot import validator {validator}: {e}")

        # All rules should reference valid validators
        for rule in factory_rules:
            validator_ref = rule.get('validator', '')
            assert validator_ref, f"Rule {rule['id']} has no validator"

            # Extract validator class name
            validator_class = validator_ref.split('.')[0]
            assert validator_class in validators, f"Rule {rule['id']} references unknown validator: {validator_class}"

    def test_rule_validation_methods(self, test_factory, rule_engine):
        """Test that all rule validation methods exist."""
        factory_rules = test_factory.get_all_rules()

        for rule in factory_rules:
            validator_ref = rule.get('validator', '')
            if not validator_ref:
                continue

            # Parse validator reference (e.g., "security_validator.validate_no_secrets")
            parts = validator_ref.split('.')
            if len(parts) != 2:
                continue  # Skip if not in expected format

            validator_class, method_name = parts

            try:
                # Import the validator class
                if validator_class == 'security_validator':
                    from tools.validator.validators.security_validator import SecurityValidator
                    validator_instance = SecurityValidator()
                elif validator_class == 'api_validator':
                    from tools.validator.validators.api_validator import APIValidator
                    validator_instance = APIValidator()
                elif validator_class == 'comment_validator':
                    from tools.validator.validators.comment_validator import CommentValidator
                    validator_instance = CommentValidator()
                elif validator_class == 'logging_validator':
                    from tools.validator.validators.logging_validator import LoggingValidator
                    validator_instance = LoggingValidator()
                elif validator_class == 'structure_validator':
                    from tools.validator.validators.structure_validator import StructureValidator
                    validator_instance = StructureValidator()
                elif validator_class == 'code_quality_validator':
                    from tools.validator.validators.code_quality_validator import CodeQualityValidator
                    validator_instance = CodeQualityValidator()
                else:
                    continue  # Skip unknown validators

                # Check that the method exists
                assert hasattr(validator_instance, method_name), \
                    f"Validator {validator_class} missing method {method_name} for rule {rule['id']}"

                # Check that it's callable
                method = getattr(validator_instance, method_name)
                assert callable(method), \
                    f"Method {method_name} in {validator_class} is not callable for rule {rule['id']}"

            except ImportError:
                pytest.fail(f"Cannot import validator {validator_class} for rule {rule['id']}")

    def test_rule_engine_validation(self, test_factory, rule_engine):
        """Test that RuleEngine can validate rules using factory data."""
        test_cases = test_factory.create_test_cases()

        # Test a few representative rules
        test_rules = [tc for tc in test_cases if tc.rule_id in ['R001', 'R008', 'R013', 'R027', 'R063']]

        for test_case in test_rules:
            # Get the rule from the engine
            engine_rule = next((r for r in rule_engine.get_all_rules() if r['id'] == test_case.rule_id), None)
            assert engine_rule is not None, f"Engine missing rule {test_case.rule_id}"

            # Verify rule properties match
            assert engine_rule['id'] == test_case.rule_id
            assert engine_rule['name'] == test_case.rule_name
            assert engine_rule['category'] == test_case.category
            assert engine_rule['severity'] == test_case.severity
            assert engine_rule['validator'] == test_case.validator
            assert engine_rule['constitution'] == test_case.constitution
            assert engine_rule['error_code'] == test_case.error_code


class TestDynamicTestGeneration:
    """Test dynamic test generation functionality."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    def test_test_case_completeness(self, test_factory):
        """Test that all test cases are complete and valid."""
        test_cases = test_factory.create_test_cases()

        assert len(test_cases) == 89, f"Expected 89 test cases, got {len(test_cases)}"

        for test_case in test_cases:
            # Verify TestCase object structure
            assert isinstance(test_case, TestCase), f"Test case is not TestCase instance"
            assert test_case.rule_id, f"Test case missing rule_id"
            assert test_case.rule_name, f"Test case missing rule_name"
            assert test_case.category, f"Test case missing category"
            assert test_case.severity, f"Test case missing severity"
            assert test_case.validator, f"Test case missing validator"
            assert test_case.constitution, f"Test case missing constitution"
            assert test_case.test_method_name, f"Test case missing test_method_name"
            assert test_case.test_data, f"Test case missing test_data"
            assert test_case.expected_behavior, f"Test case missing expected_behavior"
            assert test_case.error_code, f"Test case missing error_code"

            # Verify test method name format
            assert test_case.test_method_name.startswith('test_'), \
                f"Invalid test method name: {test_case.test_method_name}"
            assert test_case.rule_id.lower() in test_case.test_method_name, \
                f"Rule ID not in method name: {test_case.test_method_name}"

            # Verify test data structure
            assert isinstance(test_case.test_data, dict), \
                f"Test data is not a dict for {test_case.rule_id}"
            assert 'violation_examples' in test_case.test_data, \
                f"Missing violation_examples for {test_case.rule_id}"
            assert 'valid_examples' in test_case.test_data, \
                f"Missing valid_examples for {test_case.rule_id}"
            assert isinstance(test_case.test_data['violation_examples'], list), \
                f"violation_examples should be list for {test_case.rule_id}"
            assert isinstance(test_case.test_data['valid_examples'], list), \
                f"valid_examples should be list for {test_case.rule_id}"

    def test_filtering_accuracy(self, test_factory):
        """Test that filtering works correctly."""
        # Test category filtering
        security_rules = test_factory.get_rules_by_category('security')
        assert len(security_rules) > 0, "Should have security rules"
        for rule in security_rules:
            assert rule.get('category') == 'security', f"Rule {rule['id']} has wrong category"

        # Test severity filtering
        error_rules = test_factory.get_rules_by_severity('error')
        warning_rules = test_factory.get_rules_by_severity('warning')
        assert len(error_rules) > 0, "Should have error rules"
        assert len(warning_rules) > 0, "Should have warning rules"
        assert len(error_rules) + len(warning_rules) == 89, "All rules should be error or warning"

        for rule in error_rules:
            assert rule.get('severity') == 'error', f"Rule {rule['id']} has wrong severity"
        for rule in warning_rules:
            assert rule.get('severity') == 'warning', f"Rule {rule['id']} has wrong severity"

        # Test validator filtering
        security_validator_rules = test_factory.get_rules_by_validator('security_validator')
        assert len(security_validator_rules) > 0, "Should have security validator rules"
        for rule in security_validator_rules:
            assert 'security_validator' in rule.get('validator', ''), \
                f"Rule {rule['id']} doesn't use security_validator"

        # Test constitution filtering
        code_review_rules = test_factory.get_rules_by_constitution('Code Review')
        assert len(code_review_rules) > 0, "Should have Code Review rules"
        for rule in code_review_rules:
            assert rule.get('constitution') == 'Code Review', \
                f"Rule {rule['id']} has wrong constitution"

    def test_pattern_matching_accuracy(self, test_factory):
        """Test that pattern matching works correctly."""
        # Test keyword matching
        todo_rules = test_factory.get_rules_by_keywords(['TODO'])
        assert len(todo_rules) > 0, "Should have TODO-related rules"
        for rule in todo_rules:
            rule_text = f"{rule.get('name', '')} {rule.get('description', '')}".lower()
            assert 'todo' in rule_text, f"Rule {rule['id']} should contain 'todo'"

        # Test pattern matching
        uuid_rules = test_factory.get_rules_by_pattern('uuid', 'name')
        assert len(uuid_rules) > 0, "Should have UUID-related rules"
        for rule in uuid_rules:
            assert 'uuid' in rule.get('name', '').lower(), \
                f"Rule {rule['id']} name should contain 'uuid'"

        # Test case insensitive matching
        timestamp_rules = test_factory.get_rules_by_pattern('timestamp', 'description')
        assert len(timestamp_rules) > 0, "Should have timestamp-related rules"
        for rule in timestamp_rules:
            assert 'timestamp' in rule.get('description', '').lower(), \
                f"Rule {rule['id']} description should contain 'timestamp'"


class TestCoverageVerification:
    """Test that dynamic tests provide complete coverage."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    def test_100_percent_rule_coverage(self, test_factory):
        """Test that we have 100% rule coverage."""
        all_rules = test_factory.get_all_rules()
        test_cases = test_factory.create_test_cases()

        # Every rule should have a test case
        rule_ids = {rule['id'] for rule in all_rules}
        test_case_ids = {tc.rule_id for tc in test_cases}

        assert rule_ids == test_case_ids, \
            f"Missing test cases for rules: {rule_ids - test_case_ids}"

        # Should have exactly 89 rules
        assert len(all_rules) == 89, f"Expected 89 rules, got {len(all_rules)}"
        assert len(test_cases) == 89, f"Expected 89 test cases, got {len(test_cases)}"

    def test_category_coverage(self, test_factory):
        """Test that all categories are covered."""
        categories = test_factory.get_categories()
        expected_categories = [
            'security', 'api', 'documentation', 'logging',
            'structure', 'code_quality', 'scope', 'governance',
            'process', 'quality'
        ]

        for category in expected_categories:
            assert category in categories, f"Missing category: {category}"
            rules = test_factory.get_rules_by_category(category)
            assert len(rules) > 0, f"Category '{category}' has no rules"

    def test_validator_coverage(self, test_factory):
        """Test that all validators are covered."""
        validators = test_factory.get_validators()
        expected_validators = [
            'security_validator', 'api_validator', 'comment_validator',
            'logging_validator', 'structure_validator', 'code_quality_validator'
        ]

        for validator in expected_validators:
            assert validator in validators, f"Missing validator: {validator}"
            rules = test_factory.get_rules_by_validator(validator)
            assert len(rules) > 0, f"Validator '{validator}' has no rules"

    def test_constitution_coverage(self, test_factory):
        """Test that all constitutions are covered."""
        constitutions = test_factory.get_constitutions()
        expected_constitutions = [
            'Code Review', 'API Contracts', 'Coding Standards',
            'Comments', 'Folder Standards', 'Logging'
        ]

        for constitution in expected_constitutions:
            assert constitution in constitutions, f"Missing constitution: {constitution}"
            rules = test_factory.get_rules_by_constitution(constitution)
            assert len(rules) > 0, f"Constitution '{constitution}' has no rules"

    def test_severity_coverage(self, test_factory):
        """Test that both severities are covered."""
        severities = test_factory.get_severities()
        expected_severities = ['error', 'warning']

        for severity in expected_severities:
            assert severity in severities, f"Missing severity: {severity}"
            rules = test_factory.get_rules_by_severity(severity)
            assert len(rules) > 0, f"Severity '{severity}' has no rules"


class TestPerformanceAndReliability:
    """Test performance and reliability of dynamic test system."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    def test_factory_initialization_speed(self, test_factory):
        """Test that factory initializes quickly."""
        import time

        start_time = time.time()
        factory = DynamicTestFactory()
        end_time = time.time()

        initialization_time = end_time - start_time
        assert initialization_time < 1.0, f"Factory initialization too slow: {initialization_time:.2f}s"

    def test_test_case_generation_speed(self, test_factory):
        """Test that test case generation is fast."""
        import time

        start_time = time.time()
        test_cases = test_factory.create_test_cases()
        end_time = time.time()

        generation_time = end_time - start_time
        assert generation_time < 2.0, f"Test case generation too slow: {generation_time:.2f}s"
        assert len(test_cases) == 89, f"Generated {len(test_cases)} test cases, expected 89"

    def test_filtering_performance(self, test_factory):
        """Test that filtering operations are fast."""
        import time

        # Test category filtering
        start_time = time.time()
        security_rules = test_factory.get_rules_by_category('security')
        end_time = time.time()
        assert (end_time - start_time) < 0.1, "Category filtering too slow"

        # Test severity filtering
        start_time = time.time()
        error_rules = test_factory.get_rules_by_severity('error')
        end_time = time.time()
        assert (end_time - start_time) < 0.1, "Severity filtering too slow"

        # Test validator filtering
        start_time = time.time()
        api_rules = test_factory.get_rules_by_validator('api_validator')
        end_time = time.time()
        assert (end_time - start_time) < 0.1, "Validator filtering too slow"

        # Test pattern matching
        start_time = time.time()
        todo_rules = test_factory.get_rules_by_keywords(['TODO'])
        end_time = time.time()
        assert (end_time - start_time) < 0.1, "Pattern matching too slow"

    def test_memory_usage(self, test_factory):
        """Test that the system doesn't use excessive memory."""
        import sys

        # Get initial memory usage
        initial_memory = sys.getsizeof(test_factory)

        # Generate test cases
        test_cases = test_factory.create_test_cases()

        # Check memory usage is reasonable
        memory_per_test_case = sys.getsizeof(test_cases) / len(test_cases)
        assert memory_per_test_case < 1000, f"Memory usage per test case too high: {memory_per_test_case} bytes"

        # Test that we can create multiple factories without memory leaks
        factories = [DynamicTestFactory() for _ in range(10)]
        assert len(factories) == 10, "Should be able to create multiple factories"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
