#!/usr/bin/env python3
"""
Comprehensive Test Runner for ZEROUI 2.0 Constitution Rules
Following Martin Fowler's Testing Principles

This test runner provides systematic execution, reporting, and metrics
for all 293 constitution rules with world-class quality standards.
"""

import unittest
import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_constitution_rules import TestConstitutionRulesBase
from test_rule_validation import TestBasicWorkRules, TestSystemDesignRules, TestTeamworkRules, TestCodingStandardsRules, TestRuleIntegration


class TestMetrics:
    """Collect and analyze test execution metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.memory_usage = []
        self.cpu_usage = []
        self.test_results = []
    
    def start_testing(self):
        """Start test execution timing."""
        self.start_time = time.time()
        self.initial_memory = psutil.Process().memory_info().rss
    
    def end_testing(self):
        """End test execution timing."""
        self.end_time = time.time()
        self.final_memory = psutil.Process().memory_info().rss
    
    def record_test_result(self, test_name: str, result: str, execution_time: float, memory_usage: float):
        """Record individual test result."""
        self.test_results.append({
            'test_name': test_name,
            'result': result,
            'execution_time': execution_time,
            'memory_usage': memory_usage,
            'timestamp': time.time()
        })
        
        if result == 'passed':
            self.passed_tests += 1
        elif result == 'failed':
            self.failed_tests += 1
        elif result == 'skipped':
            self.skipped_tests += 1
        
        self.total_tests += 1
    
    def get_execution_time(self) -> float:
        """Get total execution time."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0
    
    def get_memory_usage(self) -> float:
        """Get peak memory usage in MB."""
        if hasattr(self, 'initial_memory') and hasattr(self, 'final_memory'):
            return (self.final_memory - self.initial_memory) / (1024 * 1024)
        return 0.0
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        return {
            'summary': {
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'skipped_tests': self.skipped_tests,
                'success_rate': (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
                'execution_time': self.get_execution_time(),
                'memory_usage_mb': self.get_memory_usage()
            },
            'test_results': self.test_results,
            'performance_metrics': {
                'average_test_time': sum(r['execution_time'] for r in self.test_results) / len(self.test_results) if self.test_results else 0,
                'slowest_test': max(self.test_results, key=lambda x: x['execution_time']) if self.test_results else None,
                'fastest_test': min(self.test_results, key=lambda x: x['execution_time']) if self.test_results else None
            }
        }


class ConstitutionTestRunner:
    """Main test runner for constitution rules."""
    
    def __init__(self, verbose: bool = True, parallel: bool = False):
        self.verbose = verbose
        self.parallel = parallel
        self.metrics = TestMetrics()
        self.test_suites = [
            TestConstitutionRulesBase,
            TestBasicWorkRules,
            TestSystemDesignRules,
            TestTeamworkRules,
            TestCodingStandardsRules,
            TestRuleIntegration
        ]
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites and return comprehensive results."""
        self.metrics.start_testing()
        
        if self.verbose:
            print("=" * 80)
            print("ZEROUI 2.0 CONSTITUTION RULES TEST SUITE")
            print("=" * 80)
            print(f"Starting test execution at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Test suites: {len(self.test_suites)}")
            print(f"Parallel execution: {'Enabled' if self.parallel else 'Disabled'}")
            print("=" * 80)
        
        if self.parallel:
            results = self._run_tests_parallel()
        else:
            results = self._run_tests_sequential()
        
        self.metrics.end_testing()
        
        if self.verbose:
            self._print_summary()
        
        return {
            'metrics': self.metrics.generate_report(),
            'results': results
        }
    
    def _run_tests_sequential(self) -> Dict[str, Any]:
        """Run tests sequentially."""
        results = {}
        
        for test_suite in self.test_suites:
            suite_name = test_suite.__name__
            if self.verbose:
                print(f"\nRunning {suite_name}...")
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                # Create test suite
                suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
                runner = unittest.TextTestRunner(verbosity=2 if self.verbose else 1, stream=open(os.devnull, 'w'))
                result = runner.run(suite)
                
                execution_time = time.time() - start_time
                memory_usage = (psutil.Process().memory_info().rss - start_memory) / (1024 * 1024)
                
                # Record metrics
                self.metrics.record_test_result(
                    suite_name,
                    'passed' if result.wasSuccessful() else 'failed',
                    execution_time,
                    memory_usage
                )
                
                results[suite_name] = {
                    'success': result.wasSuccessful(),
                    'tests_run': result.testsRun,
                    'failures': len(result.failures),
                    'errors': len(result.errors),
                    'execution_time': execution_time,
                    'memory_usage_mb': memory_usage
                }
                
                if self.verbose:
                    status = "PASSED" if result.wasSuccessful() else "FAILED"
                    print(f"  {suite_name}: {status} ({result.testsRun} tests, {execution_time:.2f}s)")
                
            except Exception as e:
                execution_time = time.time() - start_time
                memory_usage = (psutil.Process().memory_info().rss - start_memory) / (1024 * 1024)
                
                self.metrics.record_test_result(suite_name, 'failed', execution_time, memory_usage)
                
                results[suite_name] = {
                    'success': False,
                    'error': str(e),
                    'execution_time': execution_time,
                    'memory_usage_mb': memory_usage
                }
                
                if self.verbose:
                    print(f"  {suite_name}: ERROR - {str(e)}")
        
        return results
    
    def _run_tests_parallel(self) -> Dict[str, Any]:
        """Run tests in parallel using ThreadPoolExecutor."""
        results = {}
        
        def run_single_suite(test_suite):
            suite_name = test_suite.__name__
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            try:
                suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
                runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
                result = runner.run(suite)
                
                execution_time = time.time() - start_time
                memory_usage = (psutil.Process().memory_info().rss - start_memory) / (1024 * 1024)
                
                return {
                    'suite_name': suite_name,
                    'success': result.wasSuccessful(),
                    'tests_run': result.testsRun,
                    'failures': len(result.failures),
                    'errors': len(result.errors),
                    'execution_time': execution_time,
                    'memory_usage_mb': memory_usage
                }
            except Exception as e:
                execution_time = time.time() - start_time
                memory_usage = (psutil.Process().memory_info().rss - start_memory) / (1024 * 1024)
                
                return {
                    'suite_name': suite_name,
                    'success': False,
                    'error': str(e),
                    'execution_time': execution_time,
                    'memory_usage_mb': memory_usage
                }
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_suite = {executor.submit(run_single_suite, suite): suite for suite in self.test_suites}
            
            for future in as_completed(future_to_suite):
                suite = future_to_suite[future]
                try:
                    result = future.result()
                    suite_name = result['suite_name']
                    results[suite_name] = result
                    
                    # Record metrics
                    self.metrics.record_test_result(
                        suite_name,
                        'passed' if result['success'] else 'failed',
                        result['execution_time'],
                        result['memory_usage_mb']
                    )
                    
                    if self.verbose:
                        status = "PASSED" if result['success'] else "FAILED"
                        print(f"  {suite_name}: {status} ({result.get('tests_run', 0)} tests, {result['execution_time']:.2f}s)")
                
                except Exception as e:
                    suite_name = suite.__name__
                    results[suite_name] = {
                        'success': False,
                        'error': str(e),
                        'execution_time': 0,
                        'memory_usage_mb': 0
                    }
                    
                    if self.verbose:
                        print(f"  {suite_name}: ERROR - {str(e)}")
        
        return results
    
    def _print_summary(self):
        """Print test execution summary."""
        report = self.metrics.generate_report()
        summary = report['summary']
        
        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Skipped: {summary['skipped_tests']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Execution Time: {summary['execution_time']:.2f} seconds")
        print(f"Memory Usage: {summary['memory_usage_mb']:.2f} MB")
        
        if summary['failed_tests'] > 0:
            print("\nFAILED TESTS:")
            for result in self.metrics.test_results:
                if result['result'] == 'failed':
                    print(f"  - {result['test_name']}")
        
        print("=" * 80)
    
    def run_specific_tests(self, test_patterns: List[str]) -> Dict[str, Any]:
        """Run specific tests matching patterns."""
        self.metrics.start_testing()
        
        if self.verbose:
            print(f"Running specific tests matching patterns: {test_patterns}")
        
        results = {}
        for test_suite in self.test_suites:
            suite_name = test_suite.__name__
            
            # Check if suite matches any pattern
            if any(pattern.lower() in suite_name.lower() for pattern in test_patterns):
                if self.verbose:
                    print(f"\nRunning {suite_name}...")
                
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss
                
                try:
                    suite = unittest.TestLoader().loadTestsFromTestCase(test_suite)
                    runner = unittest.TextTestRunner(verbosity=2 if self.verbose else 1, stream=open(os.devnull, 'w'))
                    result = runner.run(suite)
                    
                    execution_time = time.time() - start_time
                    memory_usage = (psutil.Process().memory_info().rss - start_memory) / (1024 * 1024)
                    
                    self.metrics.record_test_result(
                        suite_name,
                        'passed' if result.wasSuccessful() else 'failed',
                        execution_time,
                        memory_usage
                    )
                    
                    results[suite_name] = {
                        'success': result.wasSuccessful(),
                        'tests_run': result.testsRun,
                        'failures': len(result.failures),
                        'errors': len(result.errors),
                        'execution_time': execution_time,
                        'memory_usage_mb': memory_usage
                    }
                
                except Exception as e:
                    execution_time = time.time() - start_time
                    memory_usage = (psutil.Process().memory_info().rss - start_memory) / (1024 * 1024)
                    
                    self.metrics.record_test_result(suite_name, 'failed', execution_time, memory_usage)
                    
                    results[suite_name] = {
                        'success': False,
                        'error': str(e),
                        'execution_time': execution_time,
                        'memory_usage_mb': memory_usage
                    }
        
        self.metrics.end_testing()
        return {
            'metrics': self.metrics.generate_report(),
            'results': results
        }
    
    def save_report(self, filename: str = "test_report.json"):
        """Save test report to file."""
        report = {
            'metrics': self.metrics.generate_report(),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'version': '2.0'
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        if self.verbose:
            print(f"\nTest report saved to: {filename}")


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description='ZEROUI 2.0 Constitution Rules Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true', help='Run tests in parallel')
    parser.add_argument('--pattern', '-t', nargs='+', help='Run specific test patterns')
    parser.add_argument('--report', '-r', help='Save report to file')
    
    args = parser.parse_args()
    
    runner = ConstitutionTestRunner(verbose=args.verbose, parallel=args.parallel)
    
    if args.pattern:
        results = runner.run_specific_tests(args.pattern)
    else:
        results = runner.run_all_tests()
    
    if args.report:
        runner.save_report(args.report)
    
    # Exit with error code if tests failed
    if results['metrics']['summary']['failed_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
