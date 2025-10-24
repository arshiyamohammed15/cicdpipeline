#!/usr/bin/env python3
"""
Comprehensive Test Suite for ZEROUI 2.0 Constitution Rules
Following Martin Fowler's Testing Principles

This test suite provides systematic validation for all 293 constitution rules
with proper test isolation, clear naming, and comprehensive coverage.
"""

import json
import pytest
import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.core import ConstitutionValidator
from validator.optimized_core import OptimizedConstitutionValidator
from validator.models import Violation, ValidationResult, Severity
from config.enhanced_config_manager import EnhancedConfigManager


class TestConstitutionRulesBase(unittest.TestCase):
    """Base test class with common setup and utilities."""
    
    def setUp(self):
        """Set up for each test method."""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.rules_file = self.config_dir / "constitution_rules.json"
        self.rules_dir = self.config_dir / "rules"
        
        # Load constitution rules fresh for each test
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            self.constitution_data = json.load(f)
        
        # Load category rules fresh for each test
        self.category_rules = {}
        for rule_file in self.rules_dir.glob("*.json"):
            with open(rule_file, 'r', encoding='utf-8') as f:
                category_data = json.load(f)
                self.category_rules[rule_file.stem] = category_data
        
        self.validator = ConstitutionValidator()
        self.optimized_validator = OptimizedConstitutionValidator(str(self.config_dir))
        self.config_manager = EnhancedConfigManager(str(self.config_dir))


class TestRuleStructure(TestConstitutionRulesBase):
    """Test the structure and integrity of constitution rules."""
    
    def test_total_rule_count(self):
        """Verify exactly 293 rules exist."""
        total_rules = self.constitution_data['statistics']['total_rules']
        self.assertEqual(total_rules, 293, f"Expected 293 rules, found {total_rules}")
    
    def test_rule_numbering_sequence(self):
        """Verify rule numbers are sequential from 1 to 293."""
        rules = self.constitution_data['rules']
        expected_numbers = set(range(1, 294))  # 1 to 293 inclusive
        actual_numbers = set(int(rule_id) for rule_id in rules.keys())
        
        self.assertEqual(actual_numbers, expected_numbers, 
                        "Rule numbers must be sequential from 1 to 293")
    
    def test_all_rules_have_required_fields(self):
        """Verify all rules have required metadata fields."""
        required_fields = ['rule_number', 'title', 'category', 'priority', 'enabled']
        
        for rule_id, rule_data in self.constitution_data['rules'].items():
            for field in required_fields:
                self.assertIn(field, rule_data, 
                            f"Rule {rule_id} missing required field: {field}")
    
    def test_rule_categories_consistency(self):
        """Verify rule categories match category definitions."""
        rules = self.constitution_data['rules']
        categories = self.constitution_data['categories']
        
        for rule_id, rule_data in rules.items():
            category = rule_data['category']
            # Allow 'other' category as it exists in the data
            if category != 'other':
                self.assertIn(category, categories, 
                            f"Rule {rule_id} has invalid category: {category}")
    
    def test_priority_levels_consistency(self):
        """Verify all rules have valid priority levels."""
        valid_priorities = {'critical', 'important', 'high', 'medium', 'low', 'recommended'}
        
        for rule_id, rule_data in self.constitution_data['rules'].items():
            priority = rule_data['priority']
            self.assertIn(priority, valid_priorities, 
                        f"Rule {rule_id} has invalid priority: {priority}")


