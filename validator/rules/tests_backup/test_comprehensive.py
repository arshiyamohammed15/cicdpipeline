#!/usr/bin/env python3
"""
Comprehensive test suite for all ZeroUI2.0 Constitution rules.

This test validates the entire rule system end-to-end.
"""

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from dynamic_test_factory import DynamicTestFactory
from validator.core import ConstitutionValidator

class TestComprehensiveValidation:
    """Comprehensive test suite for all rules."""
    
    @pytest.fixture
    def factory(self):
        """Get the dynamic test factory."""
        return DynamicTestFactory()
    
    @pytest.fixture
    def validator(self):
        """Get the constitution validator."""
        return ConstitutionValidator()
    
    def test_all_rules_defined(self, factory):
        """Test that all expected rules are defined in the factory."""
        all_rules = factory.get_all_rules()
        rule_ids = {rule["id"] for rule in all_rules}
        
        # Expected rule count based on rules_config.json
        expected_count = 89
        assert len(all_rules) == expected_count, f"Expected {expected_count} rules, found {len(all_rules)}"
        
        # Check for L-series rules (1-77)
        l_rules = {f"L{i:03d}" for i in range(1, 78)}
        missing_l_rules = l_rules - rule_ids
        assert not missing_l_rules, f"Missing L-series rules: {missing_l_rules}"
        
        # Check for R-series rules (1-89)
        r_rules = {f"R{i:03d}" for i in range(1, 90)}
        missing_r_rules = r_rules - rule_ids
        # Note: Not all R-series rules may be implemented yet
        print(f"Missing R-series rules: {missing_r_rules}")
    
    def test_all_categories_covered(self, factory):
        """Test that all rule categories are properly covered."""
        all_rules = factory.get_all_rules()
        categories = {rule.get("category") for rule in all_rules if rule.get("category")}
        
        expected_categories = {
            "requirements", "security", "privacy_security", "basic_work", 
            "performance", "architecture", "system_design", "problem_solving",
            "platform", "testing_safety", "code_quality", "teamwork",
            "code_review", "api_contracts", "coding_standards", "comments",
            "folder_standards", "logging"
        }
        
        missing_categories = expected_categories - categories
        assert not missing_categories, f"Missing categories: {missing_categories}"
    
    def test_rule_metadata_consistency(self, factory):
        """Test that all rules have consistent metadata."""
        all_rules = factory.get_all_rules()
        
        for rule in all_rules:
            # Check required fields
            assert "id" in rule, f"Rule missing 'id' field: {rule}"
            assert "name" in rule, f"Rule {rule['id']} missing 'name' field"
            assert "category" in rule, f"Rule {rule['id']} missing 'category' field"
            assert "constitution" in rule, f"Rule {rule['id']} missing 'constitution' field"
            assert "severity" in rule, f"Rule {rule['id']} missing 'severity' field"
            
            # Check field values
            assert rule["severity"] in ("error", "warning", "info"), f"Invalid severity for rule {rule['id']}: {rule['severity']}"
            assert rule["category"], f"Empty category for rule {rule['id']}"
            assert rule["constitution"], f"Empty constitution for rule {rule['id']}"
    
    def test_test_case_generation(self, factory):
        """Test that test cases can be generated for all rules."""
        all_rules = factory.get_all_rules()
        
        for rule in all_rules:
            rule_id = rule["id"]
            test_cases = factory.create_test_cases(lambda x: x.get("id") == rule_id)
            
            assert len(test_cases) > 0, f"No test cases generated for rule {rule_id}"
            
            for test_case in test_cases:
                assert test_case.rule_id == rule_id, f"Test case rule_id mismatch: {test_case.rule_id} != {rule_id}"
                assert test_case.category == rule["category"], f"Test case category mismatch for rule {rule_id}"
                assert test_case.severity in ("error", "warning", "info"), f"Invalid test case severity for rule {rule_id}"
    
    def test_validator_integration(self, validator, factory):
        """Test that the validator can process all rules."""
        all_rules = factory.get_all_rules()
        
        # Create a test file with violations for each rule category
        test_content = '''
# Test file with various violations
password = "secret123"  # L003: Privacy violation
def incomplete_function():  # L001: Incomplete implementation
    # TODO: Implement this
    pass

def slow_function():  # L008: Performance issue
    for i in range(10000):
        for j in range(10000):
            pass

def undocumented_function():  # L015: Missing documentation
    pass
'''
        
        # Write test file
        test_file = Path("test_comprehensive_violations.py")
        test_file.write_text(test_content)
        
        try:
            # Validate the test file
            result = validator.validate_file(str(test_file))
            
            # Check that violations were found
            assert result.total_violations > 0, "No violations found in test file"
            assert result.compliance_score < 100, "Compliance score should be less than 100%"
            
            # Check that violations have proper structure
            for violation in result.violations:
                assert violation.rule_number, f"Violation missing rule_number: {violation}"
                assert violation.rule_name, f"Violation missing rule_name: {violation}"
                assert violation.severity, f"Violation missing severity: {violation}"
                assert violation.message, f"Violation missing message: {violation}"
                assert violation.file_path, f"Violation missing file_path: {violation}"
                assert violation.line_number > 0, f"Invalid line_number: {violation.line_number}"
        
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
    
    def test_performance_benchmark(self, validator):
        """Test that validation performance meets requirements."""
        import time
        
        # Create a larger test file
        test_content = '''
# Performance test file
import os
import sys
import json

class TestClass:
    def __init__(self):
        self.value = "test"
    
    def method1(self):
        return self.value
    
    def method2(self):
        return self.value * 2

def function1():
    return "test"

def function2():
    return "test" * 2

# Some violations
password = "secret"
def incomplete():
    pass
'''
        
        test_file = Path("test_performance.py")
        test_file.write_text(test_content)
        
        try:
            # Measure validation time
            start_time = time.time()
            result = validator.validate_file(str(test_file))
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Performance requirements: < 2 seconds per file
            assert processing_time < 2.0, f"Validation too slow: {processing_time:.3f}s > 2.0s"
            
            # Check that result is valid
            assert result.processing_time > 0, "Processing time not recorded"
            assert result.compliance_score >= 0, "Invalid compliance score"
        
        finally:
            if test_file.exists():
                test_file.unlink()
    
    def test_rule_coverage_statistics(self, factory):
        """Test rule coverage statistics."""
        all_rules = factory.get_all_rules()
        
        # Count rules by category
        category_counts = {}
        severity_counts = {}
        
        for rule in all_rules:
            category = rule.get("category", "unknown")
            severity = rule.get("severity", "unknown")
            
            category_counts[category] = category_counts.get(category, 0) + 1
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Verify we have rules in all major categories
        assert len(category_counts) >= 10, f"Too few categories: {len(category_counts)}"
        
        # Verify severity distribution
        assert severity_counts.get("error", 0) > 0, "No error-level rules found"
        assert severity_counts.get("warning", 0) > 0, "No warning-level rules found"
        assert severity_counts.get("info", 0) > 0, "No info-level rules found"
        
        print(f"Category distribution: {category_counts}")
        print(f"Severity distribution: {severity_counts}")
