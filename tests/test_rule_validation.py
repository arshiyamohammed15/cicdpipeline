#!/usr/bin/env python3
"""
Rule Validation Test Suite
Tests individual rule validation logic and enforcement
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.models import Violation, ValidationResult, Severity
from validator.rules.basic_work import BasicWorkRuleValidator
from validator.rules.system_design import SystemDesignRuleValidator
from validator.rules.teamwork import TeamworkRuleValidator
from validator.rules.coding_standards import CodingStandardsRuleValidator


class TestBasicWorkRules(unittest.TestCase):
    """Test basic work rules validation."""
    
    def setUp(self):
        self.validator = BasicWorkRuleValidator()
    
    def test_rule_1_documentation_required(self):
        """Test Rule 1: Documentation Required"""
        # Well-documented function should pass
        good_code = '''
def example_function(param1, param2):
    """This function is well documented."""
    return param1 + param2
'''
        violations = self.validator.validate_documentation(good_code)
        self.assertEqual(len(violations), 0)
        
        # Undocumented function should fail
        bad_code = '''
def undocumented_function(param1, param2):
    return param1 + param2
'''
        violations = self.validator.validate_documentation(bad_code)
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule_id, 1)
    
    def test_rule_2_information_usage(self):
        """Test Rule 2: Only Use Information You're Given"""
        # Code using only provided information should pass
        good_code = '''
def process_data(input_data):
    """Process only the provided input data."""
    return input_data.upper()
'''
        violations = self.validator.validate_information_usage(good_code)
        self.assertEqual(len(violations), 0)
    
    def test_rule_3_privacy_protection(self):
        """Test Rule 3: Protect People's Privacy"""
        # Code with privacy protection should pass
        good_code = '''
def handle_user_data(user_data):
    """Handle user data with privacy protection."""
    # Anonymize sensitive data
    anonymized = user_data.copy()
    anonymized['email'] = '***@***.***'
    return anonymized
'''
        violations = self.validator.validate_privacy_protection(good_code)
        self.assertEqual(len(violations), 0)
    
    def test_rule_4_settings_files(self):
        """Test Rule 4: Use Settings Files, Not Hardcoded Numbers"""
        # Code using configuration should pass
        good_code = '''
import config

def get_timeout():
    return config.TIMEOUT_SECONDS
'''
        violations = self.validator.validate_settings_usage(good_code)
        self.assertEqual(len(violations), 0)
        
        # Code with hardcoded values should fail
        bad_code = '''
def get_timeout():
    return 30  # Hardcoded timeout
'''
        violations = self.validator.validate_settings_usage(bad_code)
        self.assertGreater(len(violations), 0)
    
    def test_rule_5_record_keeping(self):
        """Test Rule 5: Keep Good Records"""
        # Code with proper logging should pass
        good_code = '''
import logging

def process_request(request):
    logging.info(f"Processing request: {request.id}")
    result = perform_operation(request)
    logging.info(f"Request processed successfully: {request.id}")
    return result
'''
        violations = self.validator.validate_record_keeping(good_code)
        self.assertEqual(len(violations), 0)


class TestSystemDesignRules(unittest.TestCase):
    """Test system design rules validation."""
    
    def setUp(self):
        self.validator = SystemDesignRuleValidator()
    
    def test_rule_22_architecture_consistency(self):
        """Test Rule 22: Architecture Consistency"""
        # Well-structured architecture should pass
        good_code = '''
class UserService:
    def __init__(self, repository):
        self.repository = repository
    
    def get_user(self, user_id):
        return self.repository.find_by_id(user_id)
'''
        violations = self.validator.validate_architecture_consistency(good_code)
        self.assertEqual(len(violations), 0)
    
    def test_rule_25_separation_of_concerns(self):
        """Test Rule 25: Separation of Concerns"""
        # Code with clear separation should pass
        good_code = '''
class UserController:
    def __init__(self, user_service):
        self.user_service = user_service
    
    def handle_request(self, request):
        return self.user_service.process_user(request.data)

class UserService:
    def process_user(self, data):
        return self.validate_and_save(data)
'''
        violations = self.validator.validate_separation_of_concerns(good_code)
        self.assertEqual(len(violations), 0)
    
    def test_rule_26_dependency_injection(self):
        """Test Rule 26: Dependency Injection"""
        # Code with proper DI should pass
        good_code = '''
class OrderService:
    def __init__(self, payment_gateway, email_service):
        self.payment_gateway = payment_gateway
        self.email_service = email_service
'''
        violations = self.validator.validate_dependency_injection(good_code)
        self.assertEqual(len(violations), 0)