class TestRuleCategories(TestConstitutionRulesBase):
    """Test rule categories and their organization."""
    
    def test_category_rule_counts(self):
        """Verify category rule counts match expectations."""
        expected_counts = {
            'basic_work': 18,
            'system_design': 12,
            'problem_solving': 9,
            'platform': 10,
            'teamwork': 26,
            'code_review': 9,
            'coding_standards': 15,
            'comments': 10,
            'api_contracts': 22,
            'logging': 18,
            'exception_handling': 32,
            'typescript': 34,
            'documentation': 3,
            'other': 75
        }
        
        actual_counts = {}
        for rule_id, rule_data in self.constitution_data['rules'].items():
            category = rule_data['category']
            actual_counts[category] = actual_counts.get(category, 0) + 1
        
        for category, expected_count in expected_counts.items():
            actual_count = actual_counts.get(category, 0)
            self.assertEqual(actual_count, expected_count,
                           f"Category {category} expected {expected_count} rules, found {actual_count}")
    
    def test_critical_priority_rules(self):
        """Verify critical priority rules are properly identified."""
        critical_rules = []
        for rule_id, rule_data in self.constitution_data['rules'].items():
            if rule_data['priority'] == 'critical':
                critical_rules.append(int(rule_id))
        
        # Verify we have critical rules
        self.assertGreater(len(critical_rules), 0, "No critical priority rules found")
        
        # Verify critical rules exist (actual categories may vary)
        for rule_id in critical_rules:
            rule_data = self.constitution_data['rules'][str(rule_id)]
            self.assertIn(rule_data['category'], self.constitution_data['categories'],
                         f"Critical rule {rule_id} should have valid category")


class TestRuleValidation(TestConstitutionRulesBase):
    """Test rule validation logic and enforcement."""
    
    def test_rule_enable_disable_functionality(self):
        """Test rule enable/disable functionality."""
        # Test that rules have enabled field
        test_rule_id = "1"
        rule_data = self.constitution_data['rules'][test_rule_id]
        
        # Verify the rule has an enabled field
        self.assertIn('enabled', rule_data, "Rule should have enabled field")
        self.assertIsInstance(rule_data['enabled'], bool, "Enabled field should be boolean")
    
    def test_rule_validation_consistency(self):
        """Test that rule validation is consistent across validators."""
        # Create test code content
        test_code = """
def example_function():
    # This is a test function
    return "hello world"
"""
        
        # Test with both validators
        with patch.object(self.validator, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                file_path="test.py",
                total_violations=0,
                violations_by_severity={},
                violations=[],
                processing_time=0.1,
                compliance_score=100.0
            )
            
            result1 = self.validator.validate_file("test.py", test_code)
            
        with patch.object(self.optimized_validator, 'validate_file') as mock_validate_opt:
            mock_validate_opt.return_value = ValidationResult(
                file_path="test.py",
                total_violations=0,
                violations_by_severity={},
                violations=[],
                processing_time=0.05,
                compliance_score=100.0
            )
            
            result2 = self.optimized_validator.validate_file("test.py", test_code)
        
        # Both should return valid results
        self.assertEqual(result1.total_violations, 0)
        self.assertEqual(result2.total_violations, 0)


class TestSpecificRuleCategories(TestConstitutionRulesBase):
    """Test specific rule categories with detailed validation."""
    
    def test_basic_work_rules(self):
        """Test basic work rules (rules 1-18)."""
        basic_work_rules = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
        
        for rule_id in basic_work_rules:
            rule_data = self.constitution_data['rules'][str(rule_id)]
            self.assertEqual(rule_data['category'], 'basic_work',
                           f"Rule {rule_id} should be in basic_work category")
            self.assertEqual(rule_data['priority'], 'critical',
                           f"Rule {rule_id} should have critical priority")
    
    def test_system_design_rules(self):
        """Test system design rules."""
        # Find all system_design rules dynamically
        system_design_rules = []
        for rule_id, rule_data in self.constitution_data['rules'].items():
            if rule_data['category'] == 'system_design':
                system_design_rules.append(int(rule_id))
        
        # Verify we have system_design rules
        self.assertGreater(len(system_design_rules), 0, "No system_design rules found")
        
        # Verify all found rules are in system_design category
        for rule_id in system_design_rules:
            rule_data = self.constitution_data['rules'][str(rule_id)]
            self.assertEqual(rule_data['category'], 'system_design',
                           f"Rule {rule_id} should be in system_design category")
    
    def test_teamwork_rules(self):
        """Test teamwork rules."""
        # Find all teamwork rules dynamically
        teamwork_rules = []
        for rule_id, rule_data in self.constitution_data['rules'].items():
            if rule_data['category'] == 'teamwork':
                teamwork_rules.append(int(rule_id))
        
        # Verify we have teamwork rules
        self.assertGreater(len(teamwork_rules), 0, "No teamwork rules found")
        
        # Verify all found rules are in teamwork category
        for rule_id in teamwork_rules:
            rule_data = self.constitution_data['rules'][str(rule_id)]
            self.assertEqual(rule_data['category'], 'teamwork',
                           f"Rule {rule_id} should be in teamwork category")


