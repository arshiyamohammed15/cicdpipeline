"""
Test Suite Runner

Executes all validator tests and generates coverage report.
"""

import unittest
import sys
import time
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Run all test suites and generate report."""
    
    print("=" * 80)
    print("ZEROUI 2.0 Constitution Validator - Comprehensive Test Suite")
    print("=" * 80)
    print()
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Count tests
    test_count = suite.countTestCases()
    print(f"Discovered {test_count} tests")
    print()
    
    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    
    # Print summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Duration: {duration:.2f}s")
    print()
    
    # Calculate success rate
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / 
                       result.testsRun * 100)
        print(f"Success Rate: {success_rate:.1f}%")
    
    print("=" * 80)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())

