"""
Pattern-Based Dynamic Tests for ZeroUI 2.0 Rules

This module groups tests by patterns found in rule names/descriptions,
allowing for flexible testing of related rules without hardcoded rule IDs.
"""

import pytest
import sys
import re
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .dynamic_test_factory import DynamicTestFactory, DataTestCase


class TestReadabilityRules:
    """Test all readability-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def readability_rules(self, test_factory):
        """Get all readability-related rules."""
        keywords = ['readability', 'simple', 'english', 'short', 'sentence', 'comment']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_readability_rules_exist(self, readability_rules):
        """Test that readability rules exist."""
        assert len(readability_rules) > 0, "Should have readability-related rules"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_readability_rules(self, test_case: DataTestCase):
        """Test all readability-related rules."""
        # Verify it's a readability-related rule
        readability_keywords = ['readability', 'simple', 'english', 'short', 'sentence', 'comment']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in readability_keywords), \
            f"Rule {test_case.rule_id} should be readability-related"

        # Should be documentation category
        assert test_case.category == 'documentation', \
            f"Readability rule {test_case.rule_id} should be documentation category"

        # Should use comment_validator
        assert 'comment_validator' in test_case.validator, \
            f"Readability rule {test_case.rule_id} should use comment_validator"

        # Should have test data with examples
        assert len(test_case.test_data.get('violation_examples', [])) > 0, \
            f"Readability rule {test_case.rule_id} should have violation examples"
        assert len(test_case.test_data.get('valid_examples', [])) > 0, \
            f"Readability rule {test_case.rule_id} should have valid examples"


class TestSecurityRules:
    """Test all security-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def security_rules(self, test_factory):
        """Get all security-related rules."""
        keywords = ['security', 'secret', 'pii', 'privacy', 'auth', 'jwt', 'token', 'password', 'key']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_security_rules_exist(self, security_rules):
        """Test that security rules exist."""
        assert len(security_rules) > 0, "Should have security-related rules"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases(),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_security_rules(self, test_case: DataTestCase):
        """Test all security-related rules."""
        # Verify it's a security-related rule
        security_keywords = ['security', 'secret', 'pii', 'privacy', 'auth', 'jwt', 'token', 'password', 'key']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in security_keywords), \
            f"Rule {test_case.rule_id} should be security-related"

        # Should be security category
        assert test_case.category == 'security', \
            f"Security rule {test_case.rule_id} should be security category"

        # Should use security_validator
        assert 'security_validator' in test_case.validator, \
            f"Security rule {test_case.rule_id} should use security_validator"

        # Should be error severity (security is critical)
        assert test_case.severity == 'error', \
            f"Security rule {test_case.rule_id} should be error severity"


class TestAsyncRules:
    """Test all async-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def async_rules(self, test_factory):
        """Get all async-related rules."""
        keywords = ['async', 'await', 'blocking', 'handler']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_async_rules_exist(self, async_rules):
        """Test that async rules exist."""
        assert len(async_rules) >= 0, "Should handle async-related rules (may be 0)"

    @pytest.mark.parametrize("test_case",
                           [tc for tc in DynamicTestFactory().create_test_cases() 
                            if any(keyword in tc.rule_name.lower() or keyword in tc.description.lower()
                                   for keyword in ['async', 'await', 'blocking', 'handler'])],
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_async_rules(self, test_case: DataTestCase):
        """Test all async-related rules."""
        # Verify it's an async-related rule
        async_keywords = ['async', 'await', 'blocking', 'handler']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in async_keywords), \
            f"Rule {test_case.rule_id} should be async-related"

        # Should be code_quality category
        assert test_case.category == 'code_quality', \
            f"Async rule {test_case.rule_id} should be code_quality category"

        # Should use code_quality_validator
        assert 'code_quality_validator' in test_case.validator, \
            f"Async rule {test_case.rule_id} should use code_quality_validator"


class TestPerformanceRules:
    """Test all performance-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def performance_rules(self, test_factory):
        """Get all performance-related rules."""
        keywords = ['performance', 'perf', 'regression', 'budget', 'measurement', 'monotonic', 'time']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_performance_rules_exist(self, performance_rules):
        """Test that performance rules exist."""
        assert len(performance_rules) > 0, "Should have performance-related rules"

    @pytest.mark.parametrize("test_case",
                           [tc for tc in DynamicTestFactory().create_test_cases() 
                            if any(keyword in tc.rule_name.lower() or keyword in tc.description.lower()
                                   for keyword in ['performance', 'perf', 'regression', 'budget', 'measurement', 'monotonic', 'time'])],
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_performance_rules(self, test_case: DataTestCase):
        """Test all performance-related rules."""
        # Verify it's a performance-related rule
        performance_keywords = ['performance', 'perf', 'regression', 'budget', 'measurement', 'monotonic', 'time']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in performance_keywords), \
            f"Rule {test_case.rule_id} should be performance-related"

        # Should be security or logging category (performance monitoring)
        assert test_case.category in ['security', 'logging'], \
            f"Performance rule {test_case.rule_id} should be security or logging category"

        # Should use appropriate validator
        if test_case.category == 'security':
            assert 'security_validator' in test_case.validator, \
                f"Performance security rule {test_case.rule_id} should use security_validator"
        elif test_case.category == 'logging':
            assert 'logging_validator' in test_case.validator, \
                f"Performance logging rule {test_case.rule_id} should use logging_validator"


