#!/usr/bin/env python3
"""
Unittest Direct Runner - Pure unittest execution
Runs tests using unittest discovery.
"""

import sys
import os
import unittest
import time
import shutil
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_unittest_discovery():
    """Run tests using unittest discovery."""
    print("=" * 80)
    print("ZEROUI 2.0 CONSTITUTION RULES - UNITTEST DISCOVERY RUNNER")
    print("=" * 80)
    print(f"Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Direct unittest discovery execution")
    print("=" * 80)
    
    # Discover and run tests
    test_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    
    # Load tests from specific modules
    test_modules = [
        'test_constitution_rules',
        'test_rule_validation', 
        'test_rule_implementations',
        'test_performance'
    ]
    
    suite = unittest.TestSuite()
    loaded_modules = 0
    
    for module_name in test_modules:
        try:
            module = __import__(f"tests.{module_name}", fromlist=[module_name])
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            loaded_modules += 1
            print(f"Loaded {module_name}: {module_suite.countTestCases()} tests")
        except Exception as e:
            print(f"Error loading {module_name}: {e}")
    
    if loaded_modules == 0:
        print("No test modules could be loaded!")
        return False
    
    print(f"\nTotal test cases: {suite.countTestCases()}")
    print("=" * 80)
    
    # Run tests
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    execution_time = time.time() - start_time
    
    # Print results
    print("\n" + "=" * 80)
    print("UNITTEST DISCOVERY RESULTS")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print(f"Execution time: {execution_time:.2f} seconds")
    print("=" * 80)
    
    if result.wasSuccessful():
        print("PASSED - ALL TESTS SUCCESSFUL")
    else:
        print("FAILED - SOME TESTS FAILED")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  {test}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  {test}")
    
    return result.wasSuccessful()

def main():
    """Main entry point for unittest discovery runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='ZEROUI 2.0 Constitution Rules - Unittest Discovery Runner')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    
    success = run_unittest_discovery()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