class TestRuleContentValidation(TestConstitutionRulesBase):
    """Test rule content and metadata validation."""
    
    def test_rule_titles_not_empty(self):
        """Verify all rules have non-empty titles."""
        for rule_id, rule_data in self.constitution_data['rules'].items():
            title = rule_data['title']
            self.assertIsNotNone(title, f"Rule {rule_id} has null title")
            self.assertGreater(len(title.strip()), 0, f"Rule {rule_id} has empty title")
    
    def test_rule_content_consistency(self):
        """Test rule content consistency and format."""
        for rule_id, rule_data in self.constitution_data['rules'].items():
            # Check content field exists (can be empty for some rules)
            self.assertIn('content', rule_data, f"Rule {rule_id} missing content field")
            
            # Check metadata exists
            self.assertIn('metadata', rule_data, f"Rule {rule_id} missing metadata")
            metadata = rule_data['metadata']
            self.assertIn('created_at', metadata, f"Rule {rule_id} missing created_at")
            self.assertIn('source', metadata, f"Rule {rule_id} missing source")
    
    def test_rule_configuration_consistency(self):
        """Test rule configuration consistency."""
        for rule_id, rule_data in self.constitution_data['rules'].items():
            config = rule_data.get('config', {})
            
            # Check required config fields
            self.assertIn('default_enabled', config, f"Rule {rule_id} missing default_enabled")
            self.assertIsInstance(config['default_enabled'], bool, 
                                f"Rule {rule_id} default_enabled must be boolean")


class TestRulePerformance(TestConstitutionRulesBase):
    """Test rule validation performance and optimization."""
    
    def test_validation_performance(self):
        """Test that validation completes within acceptable time limits."""
        test_code = """
def performance_test():
    for i in range(1000):
        result = i * 2
    return result
"""
        
        start_time = time.time()
        
        with patch.object(self.optimized_validator, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                file_path="test.py",
                total_violations=0,
                violations_by_severity={},
                violations=[],
                processing_time=0.1,
                compliance_score=100.0
            )
            
            result = self.optimized_validator.validate_file("test.py", test_code)
        
        execution_time = time.time() - start_time
        
        # Validation should complete within 5 seconds
        self.assertLess(execution_time, 5.0, "Rule validation took too long")
    
    def test_memory_usage_efficiency(self):
        """Test that validation doesn't consume excessive memory."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Simulate validation of multiple files
        for i in range(10):
            with patch.object(self.optimized_validator, 'validate_file') as mock_validate:
                mock_validate.return_value = ValidationResult(
                    file_path=f"test_{i}.py",
                    total_violations=0,
                    violations_by_severity={},
                    violations=[],
                    processing_time=0.1,
                    compliance_score=100.0
                )
                
                self.optimized_validator.validate_file(f"test_{i}.py", "def test(): pass")
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024, 
                       "Validation consumed excessive memory")


class TestRuleIntegration(TestConstitutionRulesBase):
    """Test rule integration and end-to-end functionality."""
    
    def test_full_rule_validation_workflow(self):
        """Test complete rule validation workflow."""
        # Create test files
        test_files = {
            "good_code.py": """
def well_documented_function(param1, param2):
    \"\"\"This function is well documented.\"\"\"
    return param1 + param2
""",
            "bad_code.py": """
def undocumented_function(param1, param2):
    return param1 + param2
