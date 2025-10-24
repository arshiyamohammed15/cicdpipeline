#!/usr/bin/env python3
"""
Direct Test Runner - Direct Execution
Runs tests directly from test case files.
Following Martin Fowler's Testing Principles with Gold Standard Quality.
"""

import sys
import os
import unittest
import time
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class DirectTestRunner:
    """Direct test runner with pure unittest execution."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.start_time = time.time()
        self.results = {}
        
    
    def discover_test_modules(self) -> List[str]:
        """Discover all test modules in the tests directory."""
        test_dir = Path(__file__).parent
        test_modules = []
        
        # Core test modules
        core_modules = [
            'test_constitution_rules',
            'test_rule_validation', 
            'test_rule_implementations',
            'test_performance'
        ]
        
        for module_name in core_modules:
            test_file = test_dir / f"{module_name}.py"
            if test_file.exists():
                test_modules.append(module_name)
                if self.verbose:
                    print(f"Found test module: {module_name}")
            else:
                if self.verbose:
                    print(f"Warning: Test module not found: {module_name}")
        
        return test_modules
    
    def run_test_module(self, module_name: str) -> Dict[str, Any]:
        """Run a single test module."""
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Running {module_name}")
            print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Import the test module
            module = __import__(f"tests.{module_name}", fromlist=[module_name])
            
            # Create test suite from module
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Run tests with detailed output
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            execution_time = time.time() - start_time
            
            module_result = {
                'module_name': module_name,
                'success': result.wasSuccessful(),
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'execution_time': execution_time,
                'failures_list': result.failures,
                'errors_list': result.errors
            }
            
            if self.verbose:
                status = "PASSED" if result.wasSuccessful() else "FAILED"
                print(f"\n{module_name}: {status} ({result.testsRun} tests, {execution_time:.2f}s)")
                
                if result.failures:
                    print(f"  Failures: {len(result.failures)}")
                    for test, traceback in result.failures:
                        print(f"    FAIL: {test}")
                
                if result.errors:
                    print(f"  Errors: {len(result.errors)}")
                    for test, traceback in result.errors:
                        print(f"    ERROR: {test}")
            
            return module_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            if self.verbose:
                print(f"\n{module_name}: ERROR - {str(e)}")
            
            return {
                'module_name': module_name,
                'success': False,
                'error': str(e),
                'execution_time': execution_time,
                'tests_run': 0,
                'failures': 0,
                'errors': 1
            }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all discovered test modules."""
        if self.verbose:
            print("=" * 80)
            print("ZEROUI 2.0 CONSTITUTION RULES - DIRECT TEST RUNNER")
            print("=" * 80)
            print(f"Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("Direct execution from test files")
            print("=" * 80)
        
        # Discover test modules
        test_modules = self.discover_test_modules()
        
        if not test_modules:
            if self.verbose:
                print("No test modules found!")
            return {'success': False, 'error': 'No test modules found'}
        
        if self.verbose:
            print(f"Found {len(test_modules)} test modules")
        
        # Run each test module
        results = {}
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_errors = 0
        
        for module_name in test_modules:
            module_result = self.run_test_module(module_name)
            results[module_name] = module_result
            
            total_tests += module_result.get('tests_run', 0)
            if module_result.get('success', False):
                total_passed += 1
            else:
                if module_result.get('errors', 0) > 0:
                    total_errors += 1
                else:
                    total_failed += 1
        
        # Calculate overall results
        total_execution_time = time.time() - self.start_time
        success_rate = (total_passed / len(test_modules) * 100) if test_modules else 0
        
        overall_result = {
            'success': total_errors == 0 and total_failed == 0,
            'total_modules': len(test_modules),
            'total_tests': total_tests,
            'passed_modules': total_passed,
            'failed_modules': total_failed,
            'error_modules': total_errors,
            'success_rate': success_rate,
            'execution_time': total_execution_time,
            'module_results': results
        }
        
        # Print summary
        if self.verbose:
            print("\n" + "=" * 80)
            print("DIRECT TEST EXECUTION SUMMARY")
            print("=" * 80)
            print(f"Total Modules: {len(test_modules)}")
            print(f"Passed: {total_passed}")
            print(f"Failed: {total_failed}")
            print(f"Errors: {total_errors}")
            print(f"Success Rate: {success_rate:.1f}%")
            print(f"Total Execution Time: {total_execution_time:.2f} seconds")
            print("=" * 80)
            
            if overall_result['success']:
                print("PASSED - ALL TESTS SUCCESSFUL")
            else:
                print("FAILED - SOME TESTS FAILED")
        
        return overall_result

def main():
    """Main entry point for direct test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZEROUI 2.0 Constitution Rules - Direct Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--module', '-m', help='Run specific test module')
    
    args = parser.parse_args()
    
    runner = DirectTestRunner(verbose=args.verbose)
    
    if args.module:
        # Run specific module
        if args.verbose:
            print(f"Running specific module: {args.module}")
        result = runner.run_test_module(args.module)
        success = result.get('success', False)
    else:
        # Run all modules
        result = runner.run_all_tests()
        success = result.get('success', False)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