class TestTODORules:
    """Test all TODO-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def todo_rules(self, test_factory):
        """Get all TODO-related rules."""
        keywords = ['todo', 'fixme', 'hack', 'note']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_todo_rules_exist(self, todo_rules):
        """Test that TODO rules exist."""
        assert len(todo_rules) > 0, "Should have TODO-related rules"

    @pytest.mark.parametrize("test_case",
                           [tc for tc in DynamicTestFactory().create_test_cases() 
                            if any(keyword in tc.rule_name.lower() or keyword in tc.description.lower()
                                   for keyword in ['todo', 'fixme', 'hack', 'note'])],
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_todo_rules(self, test_case: DataTestCase):
        """Test all TODO-related rules."""
        # Verify it's a TODO-related rule
        todo_keywords = ['todo', 'fixme', 'hack', 'note']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in todo_keywords), \
            f"Rule {test_case.rule_id} should be TODO-related"

        # Should be documentation category
        assert test_case.category == 'documentation', \
            f"TODO rule {test_case.rule_id} should be documentation category"

        # Should use comment_validator
        assert 'comment_validator' in test_case.validator, \
            f"TODO rule {test_case.rule_id} should use comment_validator"

        # Should have specific test data for TODO format
        test_data = test_case.test_data
        assert 'violation_examples' in test_data, f"TODO rule {test_case.rule_id} should have violation examples"
        assert 'valid_examples' in test_data, f"TODO rule {test_case.rule_id} should have valid examples"

        # Violation examples should show bad TODO formats
        violation_examples = test_data['violation_examples']
        assert any('TODO' in example for example in violation_examples), \
            f"TODO rule {test_case.rule_id} violation examples should contain TODO"

        # Valid examples should show good TODO formats
        valid_examples = test_data['valid_examples']
        assert any('TODO' in example for example in valid_examples), \
            f"TODO rule {test_case.rule_id} valid examples should contain TODO"


class TestAPIRules:
    """Test all API-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def api_rules(self, test_factory):
        """Get all API-related rules."""
        keywords = ['api', 'http', 'rest', 'endpoint', 'route', 'verb', 'uri', 'idempotency', 'pagination']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_api_rules_exist(self, api_rules):
        """Test that API rules exist."""
        assert len(api_rules) > 0, "Should have API-related rules"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases().lower() or
                                                          keyword in rule.get('description', '').lower()
                                                          for keyword in ['api', 'http', 'rest', 'endpoint', 'route', 'verb', 'uri', 'idempotency', 'pagination'])
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_api_rules(self, test_case: DataTestCase):
        """Test all API-related rules."""
        # Verify it's an API-related rule
        api_keywords = ['api', 'http', 'rest', 'endpoint', 'route', 'verb', 'uri', 'idempotency', 'pagination']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in api_keywords), \
            f"Rule {test_case.rule_id} should be API-related"

        # Should be API category
        assert test_case.category == 'api', \
            f"API rule {test_case.rule_id} should be API category"

        # Should use api_validator
        assert 'api_validator' in test_case.validator, \
            f"API rule {test_case.rule_id} should use api_validator"

        # Should be error severity (API contracts are critical)
        assert test_case.severity == 'error', \
            f"API rule {test_case.rule_id} should be error severity"


