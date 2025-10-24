#!/usr/bin/env python3
"""
Table Format Test Runner for ZEROUI 2.0 Constitution Rules
Outputs all test results in a single, clean table format
"""

import sys
import os
import time
import json
import unittest
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from io import StringIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_constitution_rules import (
    TestRuleStructure, TestRuleCategories, TestRuleValidation, 
    TestSpecificRuleCategories, TestRuleContentValidation,
    TestRulePerformance, TestRuleIntegration, TestRuleErrorHandling, TestRuleReporting
)
from test_rule_validation import TestBasicWorkRules, TestSystemDesignRules, TestTeamworkRules, TestCodingStandardsRules, TestRuleIntegration
from test_rule_implementations import TestBasicWorkRuleImplementations, TestSystemDesignRuleImplementations, TestTeamworkRuleImplementations, TestCodingStandardsRuleImplementations, TestRuleEdgeCases, TestRuleIntegration
from test_performance import TestValidationPerformance, TestConcurrentValidation, TestStressValidation
from test_individual_rules import TestIndividualRules
from test_rule_implementation_logic import TestRuleImplementationLogic
from test_rule_compliance_validation import TestRuleComplianceValidation


class TableTestRunner:
    """Test runner that outputs everything in a clean table format."""
    
    def __init__(self):
        self.test_suites = {
            'CONSTITUTION RULES': [
                TestRuleStructure, TestRuleCategories, TestRuleValidation,
                TestSpecificRuleCategories, TestRuleContentValidation,
                TestRulePerformance, TestRuleIntegration, TestRuleErrorHandling, TestRuleReporting
            ],
            'RULE VALIDATION': [
                TestBasicWorkRules, TestSystemDesignRules, TestTeamworkRules,
                TestCodingStandardsRules, TestRuleIntegration
            ],
            'RULE IMPLEMENTATIONS': [
                TestBasicWorkRuleImplementations, TestSystemDesignRuleImplementations,
                TestTeamworkRuleImplementations, TestCodingStandardsRuleImplementations,
                TestRuleEdgeCases, TestRuleIntegration
            ],
            'PERFORMANCE': [
                TestValidationPerformance, TestConcurrentValidation, TestStressValidation
            ],
            'INDIVIDUAL RULES': [TestIndividualRules],
            'RULE IMPLEMENTATION LOGIC': [TestRuleImplementationLogic],
            'RULE COMPLIANCE VALIDATION': [TestRuleComplianceValidation]
        }
    
    def run_all_tests(self):
        """Run all tests and output results in table format."""
        print("=" * 100)
        print("ZEROUI 2.0 CONSTITUTION RULES - COMPREHENSIVE TEST SUITE")
        print("=" * 100)
        print(f"Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        all_results = {}
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        
        # Run all test suites
        for category, test_classes in self.test_suites.items():
            category_tests = 0
            category_passed = 0
            category_failed = 0
            category_errors = 0
            
            for test_class in test_classes:
                class_name = test_class.__name__
                
                try:
                    suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                    stream = StringIO()
                    runner = unittest.TextTestRunner(verbosity=0, stream=stream)
                    result = runner.run(suite)
                    
                    tests_run = result.testsRun
                    failures = len(result.failures)
                    errors = len(result.errors)
                    success = result.wasSuccessful()
                    
                    category_tests += tests_run
                    if success:
                        category_passed += tests_run
                    else:
                        category_failed += failures
                        category_errors += errors
                        category_passed += (tests_run - failures - errors)
                    
                    all_results[class_name] = {
                        'category': category,
                        'tests': tests_run,
                        'passed': tests_run - failures - errors,
                        'failed': failures,
                        'errors': errors,
                        'success': success
                    }
                    
                except Exception as e:
                    all_results[class_name] = {
                        'category': category,
                        'tests': 0,
                        'passed': 0,
                        'failed': 0,
                        'errors': 1,
                        'success': False
                    }
                    category_errors += 1
            
            total_tests += category_tests
            total_passed += category_passed
            total_failed += category_failed
            total_errors += category_errors
        
        # Print results in table format
        print("\n" + "=" * 100)
        print("CATEGORY BREAKDOWN")
        print("=" * 100)
        
        for category, test_classes in self.test_suites.items():
            category_tests = 0
            category_passed = 0
            category_failed = 0
            category_errors = 0
            
            for test_class in test_classes:
                class_name = test_class.__name__
                if class_name in all_results:
                    result = all_results[class_name]
                    category_tests += result['tests']
                    category_passed += result['passed']
                    category_failed += result['failed']
                    category_errors += result['errors']
            
            success_rate = (category_passed / category_tests * 100) if category_tests > 0 else 0
            print(f"{category:<30} | Tests: {category_tests:<3} | Passed: {category_passed:<3} | Failed: {category_failed:<3} | Success: {success_rate:.1f}%")
        
        print("=" * 100)
        total_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        print(f"{'TOTAL':<30} | Tests: {total_tests:<3} | Passed: {total_passed:<3} | Failed: {total_failed:<3} | Success: {total_success_rate:.1f}%")
        print("=" * 100)
        
        return {
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_errors': total_errors,
            'success_rate': total_success_rate,
            'results': all_results
        }


def main():
    """Main entry point."""
    runner = TableTestRunner()
    results = runner.run_all_tests()
    
    # Save results
    output_dir = Path("test_reports")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"table_test_report_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")


if __name__ == '__main__':
    main()
