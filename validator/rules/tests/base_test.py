"""
Base test framework for validator tests.

Provides common utilities, fixtures, and assertion helpers for all validator tests.
"""

import unittest
import ast
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from validator.models import Violation, Severity


class BaseValidatorTest(unittest.TestCase):
    """Base class for all validator tests with common utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_file_path = "test.py"
        self.config_dir = Path(__file__).parent.parent.parent.parent / "config"
    
    def assertViolation(self, violations: List[Violation], rule_id: str, 
                       severity: Severity = None, message_contains: str = None):
        """
        Assert that a specific violation exists in the violations list.
        
        Args:
            violations: List of violations to check
            rule_id: Expected rule ID
            severity: Expected severity (optional)
            message_contains: String that should be in the message (optional)
        """
        matching_violations = [v for v in violations if v.rule_id == rule_id]
        
        self.assertGreater(
            len(matching_violations), 0,
            f"Expected violation with rule_id '{rule_id}' not found. "
            f"Found violations: {[v.rule_id for v in violations]}"
        )
        
        if severity is not None:
            severity_match = [v for v in matching_violations if v.severity == severity]
            self.assertGreater(
                len(severity_match), 0,
                f"Expected severity {severity} for rule {rule_id}, "
                f"but found: {[v.severity for v in matching_violations]}"
            )
        
        if message_contains is not None:
            message_match = [v for v in matching_violations 
                           if message_contains.lower() in v.message.lower()]
            self.assertGreater(
                len(message_match), 0,
                f"Expected message containing '{message_contains}' for rule {rule_id}, "
                f"but found: {[v.message for v in matching_violations]}"
            )
    
    def assertNoViolation(self, violations: List[Violation], rule_id: str = None):
        """
        Assert that no violations exist, or no violation with specific rule_id exists.
        
        Args:
            violations: List of violations to check
            rule_id: Specific rule ID to check (optional, checks all if None)
        """
        if rule_id is None:
            self.assertEqual(
                len(violations), 0,
                f"Expected no violations, but found {len(violations)}: "
                f"{[v.rule_id for v in violations]}"
            )
        else:
            matching = [v for v in violations if v.rule_id == rule_id]
            self.assertEqual(
                len(matching), 0,
                f"Expected no violations for rule {rule_id}, but found {len(matching)}"
            )
    
    def assertViolationCount(self, violations: List[Violation], expected_count: int,
                            rule_id: str = None):
        """
        Assert the exact number of violations.
        
        Args:
            violations: List of violations to check
            expected_count: Expected number of violations
            rule_id: Specific rule ID to check (optional, checks all if None)
        """
        if rule_id is None:
            actual_count = len(violations)
            self.assertEqual(
                actual_count, expected_count,
                f"Expected {expected_count} violations, but found {actual_count}: "
                f"{[v.rule_id for v in violations]}"
            )
        else:
            matching = [v for v in violations if v.rule_id == rule_id]
            actual_count = len(matching)
            self.assertEqual(
                actual_count, expected_count,
                f"Expected {expected_count} violations for rule {rule_id}, "
                f"but found {actual_count}"
            )
    
    def loadConfigRule(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from config/*.json file.
        
        Args:
            config_file: Name of config file (e.g., 'api_contracts.json')
            
        Returns:
            Dictionary containing config data
        """
        config_path = self.config_dir / "rules" / config_file
        
        if not config_path.exists():
            self.fail(f"Config file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parseCode(self, content: str) -> ast.AST:
        """
        Parse Python code into AST.
        
        Args:
            content: Python code as string
            
        Returns:
            AST tree
        """
        try:
            return ast.parse(content)
        except SyntaxError as e:
            self.fail(f"Failed to parse code: {e}")
    
    def assertRuleExists(self, validator, rule_id: str):
        """
        Assert that a validator has a specific rule implemented.
        
        Args:
            validator: Validator instance
            rule_id: Rule ID to check
        """
        if hasattr(validator, 'rules'):
            self.assertIn(
                rule_id, validator.rules,
                f"Rule {rule_id} not found in validator.rules"
            )
    
    def getSampleCode(self, sample_name: str) -> str:
        """
        Get sample code from fixtures.
        
        Args:
            sample_name: Name of the sample
            
        Returns:
            Code content as string
        """
        from .fixtures.code_samples import CODE_SAMPLES
        
        if sample_name not in CODE_SAMPLES:
            self.fail(f"Sample code '{sample_name}' not found in fixtures")
        
        return CODE_SAMPLES[sample_name]
    
    def createViolationChecker(self):
        """Create a helper for checking violation properties."""
        class ViolationChecker:
            def __init__(self, test_case):
                self.test_case = test_case
            
            def check(self, violation: Violation, **expected):
                """Check violation properties."""
                if 'rule_id' in expected:
                    self.test_case.assertEqual(violation.rule_id, expected['rule_id'])
                if 'severity' in expected:
                    self.test_case.assertEqual(violation.severity, expected['severity'])
                if 'message_contains' in expected:
                    self.test_case.assertIn(
                        expected['message_contains'].lower(),
                        violation.message.lower()
                    )
                if 'file_path' in expected:
                    self.test_case.assertEqual(violation.file_path, expected['file_path'])
                if 'line_number' in expected:
                    self.test_case.assertEqual(violation.line_number, expected['line_number'])
        
        return ViolationChecker(self)

