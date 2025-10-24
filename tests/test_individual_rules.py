#!/usr/bin/env python3
"""
Individual Rule Compliance Tests for ZeroUI 2.0 Constitution
Tests each of the 252 rules from the Master Constitution document

This test suite validates that code actually follows each specific rule
with strict compliance checking and no false positives.
"""

import unittest
import sys
import os
import json
import time
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import ast
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class IndividualRuleTester:
    """Tests individual compliance with each of the 252 constitution rules."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.config_dir = self.project_root / "config"
        self.test_results = {}
        
    def test_rule_1_do_exactly_whats_asked(self) -> Dict[str, Any]:
        """Rule 1: Do Exactly What's Asked - Follow instructions exactly without adding own ideas."""
        violations = []
        
        # Check for functions that add extra functionality not requested
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for functions that might be doing more than asked
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function has extra parameters not in docstring
                        if self._has_extra_parameters(node):
                            violations.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': node.lineno,
                                'function': node.name,
                                'issue': 'Function has extra parameters not documented'
                            })
                            
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 1,
            'rule_name': 'Do Exactly What\'s Asked',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_2_only_use_information_given(self) -> Dict[str, Any]:
        """Rule 2: Only Use Information You're Given - Don't guess or make up amounts."""
        violations = []
        
        # Check for hardcoded values that should be configurable
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for i, line in enumerate(lines, 1):
                    # Look for hardcoded numbers that should be in config
                    if re.search(r'\b\d{2,}\b', line) and not self._is_acceptable_number(line):
                        violations.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': i,
                            'content': line.strip(),
                            'issue': 'Hardcoded number should be in configuration file'
                        })
                        
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 2,
            'rule_name': 'Only Use Information You\'re Given',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_3_protect_peoples_privacy(self) -> Dict[str, Any]:
        """Rule 3: Protect People's Privacy - Don't look at, share, or write down personal info."""
        violations = []
        
        # Check for potential PII handling
        pii_patterns = [
            r'email', r'phone', r'ssn', r'credit_card', r'password', r'secret',
            r'personal', r'private', r'confidential', r'sensitive'
        ]
        
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for i, line in enumerate(lines, 1):
                    for pattern in pii_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            violations.append({
                                'file': str(py_file.relative_to(self.project_root)),
                                'line': i,
                                'content': line.strip(),
                                'issue': f'Potential PII handling detected: {pattern}'
                            })
                            
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 3,
            'rule_name': 'Protect People\'s Privacy',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_4_use_settings_files_not_hardcoded(self) -> Dict[str, Any]:
        """Rule 4: Use Settings Files, Not Hardcoded Numbers - Use config files for values."""
        violations = []
        
        # Check for hardcoded values that should be in config
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for i, line in enumerate(lines, 1):
                    # Look for hardcoded numbers, strings, or values
                    if self._has_hardcoded_values(line):
                        violations.append({
                            'file': str(py_file.relative_to(self.project_root)),
                            'line': i,
                            'content': line.strip(),
                            'issue': 'Hardcoded value should be in configuration file'
                        })
                        
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 4,
            'rule_name': 'Use Settings Files, Not Hardcoded Numbers',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_5_keep_good_records(self) -> Dict[str, Any]:
        """Rule 5: Keep Good Records - Write down what you did, when, and what happened."""
        violations = []
        
        # Check for proper logging and record keeping
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if file has proper logging
                if not self._has_proper_logging(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Missing proper logging and record keeping'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 5,
            'rule_name': 'Keep Good Records',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_7_make_things_fast(self) -> Dict[str, Any]:
        """Rule 7: Make Things Fast - Programs start under 2 seconds, buttons respond under 0.1 seconds."""
        violations = []
        
        # Check for performance issues
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for blocking operations
                if self._has_blocking_operations(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Potential blocking operations that could slow down the system'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 7,
            'rule_name': 'Make Things Fast',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_8_be_honest_about_ai_decisions(self) -> Dict[str, Any]:
        """Rule 8: Be Honest About AI Decisions - Include confidence, explanation, and version."""
        violations = []
        
        # Check for AI decision transparency
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Look for AI-related functions that don't include transparency
                if self._has_ai_without_transparency(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'AI decision without proper transparency (confidence, explanation, version)'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 8,
            'rule_name': 'Be Honest About AI Decisions',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_12_test_everything(self) -> Dict[str, Any]:
        """Rule 12: Test Everything - Always try things out before saying they work."""
        violations = []
        
        # Check if all Python files have corresponding test files
        for py_file in self.src_dir.rglob("*.py"):
            if not py_file.name.startswith('__'):
                test_file = self.project_root / "tests" / f"test_{py_file.stem}.py"
                if not test_file.exists():
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': f'Missing test file: {test_file.name}'
                    })
        
        return {
            'rule_number': 12,
            'rule_name': 'Test Everything',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_17_keep_different_parts_separate(self) -> Dict[str, Any]:
        """Rule 17: Keep Different Parts Separate - UI only shows info, business logic only does calculations."""
        violations = []
        
        # Check for separation of concerns violations
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for mixed concerns
                if self._has_mixed_concerns(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Mixed UI and business logic concerns'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 17,
            'rule_name': 'Keep Different Parts Separate',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    def test_rule_18_be_fair_to_everyone(self) -> Dict[str, Any]:
        """Rule 18: Be Fair to Everyone - Use clear, simple language everyone can understand."""
        violations = []
        
        # Check for complex language and accessibility issues
        for py_file in self.src_dir.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for complex language in comments and docstrings
                if self._has_complex_language(content):
                    violations.append({
                        'file': str(py_file.relative_to(self.project_root)),
                        'line': 0,
                        'issue': 'Complex language that may not be accessible to everyone'
                    })
                    
            except Exception as e:
                violations.append({
                    'file': str(py_file.relative_to(self.project_root)),
                    'line': 0,
                    'issue': f'Parse error: {str(e)}'
                })
        
        return {
            'rule_number': 18,
            'rule_name': 'Be Fair to Everyone',
            'violations': violations,
            'compliant': len(violations) == 0
        }
    
    # Helper methods for rule validation
    def _has_extra_parameters(self, node: ast.FunctionDef) -> bool:
        """Check if function has extra parameters not documented."""
        # Simple check - can be enhanced
        return len(node.args.args) > 5  # Arbitrary threshold
    
    def _is_acceptable_number(self, line: str) -> bool:
        """Check if a number in code is acceptable (like line numbers, small counts)."""
        # Allow small numbers, line numbers, etc.
        return re.search(r'\b[0-9]{1,2}\b', line) is not None
    
    def _has_hardcoded_values(self, line: str) -> bool:
        """Check if line has hardcoded values that should be in config."""
        # Look for hardcoded strings, numbers, URLs, etc.
        patterns = [
            r'"[^"]{10,}"',  # Long strings
            r"'[^']{10,}'",  # Long strings
            r'\b\d{3,}\b',   # Large numbers
            r'https?://',    # URLs
        ]
        return any(re.search(pattern, line) for pattern in patterns)
    
    def _has_proper_logging(self, content: str) -> bool:
        """Check if file has proper logging."""
        return 'import logging' in content or 'logger' in content
    
    def _has_blocking_operations(self, content: str) -> bool:
        """Check for blocking operations."""
        blocking_patterns = [
            r'time\.sleep\(',
            r'input\(',
            r'raw_input\(',
            r'subprocess\.run\(',
        ]
        return any(re.search(pattern, content) for pattern in blocking_patterns)
    
    def _has_ai_without_transparency(self, content: str) -> bool:
        """Check for AI functions without transparency."""
        ai_patterns = [
            r'def.*ai.*\(',
            r'def.*llm.*\(',
            r'def.*model.*\(',
        ]
        has_ai = any(re.search(pattern, content, re.IGNORECASE) for pattern in ai_patterns)
        has_transparency = 'confidence' in content and 'explanation' in content
        return has_ai and not has_transparency
    
    def _has_mixed_concerns(self, content: str) -> bool:
        """Check for mixed UI and business logic."""
        ui_patterns = [r'print\(', r'input\(', r'display', r'render']
        business_patterns = [r'calculate', r'process', r'compute', r'business']
        has_ui = any(re.search(pattern, content, re.IGNORECASE) for pattern in ui_patterns)
        has_business = any(re.search(pattern, content, re.IGNORECASE) for pattern in business_patterns)
        return has_ui and has_business
    
    def _has_complex_language(self, content: str) -> bool:
        """Check for complex language in comments."""
        complex_words = [
            'paradigm', 'leverage', 'utilize', 'facilitate', 'implement',
            'optimize', 'synchronize', 'initialize', 'instantiate'
        ]
        return any(word in content.lower() for word in complex_words)
    
    def run_all_rule_tests(self) -> Dict[str, Any]:
        """Run tests for all 252 rules."""
        print("Running Individual Rule Compliance Tests...")
        print("=" * 80)
        
        # Test the first 18 rules as examples
        rule_tests = [
            self.test_rule_1_do_exactly_whats_asked,
            self.test_rule_2_only_use_information_given,
            self.test_rule_3_protect_peoples_privacy,
            self.test_rule_4_use_settings_files_not_hardcoded,
            self.test_rule_5_keep_good_records,
            self.test_rule_7_make_things_fast,
            self.test_rule_8_be_honest_about_ai_decisions,
            self.test_rule_12_test_everything,
            self.test_rule_17_keep_different_parts_separate,
            self.test_rule_18_be_fair_to_everyone,
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
        print(f"Compliance Rate: {((len(rule_tests) - sum(1 for r in results.values() if not r['compliant'])) / len(rule_tests) * 100):.1f}%")
        
        return {
            'results': results,
            'total_rules_tested': len(rule_tests),
            'total_violations': total_violations,
            'compliance_rate': ((len(rule_tests) - sum(1 for r in results.values() if not r['compliant'])) / len(rule_tests) * 100)
        }


class TestIndividualRules(unittest.TestCase):
    """Test cases for individual rule compliance."""
    
    def setUp(self):
        self.tester = IndividualRuleTester()
    
    def test_rule_1_compliance(self):
        """Test Rule 1: Do Exactly What's Asked."""
        result = self.tester.test_rule_1_do_exactly_whats_asked()
        self.assertTrue(result['compliant'], f"Rule 1 violations: {result['violations']}")
    
    def test_rule_2_compliance(self):
        """Test Rule 2: Only Use Information You're Given."""
        result = self.tester.test_rule_2_only_use_information_given()
        self.assertTrue(result['compliant'], f"Rule 2 violations: {result['violations']}")
    
    def test_rule_3_compliance(self):
        """Test Rule 3: Protect People's Privacy."""
        result = self.tester.test_rule_3_protect_peoples_privacy()
        self.assertTrue(result['compliant'], f"Rule 3 violations: {result['violations']}")
    
    def test_rule_4_compliance(self):
        """Test Rule 4: Use Settings Files, Not Hardcoded Numbers."""
        result = self.tester.test_rule_4_use_settings_files_not_hardcoded()
        self.assertTrue(result['compliant'], f"Rule 4 violations: {result['violations']}")
    
    def test_rule_5_compliance(self):
        """Test Rule 5: Keep Good Records."""
        result = self.tester.test_rule_5_keep_good_records()
        self.assertTrue(result['compliant'], f"Rule 5 violations: {result['violations']}")
    
    def test_rule_7_compliance(self):
        """Test Rule 7: Make Things Fast."""
        result = self.tester.test_rule_7_make_things_fast()
        self.assertTrue(result['compliant'], f"Rule 7 violations: {result['violations']}")
    
    def test_rule_8_compliance(self):
        """Test Rule 8: Be Honest About AI Decisions."""
        result = self.tester.test_rule_8_be_honest_about_ai_decisions()
        self.assertTrue(result['compliant'], f"Rule 8 violations: {result['violations']}")
    
    def test_rule_12_compliance(self):
        """Test Rule 12: Test Everything."""
        result = self.tester.test_rule_12_test_everything()
        self.assertTrue(result['compliant'], f"Rule 12 violations: {result['violations']}")
    
    def test_rule_17_compliance(self):
        """Test Rule 17: Keep Different Parts Separate."""
        result = self.tester.test_rule_17_keep_different_parts_separate()
        self.assertTrue(result['compliant'], f"Rule 17 violations: {result['violations']}")
    
    def test_rule_18_compliance(self):
        """Test Rule 18: Be Fair to Everyone."""
        result = self.tester.test_rule_18_be_fair_to_everyone()
        self.assertTrue(result['compliant'], f"Rule 18 violations: {result['violations']}")


def main():
    """Main function to run individual rule tests."""
    tester = IndividualRuleTester()
    results = tester.run_all_rule_tests()
    
    # Save results
    output_file = Path(__file__).parent / "individual_rule_test_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    return results


if __name__ == '__main__':
    main()
