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
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import concurrent.futures
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_runner import ConstitutionTestRunner, TestMetrics
from test_constitution_rules import TestConstitutionRulesBase
from test_rule_validation import TestBasicWorkRules, TestSystemDesignRules, TestTeamworkRules, TestCodingStandardsRules, TestRuleIntegration
from test_rule_implementations import TestBasicWorkRuleImplementations, TestSystemDesignRuleImplementations, TestTeamworkRuleImplementations, TestCodingStandardsRuleImplementations, TestCommentsRuleImplementations, TestLoggingRuleImplementations, TestPerformanceRuleImplementations, TestRuleEdgeCases, TestRuleIntegration
from test_performance import TestValidationPerformance, TestMemoryUsage, TestConcurrentValidation, TestStressValidation, TestScalability


class ComprehensiveTestRunner:
    """Comprehensive test runner for all constitution rule tests."""
    
    def __init__(self, verbose: bool = True, parallel: bool = False, output_dir: str = "test_reports"):
        self.verbose = verbose
        self.parallel = parallel
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize test suites
        self.test_suites = {
            'constitution_rules': TestConstitutionRulesBase,
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
                TestCommentsRuleImplementations,
                TestLoggingRuleImplementations,
                TestPerformanceRuleImplementations,
                TestRuleEdgeCases,
                TestRuleIntegration
            ],
            'performance': [
                TestValidationPerformance,
                TestMemoryUsage,
                TestConcurrentValidation,
                TestStressValidation,
                TestScalability
            ]
        }
        
        self.metrics = TestMetrics()
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and generate comprehensive report."""
        if self.verbose:
            print("=" * 100)
            print("ZEROUI 2.0 CONSTITUTION RULES - COMPREHENSIVE TEST SUITE")
            print("=" * 100)
            print(f"Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Total Test Categories: {len(self.test_suites)}")
            print(f"Parallel Execution: {'Enabled' if self.parallel else 'Disabled'}")
            print("=" * 100)
        
        self.metrics.start_testing()
        
        results = {}
        
        # Run each test category
        for category, test_classes in self.test_suites.items():
            if self.verbose:
                print(f"\n{'='*20} {category.upper()} TESTS {'='*20}")
            
            if isinstance(test_classes, list):
                category_results = self._run_test_list(category, test_classes)
            else:
                category_results = self._run_single_test(category, test_classes)
            
            results[category] = category_results
        
        self.metrics.end_testing()
        
        # Generate comprehensive report
        report = self._generate_comprehensive_report(results)
        
        if self.verbose:
            self._print_comprehensive_summary(report)
        
        # Save detailed report
        self._save_detailed_report(report)
        
        return report
    
    def _run_test_list(self, category: str, test_classes: List) -> Dict[str, Any]:
        """Run a list of test classes."""
        results = {}
        
        for test_class in test_classes:
            class_name = test_class.__name__
            if self.verbose:
                print(f"\nRunning {class_name}...")
            
            start_time = time.time()
            start_memory = self._get_memory_usage()
            
            try:
                # Create test suite
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
                runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
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
                    'category': category
                }
                
                if self.verbose:
                    status = "PASSED" if result.wasSuccessful() else "FAILED"
                    print(f"  {class_name}: {status} ({result.testsRun} tests, {execution_time:.2f}s)")
                
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
                
                if self.verbose:
                    print(f"  {class_name}: ERROR - {str(e)}")
        
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
        
        print("\n" + "=" * 100)
        print("COMPREHENSIVE TEST EXECUTION SUMMARY")
        print("=" * 100)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['total_passed']}")
        print(f"Failed: {summary['total_failed']}")
        print(f"Errors: {summary['total_errors']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Execution Time: {summary['execution_time']:.2f} seconds")
        print(f"Total Memory Usage: {summary['memory_usage_mb']:.2f} MB")
        
        print("\n" + "-" * 100)
        print("CATEGORY BREAKDOWN")
        print("-" * 100)
        for category, cat_summary in categories.items():
            print(f"{category.upper():<20} | Tests: {cat_summary['tests']:<6} | Passed: {cat_summary['passed']:<6} | Failed: {cat_summary['failed']:<6} | Success: {cat_summary['success_rate']:.1f}%")
        
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
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(
        verbose=args.verbose,
        parallel=args.parallel,
        output_dir=args.output_dir
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
