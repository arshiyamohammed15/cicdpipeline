#!/usr/bin/env python3
"""
Rule Implementation Logic Tests for ZeroUI 2.0 Constitution
Tests the actual implementation logic and behavior of each rule

This test suite verifies that the codebase actually implements
the logic required by each constitution rule.
"""

import unittest
import sys
import os
import json
import time
import re
import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import importlib.util

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class RuleImplementationLogicTester:
    """Tests the actual implementation logic of constitution rules."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.config_dir = self.project_root / "config"
        self.test_results = {}
        
    def test_rule_1_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 1: Do Exactly What's Asked - Implementation Logic."""
        violations = []
        
        # Check if functions do exactly what their names suggest
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function name matches what it actually does
                        if self._function_does_more_than_name_suggests(node, content):
                            violations.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': node.lineno,
                                'function': node.name,
                                'issue': 'Function does more than its name suggests'
                            })
                            
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 1,
            'rule_name': 'Do Exactly What\'s Asked - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_2_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 2: Only Use Information You're Given - Implementation Logic."""
        violations = []
        
        # Check if code uses only provided information
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for functions that make assumptions
                if self._makes_unwarranted_assumptions(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Code makes assumptions not based on provided information'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 2,
            'rule_name': 'Only Use Information You\'re Given - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_3_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 3: Protect People's Privacy - Implementation Logic."""
        violations = []
        
        # Check if privacy protection is actually implemented
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for proper privacy protection implementation
                if self._lacks_privacy_protection(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Missing privacy protection implementation'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 3,
            'rule_name': 'Protect People\'s Privacy - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_4_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 4: Use Settings Files, Not Hardcoded Numbers - Implementation Logic."""
        violations = []
        
        # Check if configuration is properly implemented
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if file uses configuration properly
                if self._doesnt_use_configuration_properly(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Does not use configuration files properly'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 4,
            'rule_name': 'Use Settings Files, Not Hardcoded Numbers - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_5_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 5: Keep Good Records - Implementation Logic."""
        violations = []
        
        # Check if proper record keeping is implemented
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if file implements proper logging/record keeping
                if self._lacks_proper_record_keeping(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Missing proper record keeping implementation'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 5,
            'rule_name': 'Keep Good Records - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_7_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 7: Make Things Fast - Implementation Logic."""
        violations = []
        
        # Check if performance optimizations are implemented
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for performance issues
                if self._has_performance_issues(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Performance issues detected'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 7,
            'rule_name': 'Make Things Fast - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_8_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 8: Be Honest About AI Decisions - Implementation Logic."""
        violations = []
        
        # Check if AI transparency is properly implemented
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for AI transparency implementation
                if self._lacks_ai_transparency(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Missing AI decision transparency implementation'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 8,
            'rule_name': 'Be Honest About AI Decisions - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_12_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 12: Test Everything - Implementation Logic."""
        violations = []
        
        # Check if comprehensive testing is implemented
        test_coverage = self._check_test_coverage()
        if test_coverage['coverage_percentage'] < 90:
            violations.append({
                'file': 'test_coverage',
                'line': 0,
                'issue': f'Test coverage too low: {test_coverage["coverage_percentage"]:.1f}%'
            })
        
        return {
            'rule_number': 12,
            'rule_name': 'Test Everything - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0,
            'test_coverage': test_coverage
        }
    
    def test_rule_17_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 17: Keep Different Parts Separate - Implementation Logic."""
        violations = []
        
        # Check if separation of concerns is properly implemented
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for proper separation of concerns
                if self._violates_separation_of_concerns(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Violates separation of concerns'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 17,
            'rule_name': 'Keep Different Parts Separate - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_18_implementation_logic(self) -> Dict[str, Any]:
        """Test Rule 18: Be Fair to Everyone - Implementation Logic."""
        violations = []
        
        # Check if accessibility and fairness are implemented
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for accessibility implementation
                if self._lacks_accessibility_considerations(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Missing accessibility considerations'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 18,
            'rule_name': 'Be Fair to Everyone - Implementation Logic',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    # Helper methods for implementation logic validation
    def _function_does_more_than_name_suggests(self, node: ast.FunctionDef, content: str) -> bool:
        """Check if function does more than its name suggests."""
        # Simple heuristic - can be enhanced
        function_lines = len([line for line in content.split('\n')[node.lineno-1:node.end_lineno] if line.strip()])
        return function_lines > 20  # Arbitrary threshold
    
    def _makes_unwarranted_assumptions(self, content: str) -> bool:
        """Check if code makes unwarranted assumptions."""
        assumption_patterns = [
            r'# TODO.*assume',
            r'# FIXME.*assume',
            r'# NOTE.*assume',
            r'assert.*True',  # Dangerous assumptions
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in assumption_patterns)
    
    def _lacks_privacy_protection(self, content: str) -> bool:
        """Check if privacy protection is missing."""
        privacy_patterns = [
            r'redact',
            r'encrypt',
            r'hash',
            r'privacy',
            r'pii',
            r'personal.*info',
        ]
        return not any(re.search(pattern, content, re.IGNORECASE) for pattern in privacy_patterns)
    
    def _doesnt_use_configuration_properly(self, content: str) -> bool:
        """Check if configuration is not used properly."""
        config_patterns = [
            r'config',
            r'settings',
            r'environ',
            r'getenv',
        ]
        has_config = any(re.search(pattern, content, re.IGNORECASE) for pattern in config_patterns)
        has_hardcoded = re.search(r'"[^"]{5,}"', content) or re.search(r"'[^']{5,}'", content)
        return has_hardcoded and not has_config
    
    def _lacks_proper_record_keeping(self, content: str) -> bool:
        """Check if proper record keeping is missing."""
        logging_patterns = [
            r'log',
            r'record',
            r'audit',
            r'trace',
            r'receipt',
        ]
        return not any(re.search(pattern, content, re.IGNORECASE) for pattern in logging_patterns)
    
    def _has_performance_issues(self, content: str) -> bool:
        """Check for performance issues."""
        performance_issues = [
            r'for.*for.*for',  # Nested loops
            r'while.*while',   # Nested while loops
            r'time\.sleep',
            r'subprocess\.run',
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in performance_issues)
    
    def _lacks_ai_transparency(self, content: str) -> bool:
        """Check if AI transparency is missing."""
        ai_patterns = [r'ai', r'llm', r'model', r'gpt', r'openai']
        transparency_patterns = [r'confidence', r'explanation', r'version', r'transparency']
        
        has_ai = any(re.search(pattern, content, re.IGNORECASE) for pattern in ai_patterns)
        has_transparency = any(re.search(pattern, content, re.IGNORECASE) for pattern in transparency_patterns)
        
        return has_ai and not has_transparency
    
    def _check_test_coverage(self) -> Dict[str, Any]:
        """Check test coverage."""
        test_files = list(self.project_root.glob("tests/test_*.py"))
        src_files = list(self.src_dir.rglob("*.py"))
        
        # Simple coverage calculation
        coverage_percentage = (len(test_files) / max(len(src_files), 1)) * 100
        
        return {
            'test_files': len(test_files),
            'src_files': len(src_files),
            'coverage_percentage': coverage_percentage
        }
    
    def _violates_separation_of_concerns(self, content: str) -> bool:
        """Check if separation of concerns is violated."""
        ui_patterns = [r'print', r'input', r'display', r'render', r'ui']
        business_patterns = [r'calculate', r'process', r'business', r'logic']
        
        has_ui = any(re.search(pattern, content, re.IGNORECASE) for pattern in ui_patterns)
        has_business = any(re.search(pattern, content, re.IGNORECASE) for pattern in business_patterns)
        
        return has_ui and has_business
    
    def _lacks_accessibility_considerations(self, content: str) -> bool:
        """Check if accessibility considerations are missing."""
        accessibility_patterns = [
            r'accessibility',
            r'aria',
            r'alt.*text',
            r'screen.*reader',
            r'keyboard.*navigation',
        ]
        return not any(re.search(pattern, content, re.IGNORECASE) for pattern in accessibility_patterns)
    
    def run_all_implementation_logic_tests(self) -> Dict[str, Any]:
        """Run all implementation logic tests."""
        print("Running Rule Implementation Logic Tests...")
        print("=" * 80)
        
        # Test the first 18 rules as examples
        rule_tests = [
            self.test_rule_1_implementation_logic,
            self.test_rule_2_implementation_logic,
            self.test_rule_3_implementation_logic,
            self.test_rule_4_implementation_logic,
            self.test_rule_5_implementation_logic,
            self.test_rule_7_implementation_logic,
            self.test_rule_8_implementation_logic,
            self.test_rule_12_implementation_logic,
            self.test_rule_17_implementation_logic,
            self.test_rule_18_implementation_logic,
        ]
        
        results = {}
        total_violations = 0
        
        for test_func in rule_tests:
            print(f"Testing {test_func.__name__}...")
            result = test_func()
            results[result['rule_number']] = result
            total_violations += len(result['violations'])
            
            status = "PASS" if result['compliant'] else "FAIL"
            print(f"  Rule {result['rule_number']}: {result['rule_name']} - {status}")
            if result['violations']:
                print(f"    Violations: {len(result['violations'])}")
                for violation in result['violations'][:3]:  # Show first 3
                    print(f"      {violation['file']}:{violation.get('line', 0)} - {violation['issue']}")
        
        print("=" * 80)
        print(f"Total Rules Tested: {len(rule_tests)}")
        print(f"Total Violations: {total_violations}")
        print(f"Implementation Logic Compliance: {((len(rule_tests) - sum(1 for r in results.values() if not r['compliant'])) / len(rule_tests) * 100):.1f}%")
        
        return {
            'results': results,
            'total_rules_tested': len(rule_tests),
            'total_violations': total_violations,
            'compliance_rate': ((len(rule_tests) - sum(1 for r in results.values() if not r['compliant'])) / len(rule_tests) * 100)
        }


class TestRuleImplementationLogic(unittest.TestCase):
    """Test cases for rule implementation logic."""
    
    def setUp(self):
        self.tester = RuleImplementationLogicTester()
    
    def test_rule_1_implementation_logic(self):
        """Test Rule 1: Do Exactly What's Asked - Implementation Logic."""
        result = self.tester.test_rule_1_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 1 implementation logic violations: {result['violations']}")
    
    def test_rule_2_implementation_logic(self):
        """Test Rule 2: Only Use Information You're Given - Implementation Logic."""
        result = self.tester.test_rule_2_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 2 implementation logic violations: {result['violations']}")
    
    def test_rule_3_implementation_logic(self):
        """Test Rule 3: Protect People's Privacy - Implementation Logic."""
        result = self.tester.test_rule_3_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 3 implementation logic violations: {result['violations']}")
    
    def test_rule_4_implementation_logic(self):
        """Test Rule 4: Use Settings Files, Not Hardcoded Numbers - Implementation Logic."""
        result = self.tester.test_rule_4_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 4 implementation logic violations: {result['violations']}")
    
    def test_rule_5_implementation_logic(self):
        """Test Rule 5: Keep Good Records - Implementation Logic."""
        result = self.tester.test_rule_5_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 5 implementation logic violations: {result['violations']}")
    
    def test_rule_7_implementation_logic(self):
        """Test Rule 7: Make Things Fast - Implementation Logic."""
        result = self.tester.test_rule_7_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 7 implementation logic violations: {result['violations']}")
    
    def test_rule_8_implementation_logic(self):
        """Test Rule 8: Be Honest About AI Decisions - Implementation Logic."""
        result = self.tester.test_rule_8_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 8 implementation logic violations: {result['violations']}")
    
    def test_rule_12_implementation_logic(self):
        """Test Rule 12: Test Everything - Implementation Logic."""
        result = self.tester.test_rule_12_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 12 implementation logic violations: {result['violations']}")
    
    def test_rule_17_implementation_logic(self):
        """Test Rule 17: Keep Different Parts Separate - Implementation Logic."""
        result = self.tester.test_rule_17_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 17 implementation logic violations: {result['violations']}")
    
    def test_rule_18_implementation_logic(self):
        """Test Rule 18: Be Fair to Everyone - Implementation Logic."""
        result = self.tester.test_rule_18_implementation_logic()
        self.assertTrue(result['compliant'], f"Rule 18 implementation logic violations: {result['violations']}")


def main():
    """Main function to run implementation logic tests."""
    tester = RuleImplementationLogicTester()
    results = tester.run_all_implementation_logic_tests()
    
    # Save results
    output_file = Path(__file__).parent / "rule_implementation_logic_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    return results


if __name__ == '__main__':
    main()