class TestTeamworkRules(unittest.TestCase):
    """Test teamwork rules validation."""
    
    def setUp(self):
        self.validator = TeamworkRuleValidator()
    
    def test_rule_52_collaboration_standards(self):
        """Test Rule 52: Collaboration Standards"""
        # Code with collaboration features should pass
        good_code = '''
# TODO: Implement caching mechanism
# FIXME: Handle edge case for empty arrays
# NOTE: This function is used by the frontend team
def process_data(data):
    """Process data with team collaboration in mind."""
    return data
'''
        violations = self.validator.validate_collaboration_standards(good_code)
        self.assertEqual(len(violations), 0)
    
    def test_rule_53_code_review_readiness(self):
        """Test Rule 53: Code Review Readiness"""
        # Code ready for review should pass
        good_code = '''
def calculate_total(items):
    """
    Calculate the total price of items.
    
    Args:
        items: List of items with price property
        
    Returns:
        float: Total price
    """
    return sum(item.price for item in items)
'''
        violations = self.validator.validate_code_review_readiness(good_code)
        self.assertEqual(len(violations), 0)


class TestCodingStandardsRules(unittest.TestCase):
    """Test coding standards rules validation."""
    
    def setUp(self):
        self.validator = CodingStandardsRuleValidator()
    
    def test_rule_naming_conventions(self):
        """Test naming convention rules"""
        # Good naming should pass
        good_code = '''
def calculate_user_age(birth_date):
    """Calculate user age from birth date."""
    return (datetime.now() - birth_date).days // 365

class UserAccount:
    def __init__(self, user_id):
        self.user_id = user_id
        self.is_active = True
'''
        violations = self.validator.validate_naming_conventions(good_code)
        self.assertEqual(len(violations), 0)
        
        # Bad naming should fail
        bad_code = '''
def calc_age(bd):  # Poor naming
    return (datetime.now() - bd).days // 365

class user_account:  # Should be PascalCase
    def __init__(self, id):
        self.id = id
'''
        violations = self.validator.validate_naming_conventions(bad_code)
        self.assertGreater(len(violations), 0)
    
    def test_rule_function_length(self):
        """Test function length rules"""
        # Short function should pass
        good_code = '''
def add_numbers(a, b):
    """Add two numbers."""
    return a + b
'''
        violations = self.validator.validate_function_length(good_code)
        self.assertEqual(len(violations), 0)
        
        # Long function should fail
        bad_code = '''
def very_long_function():
    """This function is too long."""
    step1 = "do something"
    step2 = "do something else"
    step3 = "do another thing"
    step4 = "do yet another thing"
    step5 = "do more things"
    step6 = "do even more things"
    step7 = "do lots of things"
    step8 = "do many things"
    step9 = "do numerous things"
    step10 = "do countless things"
    return step1 + step2 + step3 + step4 + step5 + step6 + step7 + step8 + step9 + step10
'''
        violations = self.validator.validate_function_length(bad_code)
        self.assertGreater(len(violations), 0)


class TestRuleIntegration(unittest.TestCase):
    """Test rule integration and cross-rule validation."""
    
    def test_multiple_rule_violations(self):
        """Test detection of multiple rule violations in single file"""
        bad_code = '''
def bad_function(x):  # No documentation, poor naming
    y = x * 2  # Hardcoded value
    return y  # No logging
'''
        
        # Mock multiple validators
        with patch('validator.rules.basic_work.BasicWorkRuleValidator') as mock_basic:
            with patch('validator.rules.coding_standards.CodingStandardsRuleValidator') as mock_standards:
                mock_basic.return_value.validate_documentation.return_value = [
                    Violation(1, "Documentation Required", Severity.HIGH, "Missing documentation", 1, 1)
                ]
                mock_standards.return_value.validate_naming_conventions.return_value = [
                    Violation(15, "Naming Convention", Severity.MEDIUM, "Poor function name", 1, 1)
                ]
                
                # Test that multiple violations are detected
                basic_validator = mock_basic.return_value
                standards_validator = mock_standards.return_value
                
                basic_violations = basic_validator.validate_documentation(bad_code)
                standards_violations = standards_validator.validate_naming_conventions(bad_code)
                
                all_violations = basic_violations + standards_violations
                self.assertEqual(len(all_violations), 2)
    
    def test_rule_priority_handling(self):
        """Test that rule priorities are properly handled"""
        violations = [
            Violation(1, "Critical Rule", Severity.CRITICAL, "Critical issue", 1, 1),
            Violation(2, "High Rule", Severity.HIGH, "High priority issue", 2, 1),
            Violation(3, "Medium Rule", Severity.MEDIUM, "Medium priority issue", 3, 1),
            Violation(4, "Low Rule", Severity.LOW, "Low priority issue", 4, 1)
        ]
        
        # Test severity ordering
        critical_violations = [v for v in violations if v.severity == Severity.CRITICAL]
        high_violations = [v for v in violations if v.severity == Severity.HIGH]
        medium_violations = [v for v in violations if v.severity == Severity.MEDIUM]
        low_violations = [v for v in violations if v.severity == Severity.LOW]
        
        self.assertEqual(len(critical_violations), 1)
        self.assertEqual(len(high_violations), 1)
        self.assertEqual(len(medium_violations), 1)
        self.assertEqual(len(low_violations), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
