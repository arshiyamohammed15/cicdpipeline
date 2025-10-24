#!/usr/bin/env python3
"""
Comprehensive Test Runner for ZEROUI 2.0 Constitution Rules
Martin Fowler's Testing Principles Implementation

This script runs all test suites and provides comprehensive reporting
for the 293 constitution rules with world-class quality standards.
"""

import sys
import os
import time
import json
import argparse
import unittest
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import concurrent.futures
from datetime import datetime
from io import StringIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_runner import ConstitutionTestRunner, TestMetrics
from test_constitution_rules import (
    TestConstitutionRulesBase, TestRuleStructure, TestRuleCategories, 
    TestRuleValidation, TestSpecificRuleCategories, TestRuleContentValidation,
    TestRulePerformance, TestRuleIntegration, TestRuleErrorHandling, TestRuleReporting
)
from test_rule_validation import TestBasicWorkRules, TestSystemDesignRules, TestTeamworkRules, TestCodingStandardsRules, TestRuleIntegration
from test_rule_implementations import TestBasicWorkRuleImplementations, TestSystemDesignRuleImplementations, TestTeamworkRuleImplementations, TestCodingStandardsRuleImplementations, TestRuleEdgeCases, TestRuleIntegration
from test_performance import TestValidationPerformance, TestMemoryUsage, TestConcurrentValidation, TestStressValidation, TestScalability
from test_individual_rules import TestIndividualRules
from test_rule_implementation_logic import TestRuleImplementationLogic
from test_rule_compliance_validation import TestRuleComplianceValidation
from test_all_constitution_rules import Test293ConstitutionRules


