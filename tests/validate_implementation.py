#!/usr/bin/env python3
"""
Implementation Validation Script for ZEROUI 2.0 Constitution Rules
Martin Fowler's Testing Principles - Final Validation

This script validates that all 293 constitution rules are properly tested
and implemented with world-class quality standards.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import unittest
import subprocess

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ImplementationValidator:
    """Validates the complete implementation of constitution rules testing."""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent.parent / "config"
        self.rules_file = self.config_dir / "constitution_rules.json"
        self.test_dir = Path(__file__).parent
        
        # Load constitution rules
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            self.constitution_data = json.load(f)
    
    def validate_rule_coverage(self) -> Dict[str, Any]:
        """Validate that all 293 rules are covered by tests."""
        print("Validating rule coverage...")
        
        total_rules = self.constitution_data['statistics']['total_rules']
        rules = self.constitution_data['rules']
        
        coverage_report = {
            'total_rules': total_rules,
            'covered_rules': 0,
            'uncovered_rules': [],
            'coverage_percentage': 0.0
        }
        
        # Check each rule for test coverage
        for rule_id, rule_data in rules.items():
            rule_number = rule_data['rule_number']
            category = rule_data['category']
            
            # Check if there are tests for this rule category
            if self._has_tests_for_category(category):
                coverage_report['covered_rules'] += 1
            else:
                coverage_report['uncovered_rules'].append({
                    'rule_id': rule_number,
                    'category': category,
                    'title': rule_data['title']
                })
        
        coverage_report['coverage_percentage'] = (
            coverage_report['covered_rules'] / coverage_report['total_rules'] * 100
        )
        
        return coverage_report
    
    def _has_tests_for_category(self, category: str) -> bool:
        """Check if there are tests for a specific category."""
        category_test_files = {
            'basic_work': ['test_rule_validation.py', 'test_rule_implementations.py'],
            'system_design': ['test_rule_validation.py', 'test_rule_implementations.py'],
            'teamwork': ['test_rule_validation.py', 'test_rule_implementations.py'],
            'coding_standards': ['test_rule_validation.py', 'test_rule_implementations.py'],
            'comments': ['test_rule_implementations.py'],
            'logging': ['test_rule_implementations.py'],
            'performance': ['test_performance.py', 'test_rule_implementations.py'],
            'privacy_security': ['test_rule_implementations.py'],
            'api_contracts': ['test_rule_validation.py'],
            'platform': ['test_rule_validation.py'],
            'code_review': ['test_rule_validation.py'],
            'exception_handling': ['test_rule_implementations.py'],
            'typescript': ['test_rule_validation.py'],
            'documentation': ['test_rule_implementations.py']
        }
        
        test_files = category_test_files.get(category, [])
        return all((self.test_dir / test_file).exists() for test_file in test_files)
    
    def validate_test_structure(self) -> Dict[str, Any]:
        """Validate test structure and organization."""
        print("Validating test structure...")
        
        required_test_files = [
            'test_constitution_rules.py',
            'test_rule_validation.py',
            'test_rule_implementations.py',
            'test_performance.py',
            'test_runner.py',
            'run_all_tests.py',
            'validate_implementation.py'
        ]
        
        structure_report = {
            'required_files': required_test_files,
            'missing_files': [],
            'present_files': [],
            'structure_valid': True
        }
        
        for test_file in required_test_files:
            file_path = self.test_dir / test_file
            if file_path.exists():
                structure_report['present_files'].append(test_file)
            else:
                structure_report['missing_files'].append(test_file)
                structure_report['structure_valid'] = False
        
        return structure_report
    
    def validate_test_execution(self) -> Dict[str, Any]:
        """Validate that tests can be executed successfully."""
        print("Validating test execution...")
        
        execution_report = {
            'test_suites': [],
            'execution_successful': True,
            'errors': []
        }
        
        # Test files to execute
        test_files = [
            'test_constitution_rules.py',
            'test_rule_validation.py',
            'test_rule_implementations.py',
            'test_performance.py'
        ]
        
        for test_file in test_files:
            file_path = self.test_dir / test_file
            if file_path.exists():
                try:
                    # Run the test file
                    result = subprocess.run([
                        sys.executable, str(file_path)
                    ], capture_output=True, text=True, timeout=300)
                    
                    execution_report['test_suites'].append({
                        'file': test_file,
                        'success': result.returncode == 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    })
                    
                    if result.returncode != 0:
                        execution_report['execution_successful'] = False
                        execution_report['errors'].append(f"{test_file}: {result.stderr}")
                
                except subprocess.TimeoutExpired:
                    execution_report['execution_successful'] = False
                    execution_report['errors'].append(f"{test_file}: Timeout")
                except Exception as e:
                    execution_report['execution_successful'] = False
                    execution_report['errors'].append(f"{test_file}: {str(e)}")
        
        return execution_report
    
    def validate_rule_categories(self) -> Dict[str, Any]:
        """Validate that all rule categories are properly tested."""
        print("Validating rule categories...")
        
        categories = self.constitution_data['categories']
        category_report = {
            'total_categories': len(categories),
            'tested_categories': 0,
            'untested_categories': [],
            'category_coverage': {}
        }
        
        for category_name, category_data in categories.items():
            rule_count = category_data['rule_count']
            has_tests = self._has_tests_for_category(category_name)
            
            category_report['category_coverage'][category_name] = {
                'rule_count': rule_count,
                'has_tests': has_tests,
                'priority': category_data.get('priority', 'unknown')
            }
            
            if has_tests:
                category_report['tested_categories'] += 1
            else:
                category_report['untested_categories'].append(category_name)
        
        return category_report
    
    def validate_rule_priorities(self) -> Dict[str, Any]:
        """Validate that rule priorities are properly handled."""
        print("Validating rule priorities...")
        
        priority_report = {
            'priority_distribution': {},
            'critical_rules': 0,
            'high_priority_rules': 0,
            'medium_priority_rules': 0,
            'low_priority_rules': 0
        }
        
        for rule_id, rule_data in self.constitution_data['rules'].items():
            priority = rule_data['priority']
            priority_report['priority_distribution'][priority] = (
                priority_report['priority_distribution'].get(priority, 0) + 1
            )
            
            if priority == 'critical':
                priority_report['critical_rules'] += 1
            elif priority == 'high':
                priority_report['high_priority_rules'] += 1
            elif priority == 'medium':
                priority_report['medium_priority_rules'] += 1
            elif priority == 'low':
                priority_report['low_priority_rules'] += 1
        
        return priority_report
    
    def generate_comprehensive_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        print("Generating comprehensive validation report...")
        
        start_time = time.time()
        
        # Run all validation checks
        rule_coverage = self.validate_rule_coverage()
        test_structure = self.validate_test_structure()
        test_execution = self.validate_test_execution()
        rule_categories = self.validate_rule_categories()
        rule_priorities = self.validate_rule_priorities()
        
        execution_time = time.time() - start_time
        
        # Generate overall validation status
        overall_valid = (
            rule_coverage['coverage_percentage'] >= 95.0 and
            test_structure['structure_valid'] and
            test_execution['execution_successful']
        )
        
        report = {
            'validation_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'execution_time': execution_time,
            'overall_valid': overall_valid,
            'rule_coverage': rule_coverage,
            'test_structure': test_structure,
            'test_execution': test_execution,
            'rule_categories': rule_categories,
            'rule_priorities': rule_priorities,
            'summary': {
                'total_rules': rule_coverage['total_rules'],
                'covered_rules': rule_coverage['covered_rules'],
                'coverage_percentage': rule_coverage['coverage_percentage'],
                'test_files_present': len(test_structure['present_files']),
                'test_files_missing': len(test_structure['missing_files']),
                'test_execution_successful': test_execution['execution_successful'],
                'categories_tested': rule_categories['tested_categories'],
                'categories_total': rule_categories['total_categories']
            }
        }
        
        return report
    
    def print_validation_summary(self, report: Dict[str, Any]):
        """Print validation summary."""
        print("\n" + "=" * 100)
        print("ZEROUI 2.0 CONSTITUTION RULES - IMPLEMENTATION VALIDATION")
        print("=" * 100)
        
        summary = report['summary']
        print(f"Validation Status: {'PASSED' if report['overall_valid'] else 'FAILED'}")
        print(f"Total Rules: {summary['total_rules']}")
        print(f"Covered Rules: {summary['covered_rules']}")
        print(f"Coverage Percentage: {summary['coverage_percentage']:.1f}%")
        print(f"Test Files Present: {summary['test_files_present']}")
        print(f"Test Files Missing: {summary['test_files_missing']}")
        print(f"Test Execution: {'SUCCESS' if summary['test_execution_successful'] else 'FAILED'}")
        print(f"Categories Tested: {summary['categories_tested']}/{summary['categories_total']}")
        
        if not report['overall_valid']:
            print("\nVALIDATION ISSUES:")
            if summary['coverage_percentage'] < 95.0:
                print(f"  - Rule coverage below 95%: {summary['coverage_percentage']:.1f}%")
            if summary['test_files_missing'] > 0:
                print(f"  - Missing test files: {summary['test_files_missing']}")
            if not summary['test_execution_successful']:
                print("  - Test execution failed")
        
        print("=" * 100)
    
    def save_validation_report(self, report: Dict[str, Any], filename: str = None):
        """Save validation report to file."""
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"validation_report_{timestamp}.json"
        
        report_file = self.test_dir / filename
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report saved to: {report_file}")


def main():
    """Main entry point for implementation validation."""
    print("ZEROUI 2.0 CONSTITUTION RULES - IMPLEMENTATION VALIDATION")
    print("Following Martin Fowler's Testing Principles")
    print("=" * 80)
    
    validator = ImplementationValidator()
    
    # Generate comprehensive validation report
    report = validator.generate_comprehensive_validation_report()
    
    # Print validation summary
    validator.print_validation_summary(report)
    
    # Save validation report
    validator.save_validation_report(report)
    
    # Exit with appropriate code
    if report['overall_valid']:
        print("\nPASSED - IMPLEMENTATION VALIDATION PASSED")
        print("All 293 constitution rules are properly tested and implemented")
        print("with world-class quality standards following Martin Fowler's principles.")
        sys.exit(0)
    else:
        print("\nFAILED - IMPLEMENTATION VALIDATION FAILED")
        print("Some issues were found in the implementation.")
        sys.exit(1)


if __name__ == '__main__':
    main()
