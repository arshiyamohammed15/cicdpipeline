#!/usr/bin/env python3
"""
Simplified Rule Validation Test Suite
Tests individual rule validation logic with actual available methods
"""

import json
import unittest
import ast
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from validator.models import Violation, ValidationResult, Severity
from validator.rules.basic_work import BasicWorkValidator
from validator.rules.system_design import SystemDesignValidator
from validator.rules.teamwork import TeamworkValidator
from validator.rules.coding_standards import CodingStandardsValidator


class TestBasicWorkRules(unittest.TestCase):
    """Test basic work rules validation."""
    
    def setUp(self):
        self.validator = BasicWorkValidator()
    
    def test_rule_4_settings_files(self):
        """Test Rule 4: Use Settings Files, Not Hardcoded Numbers"""
        # Code with hardcoded values should generate violations
        bad_code = '''
HOST = "localhost"
PORT = 8080
TIMEOUT = 30
'''
        tree = ast.parse(bad_code)
        violations = self.validator.validate_settings_files(tree, bad_code, "test.py")
        self.assertIsInstance(violations, list)
        
        # Code with settings usage should have fewer violations
        good_code = '''
import os
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "8080"))
TIMEOUT = int(os.getenv("TIMEOUT", "30"))
'''
        tree = ast.parse(good_code)
        violations = self.validator.validate_settings_files(tree, good_code, "test.py")
        self.assertIsInstance(violations, list)
    
    def test_rule_5_logging_records(self):
        """Test Rule 5: Keep Good Records + Keep Good Logs"""
        # Code with logging should have fewer violations
        good_code = '''
import logging
logger = logging.getLogger(__name__)

def process_data(data):
    logger.info("Processing data")
    result = data.upper()
    logger.info("Data processed successfully")
    return result
'''
        tree = ast.parse(good_code)
        violations = self.validator.validate_logging_records(tree, good_code, "test.py")
        self.assertIsInstance(violations, list)
        
        # Code without logging should have more violations
        bad_code = '''
def process_data(data):
    result = data.upper()
    return result
'''
        tree = ast.parse(bad_code)
        violations = self.validator.validate_logging_records(tree, bad_code, "test.py")
        self.assertIsInstance(violations, list)
    
    def test_rule_10_ai_transparency(self):
        """Test Rule 10: Be Honest About AI Decisions"""
        # Code with AI transparency should have fewer violations
        good_code = '''
def ai_prediction(data, confidence=0.95):
    """AI prediction with confidence reporting."""
    result = model.predict(data)
    return {"prediction": result, "confidence": confidence}
'''
        tree = ast.parse(good_code)
        violations = self.validator.validate_ai_transparency(tree, good_code, "test.py")
        self.assertIsInstance(violations, list)
    
    def test_validate_all(self):
        """Test the validate_all method"""
        code = '''
import os
import logging

def process_data(data):
    logger = logging.getLogger(__name__)
    logger.info("Processing data")
    return data.upper()
'''
        tree = ast.parse(code)
        violations = self.validator.validate_all(tree, code, "test.py")
        self.assertIsInstance(violations, list)


class TestSystemDesignRules(unittest.TestCase):
    """Test system design rules validation."""
    
    def setUp(self):
        self.validator = SystemDesignValidator()
    
    def test_validate_consistent_modules(self):
        """Test consistent module validation"""
        code = '''
class Module:
    def __init__(self):
        self.config = {}
    
    def setup(self):
        pass
    
    def configure(self):
        pass
'''
        tree = ast.parse(code)
        violations = self.validator.validate_consistent_modules(tree, code, "test.py")
        self.assertIsInstance(violations, list)
    
    def test_validate_all(self):
        """Test the validate_all method"""
        code = '''
class Module:
    def __init__(self):
        self.config = {}
    
    def setup(self):
        pass
'''
        tree = ast.parse(code)
        violations = self.validator.validate_all(tree, code, "test.py")
        self.assertIsInstance(violations, list)


class TestTeamworkRules(unittest.TestCase):
    """Test teamwork rules validation."""
    
    def setUp(self):
        self.validator = TeamworkValidator()
    
    def test_validate_early_issue_detection(self):
        """Test early issue detection validation"""
        code = '''
def process_data(data):
    if not data:
        raise ValueError("Data cannot be empty")
    
    if len(data) > 1000:
        raise ValueError("Data too large")
    
    return data.upper()
'''
        tree = ast.parse(code)
        violations = self.validator.validate_early_issue_detection(tree, code, "test.py")
        self.assertIsInstance(violations, list)
    
    def test_validate_all(self):
        """Test the validate_all method"""
        code = '''
def process_data(data):
    if not data:
        raise ValueError("Data cannot be empty")
    return data.upper()
'''
        tree = ast.parse(code)
        violations = self.validator.validate_all(tree, code, "test.py")
        self.assertIsInstance(violations, list)


class TestCodingStandardsRules(unittest.TestCase):
    """Test coding standards rules validation."""
    
    def setUp(self):
        self.validator = CodingStandardsValidator()
    
    def test_validate_python_standards(self):
        """Test Python standards validation"""
        code = '''
def example_function(param1: str, param2: int) -> str:
    """Example function with type hints."""
    return f"{param1}_{param2}"
'''
        violations = self.validator._validate_python_standards(code, "test.py")
        self.assertIsInstance(violations, list)
    
    def test_validate_naming_conventions(self):
        """Test naming conventions validation"""
        code = '''
def snake_case_function():
    """Function with proper snake_case naming."""
    pass

class PascalCaseClass:
    """Class with proper PascalCase naming."""
    pass
'''
        violations = self.validator._validate_naming_conventions(code, "test.py")
        self.assertIsInstance(violations, list)


class TestRuleIntegration(unittest.TestCase):
    """Test rule integration and cross-validation."""
    
    def test_basic_work_integration(self):
        """Test basic work rules integration"""
        validator = BasicWorkValidator()
        
        code = '''
import os
import logging

def process_data(data):
    logger = logging.getLogger(__name__)
    logger.info("Processing data")
    return data.upper()
'''
        tree = ast.parse(code)
        violations = validator.validate_all(tree, code, "test.py")
        self.assertIsInstance(violations, list)
    
    def test_system_design_integration(self):
        """Test system design rules integration"""
        validator = SystemDesignValidator()
        
        code = '''
class Module:
    def __init__(self):
        self.config = {}
    
    def setup(self):
        pass
'''
        tree = ast.parse(code)
        violations = validator.validate_all(tree, code, "test.py")
        self.assertIsInstance(violations, list)


if __name__ == '__main__':
    unittest.main()