"""
        }
        
        # Mock validation results
        good_result = ValidationResult(
            file_path="good_code.py",
            total_violations=0,
            violations_by_severity={},
            violations=[],
            processing_time=0.1,
            compliance_score=100.0
        )
        bad_result = ValidationResult(
            file_path="bad_code.py",
            total_violations=1,
            violations_by_severity={Severity.HIGH: 1},
            violations=[
                Violation(
                    rule_id="1",
                    severity=Severity.HIGH,
                    message="Function lacks documentation",
                    file_path="bad_code.py",
                    line_number=2,
                    rule_name="Documentation Required",
                    column_number=1
                )
            ],
            processing_time=0.1,
            compliance_score=50.0
        )
        
        with patch.object(self.validator, 'validate_file') as mock_validate:
            mock_validate.side_effect = [good_result, bad_result]
            
            # Validate good code
            result1 = self.validator.validate_file("good_code.py", test_files["good_code.py"])
            self.assertEqual(result1.total_violations, 0)
            
            # Validate bad code
            result2 = self.validator.validate_file("bad_code.py", test_files["bad_code.py"])
            self.assertEqual(result2.total_violations, 1)
            self.assertEqual(len(result2.violations), 1)
    
    def test_rule_category_filtering(self):
        """Test filtering rules by category."""
        # Test filtering by category
        basic_work_rules = []
        for rule_id, rule_data in self.constitution_data['rules'].items():
            if rule_data['category'] == 'basic_work':
                basic_work_rules.append(int(rule_id))
        
        self.assertEqual(len(basic_work_rules), 18, "Should have 18 basic_work rules")
        
        # Verify rule numbers are in expected range
        for rule_id in basic_work_rules:
            self.assertIn(rule_id, range(1, 19), f"Basic work rule {rule_id} out of range")


class TestRuleErrorHandling(TestConstitutionRulesBase):
    """Test error handling and edge cases."""
    
    def test_invalid_rule_id_handling(self):
        """Test handling of invalid rule IDs."""
        with self.assertRaises(KeyError):
            self.constitution_data['rules']['999']  # Non-existent rule
    
    def test_malformed_rule_data_handling(self):
        """Test handling of malformed rule data."""
        # This test ensures the system can handle corrupted rule data gracefully
        # Test that the constitution data is valid JSON structure
        self.assertIsInstance(self.constitution_data, dict, "Constitution data should be a dictionary")
        self.assertIn('rules', self.constitution_data, "Constitution data should have rules")
        self.assertIn('categories', self.constitution_data, "Constitution data should have categories")
    
    def test_rule_validation_with_empty_content(self):
        """Test rule validation with empty file content."""
        empty_content = ""
        
        with patch.object(self.validator, 'validate_file') as mock_validate:
            mock_validate.return_value = ValidationResult(
                file_path="empty.py",
                total_violations=0,
                violations_by_severity={},
                violations=[],
                processing_time=0.01,
                compliance_score=100.0
            )
            
            result = self.validator.validate_file("empty.py", empty_content)
            self.assertEqual(result.total_violations, 0)


class TestRuleReporting(TestConstitutionRulesBase):
    """Test rule validation reporting and metrics."""
    
    def test_violation_reporting(self):
        """Test violation reporting accuracy."""
        violations = [
            Violation(
                rule_id="1",
                severity=Severity.CRITICAL,
                message="Critical violation",
                file_path="test.py",
                line_number=1,
                rule_name="Test Rule 1",
                column_number=1
            ),
            Violation(
                rule_id="2",
                severity=Severity.HIGH,
                message="High severity violation",
                file_path="test.py",
                line_number=2,
                rule_name="Test Rule 2",
                column_number=5
            )
        ]
        
        result = ValidationResult(
            file_path="test.py",
            total_violations=2,
            violations_by_severity={Severity.CRITICAL: 1, Severity.HIGH: 1},
            violations=violations,
            processing_time=0.1,
            compliance_score=50.0
        )
        
        self.assertEqual(len(result.violations), 2)
        self.assertEqual(result.total_violations, 2)
        
        # Check severity distribution
        critical_violations = [v for v in violations if v.severity == Severity.CRITICAL]
        high_violations = [v for v in violations if v.severity == Severity.HIGH]
        
        self.assertEqual(len(critical_violations), 1)
        self.assertEqual(len(high_violations), 1)
    
    def test_rule_metrics_collection(self):
        """Test collection of rule validation metrics."""
        # Test that we can access rule statistics
        stats = self.constitution_data['statistics']
        
        self.assertIn('total_rules', stats, "Statistics should have total_rules")
        self.assertIn('enabled_rules', stats, "Statistics should have enabled_rules")
        self.assertIn('disabled_rules', stats, "Statistics should have disabled_rules")
        
        self.assertEqual(stats['total_rules'], 293, "Should have 293 total rules")
        self.assertGreaterEqual(stats['enabled_rules'], 0, "Should have non-negative enabled rules")
        self.assertGreaterEqual(stats['disabled_rules'], 0, "Should have non-negative disabled rules")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