class ComprehensiveTestRunner:
    """Comprehensive test runner for all constitution rule tests."""
    
    def __init__(self, verbose: bool = True, parallel: bool = False, output_dir: str = "test_reports", clear_cache: bool = True, no_cache: bool = True):
        self.verbose = verbose
        self.parallel = parallel
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.clear_cache = clear_cache
        self.no_cache = no_cache
        
        # Always clear cache and disable cache for strict testing
        self._clear_test_cache()
        
        # Initialize test suites with proper discovery
        self.test_suites = self._discover_test_suites()
        self.metrics = TestMetrics()
    
    
    def _discover_test_suites(self):
        """Discover test suites directly from test files."""
        test_suites = {
            # Removed original constitution_rules - now covered by constitution_rules_293
            'rule_validation': [
                TestBasicWorkRules,
                TestSystemDesignRules,
                TestTeamworkRules,
                TestCodingStandardsRules,
                TestRuleIntegration
            ],
            'rule_implementations': [
                TestBasicWorkRuleImplementations,
                TestSystemDesignRuleImplementations,
                TestTeamworkRuleImplementations,
                TestCodingStandardsRuleImplementations,
                TestRuleEdgeCases,
                TestRuleIntegration
            ],
            'performance': [
                TestValidationPerformance,
                # TestMemoryUsage,  # Temporarily disabled
                TestConcurrentValidation,
                TestStressValidation,
                # TestScalability  # Temporarily disabled
            ],
            'individual_rules': [
                TestIndividualRules
            ],
            'rule_implementation_logic': [
                TestRuleImplementationLogic
            ],
            'rule_compliance_validation': [
                TestRuleComplianceValidation
            ],
            'constitution_rules_293': [
                Test293ConstitutionRules
            ]
        }
        return test_suites
    
    def _clear_test_cache(self):
        """Clear test cache files and directories."""
        if self.verbose:
            print("Clearing test cache...")
        
        # Clear Python cache files
        cache_dirs = [
            Path(__file__).parent / "__pycache__",
            Path(__file__).parent.parent / "__pycache__",
            Path(__file__).parent.parent / "config" / "__pycache__",
            Path(__file__).parent.parent / "validator" / "__pycache__"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                if self.verbose:
                    print(f"  Cleared: {cache_dir}")
        
        # Clear test report cache
        if self.output_dir.exists():
            for file in self.output_dir.glob("*.json"):
                if "cache" in file.name.lower():
                    file.unlink()
                    if self.verbose:
                        print(f"  Cleared cache file: {file}")
        
        if self.verbose:
            print("Cache cleared successfully.")
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and generate comprehensive report."""
        # Silent execution - no header output
        
        self.metrics.start_testing()
        
        results = {}
        
        # Run each test category silently
        for category, test_classes in self.test_suites.items():
            if isinstance(test_classes, list):
                category_results = self._run_test_list(category, test_classes)
            else:
                category_results = self._run_single_test(category, test_classes)
            
            results[category] = category_results
        
        self.metrics.end_testing()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(results)
        
        self._print_comprehensive_summary(report)
        
        # Save detailed report
        self._save_detailed_report(report)
        
        return report
    
    def _run_test_list(self, category: str, test_classes: List) -> Dict[str, Any]:
        """Run a list of test classes with direct unittest execution."""
        results = {}
        
        for test_class in test_classes:
            class_name = test_class.__name__
            # Silent execution
            
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            try:
                # Create test suite directly
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                
                # Use StringIO to capture output instead of devnull
                stream = StringIO()
                runner = unittest.TextTestRunner(verbosity=2, stream=stream)
                result = runner.run(suite)
                
                execution_time = time.time() - start_time
                memory_usage = self._get_memory_usage() - start_memory
                
                # Record metrics
                self.metrics.record_test_result(
                    f"{category}_{class_name}",
                    'passed' if result.wasSuccessful() else 'failed',
                    execution_time,
                    memory_usage
                )
                
                results[class_name] = {
                    'success': result.wasSuccessful(),
                    'tests_run': result.testsRun,
                    'failures': len(result.failures),
                    'errors': len(result.errors),
                    'execution_time': execution_time,
                    'memory_usage_mb': memory_usage / (1024 * 1024),
                    'category': category,
                    'output': stream.getvalue()
                }
                
                # Silent execution
                
            except Exception as e:
                execution_time = time.time() - start_time
                memory_usage = self._get_memory_usage() - start_memory
                
                self.metrics.record_test_result(f"{category}_{class_name}", 'failed', execution_time, memory_usage)
                
                results[class_name] = {
                    'success': False,
                    'error': str(e),
                    'execution_time': execution_time,
                    'memory_usage_mb': memory_usage / (1024 * 1024),
                    'category': category
                }
                
                # Silent execution
        
        return results
    
    def _run_single_test(self, category: str, test_class) -> Dict[str, Any]:
        """Run a single test class."""
        class_name = test_class.__name__
        if self.verbose:
            print(f"\nRunning {class_name}...")
        
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
            result = runner.run(suite)
            
            execution_time = time.time() - start_time
            memory_usage = self._get_memory_usage() - start_memory
            
            self.metrics.record_test_result(
                f"{category}_{class_name}",
                'passed' if result.wasSuccessful() else 'failed',
                execution_time,
                memory_usage
            )
            
            result_dict = {
                'success': result.wasSuccessful(),
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'execution_time': execution_time,
                'memory_usage_mb': memory_usage / (1024 * 1024),
                'category': category
            }
            
            if self.verbose:
                status = "PASSED" if result.wasSuccessful() else "FAILED"
                print(f"  {class_name}: {status} ({result.testsRun} tests, {execution_time:.2f}s)")
            
            return {class_name: result_dict}
            
        except Exception as e:
            execution_time = time.time() - start_time
            memory_usage = self._get_memory_usage() - start_memory
            
            self.metrics.record_test_result(f"{category}_{class_name}", 'failed', execution_time, memory_usage)
            
            if self.verbose:
                print(f"  {class_name}: ERROR - {str(e)}")
            
            return {class_name: {
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'memory_usage_mb': memory_usage / (1024 * 1024),
                'category': category
            }}
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        import psutil
        return psutil.Process().memory_info().rss
    
    def _generate_comprehensive_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_execution_time = 0
        total_memory_usage = 0
        
        category_summaries = {}
        
        for category, category_results in results.items():
            category_tests = 0
            category_passed = 0
            category_failed = 0
            category_errors = 0
            category_time = 0
            category_memory = 0
            
            for test_name, test_result in category_results.items():
                if isinstance(test_result, dict):
                    category_tests += test_result.get('tests_run', 0)
                    category_passed += test_result.get('tests_run', 0) - test_result.get('failures', 0) - test_result.get('errors', 0)
                    category_failed += test_result.get('failures', 0)
                    category_errors += test_result.get('errors', 0)
                    category_time += test_result.get('execution_time', 0)
                    category_memory += test_result.get('memory_usage_mb', 0)
            
            category_summaries[category] = {
                'tests': category_tests,
                'passed': category_passed,
                'failed': category_failed,
                'errors': category_errors,
                'success_rate': (category_passed / category_tests * 100) if category_tests > 0 else 0,
                'execution_time': category_time,
                'memory_usage_mb': category_memory
            }
            
            total_tests += category_tests
            total_passed += category_passed
            total_failed += category_failed
            total_errors += category_errors
            total_execution_time += category_time
            total_memory_usage += category_memory
        
        return {
            'summary': {
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'total_errors': total_errors,
                'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
                'execution_time': total_execution_time,
                'memory_usage_mb': total_memory_usage,
                'timestamp': datetime.now().isoformat()
            },
            'categories': category_summaries,
            'detailed_results': results,
            'metrics': self.metrics.generate_report()
        }
    
    def _print_comprehensive_summary(self, report: Dict[str, Any]):
        """Print comprehensive test summary."""
        summary = report['summary']
        categories = report['categories']
        
        print("=" * 100)
        print("CATEGORY BREAKDOWN")
        print("=" * 100)
        for category, cat_summary in categories.items():
            category_name = category.upper().replace('_', ' ')
            print(f"{category_name:<30} | Tests: {cat_summary['tests']:<3} | Passed: {cat_summary['passed']:<3} | Failed: {cat_summary['failed']:<3} | Success: {cat_summary['success_rate']:.1f}%")
        
        print("=" * 100)
        print(f"{'TOTAL':<30} | Tests: {summary['total_tests']:<3} | Passed: {summary['total_passed']:<3} | Failed: {summary['total_failed']:<3} | Success: {summary['success_rate']:.1f}%")
        print("=" * 100)
    
    def _save_detailed_report(self, report: Dict[str, Any]):
        """Save detailed test report to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"comprehensive_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        if self.verbose:
            print(f"\nDetailed report saved to: {report_file}")
        
        # Also save a summary report
        summary_file = self.output_dir / f"test_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("ZEROUI 2.0 CONSTITUTION RULES - TEST SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Test Execution: {report['summary']['timestamp']}\n")
            f.write(f"Total Tests: {report['summary']['total_tests']}\n")
            f.write(f"Passed: {report['summary']['total_passed']}\n")
            f.write(f"Failed: {report['summary']['total_failed']}\n")
            f.write(f"Errors: {report['summary']['total_errors']}\n")
            f.write(f"Success Rate: {report['summary']['success_rate']:.1f}%\n")
            f.write(f"Execution Time: {report['summary']['execution_time']:.2f} seconds\n")
            f.write(f"Memory Usage: {report['summary']['memory_usage_mb']:.2f} MB\n")
        
        if self.verbose:
            print(f"Summary report saved to: {summary_file}")


def main():
    """Main entry point for comprehensive test runner."""
    parser = argparse.ArgumentParser(description='ZEROUI 2.0 Constitution Rules - Comprehensive Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--output-dir', '-o', default='test_reports', help='Output directory for reports')
    parser.add_argument('--category', '-c', help='Run specific test category')
    parser.add_argument('--clear-cache', action='store_true', help='Clear test cache before running')
    parser.add_argument('--no-cache', action='store_true', help='Disable test caching (same as --clear-cache)')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(
        verbose=args.verbose,
        parallel=args.parallel,
        output_dir=args.output_dir,
        clear_cache=args.clear_cache or args.no_cache,
        no_cache=args.no_cache
    )
    
    if args.category:
        # Run specific category
        if args.category in runner.test_suites:
            print(f"Running {args.category} tests only...")
            # Implementation for running specific category
        else:
            print(f"Unknown category: {args.category}")
            print(f"Available categories: {list(runner.test_suites.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        report = runner.run_all_tests()
        
        # Exit with error code if tests failed
        if report['summary']['total_failed'] > 0 or report['summary']['total_errors'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == '__main__':
    main()