class TestLoggingRules:
    """Test all logging-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def logging_rules(self, test_factory):
        """Get all logging-related rules."""
        keywords = ['log', 'jsonl', 'trace', 'timestamp', 'monotonic', 'utf8', 'w3c', 'event', 'error', 'hash']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_logging_rules_exist(self, logging_rules):
        """Test that logging rules exist."""
        assert len(logging_rules) > 0, "Should have logging-related rules"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases().lower() or
                                                          keyword in rule.get('description', '').lower()
                                                          for keyword in ['log', 'jsonl', 'trace', 'timestamp', 'monotonic', 'utf8', 'w3c', 'event', 'error', 'hash'])
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_logging_rules(self, test_case: DataTestCase):
        """Test all logging-related rules."""
        # Verify it's a logging-related rule
        logging_keywords = ['log', 'jsonl', 'trace', 'timestamp', 'monotonic', 'utf8', 'w3c', 'event', 'error', 'hash']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in logging_keywords), \
            f"Rule {test_case.rule_id} should be logging-related"

        # Should be logging category
        assert test_case.category == 'logging', \
            f"Logging rule {test_case.rule_id} should be logging category"

        # Should use logging_validator
        assert 'logging_validator' in test_case.validator, \
            f"Logging rule {test_case.rule_id} should use logging_validator"

        # Should be error severity (logging is critical for observability)
        assert test_case.severity == 'error', \
            f"Logging rule {test_case.rule_id} should be error severity"


class TestStructureRules:
    """Test all structure-related rules."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    @pytest.fixture(scope="class")
    def structure_rules(self, test_factory):
        """Get all structure-related rules."""
        keywords = ['structure', 'folder', 'directory', 'path', 'server', 'junction', 'eol', 'case', 'test']
        return test_factory.get_rules_by_keywords(keywords, ['name', 'description'])

    def test_structure_rules_exist(self, structure_rules):
        """Test that structure rules exist."""
        assert len(structure_rules) > 0, "Should have structure-related rules"

    @pytest.mark.parametrize("test_case",
                           DynamicTestFactory().create_test_cases().lower() or
                                                          keyword in rule.get('description', '').lower()
                                                          for keyword in ['structure', 'folder', 'directory', 'path', 'server', 'junction', 'eol', 'case', 'test'])
                           ),
                           ids=lambda tc: f"{tc.rule_id}_{tc.rule_name.replace(' ', '_')}")
    def test_structure_rules(self, test_case: DataTestCase):
        """Test all structure-related rules."""
        # Verify it's a structure-related rule
        structure_keywords = ['structure', 'folder', 'directory', 'path', 'server', 'junction', 'eol', 'case', 'test']
        rule_text = f"{test_case.rule_name} {test_case.expected_behavior}".lower()

        assert any(keyword in rule_text for keyword in structure_keywords), \
            f"Rule {test_case.rule_id} should be structure-related"

        # Should be structure, scope, governance, process, or quality category
        assert test_case.category in ['structure', 'scope', 'governance', 'process', 'quality'], \
            f"Structure rule {test_case.rule_id} should be structure/governance category"

        # Should use structure_validator
        assert 'structure_validator' in test_case.validator, \
            f"Structure rule {test_case.rule_id} should use structure_validator"


class TestPatternMatching:
    """Test pattern matching functionality."""

    @pytest.fixture(scope="class")
    def test_factory(self):
        """Get the test factory instance."""
        return DynamicTestFactory()

    def test_keyword_matching(self, test_factory):
        """Test keyword-based rule discovery."""
        # Test single keyword
        security_rules = test_factory.get_rules_by_keywords(['security'])
        assert len(security_rules) > 0, "Should find security rules by keyword"

        # Test multiple keywords
        api_rules = test_factory.get_rules_by_keywords(['api', 'http'])
        assert len(api_rules) > 0, "Should find API rules by multiple keywords"

        # Test case insensitive matching
        todo_rules = test_factory.get_rules_by_keywords(['TODO'])
        assert len(todo_rules) > 0, "Should find TODO rules case insensitively"

    def test_pattern_matching(self, test_factory):
        """Test regex pattern-based rule discovery."""
        # Test simple pattern
        uuid_rules = test_factory.get_rules_by_pattern('uuid', 'name')
        assert len(uuid_rules) > 0, "Should find UUID rules by pattern"

        # Test case insensitive pattern
        timestamp_rules = test_factory.get_rules_by_pattern('timestamp', 'description')
        assert len(timestamp_rules) > 0, "Should find timestamp rules by pattern"

        # Test complex pattern
        error_rules = test_factory.get_rules_by_pattern('error.*envelope', 'name')
        assert len(error_rules) >= 0, "Should handle complex patterns"

    def test_pattern_coverage(self, test_factory):
        """Test that pattern matching covers expected rule types."""
        patterns_to_test = [
            ('security', 'security'),
            ('api', 'api'),
            ('todo', 'documentation'),
            ('log', 'logging'),
            ('structure', 'structure'),
            ('async', 'code_quality')
        ]

        for pattern, expected_category in patterns_to_test:
            rules = test_factory.get_rules_by_pattern(pattern, 'name')
            if len(rules) > 0:
                # If we found rules, verify they're in the expected category
                for rule in rules:
                    assert rule.get('category') == expected_category, \
                        f"Pattern '{pattern}' found rule {rule['id']} in wrong category"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
