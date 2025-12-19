#!/usr/bin/env python3
"""
Execute all IAM test suites with clear output.
"""

import sys
import unittest
from pathlib import Path
from datetime import datetime

# Add project root
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*80)
    print(text)
    print("="*80 + "\n")

def run_test_suite(module_name, suite_name):
    """Run a test suite and return results."""
    print_header(f"Running {suite_name}: {module_name}")

    try:
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(module_name)
        test_count = suite.countTestCases()
        print(f"Found {test_count} test cases")

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        print(f"\n{suite_name} Results:")
        print(f"  Tests run: {result.testsRun}")
        print(f"  Failures: {len(result.failures)}")
        print(f"  Errors: {len(result.errors)}")
        print(f"  Skipped: {len(result.skipped)}")

        if result.failures:
            print(f"\n  Failures:")
            for test, tb in result.failures[:3]:  # Show first 3
                print(f"    - {test}")

        if result.errors:
            print(f"\n  Errors:")
            for test, tb in result.errors[:3]:  # Show first 3
                print(f"    - {test}")

        return result.wasSuccessful(), result.testsRun, len(result.failures), len(result.errors)

    except Exception as e:
        print(f"ERROR: Failed to execute {suite_name}")
        print(f"  {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0, 1

def main():
    """Main execution."""
    print_header("IAM Module (EPC-1) Test Execution")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {project_root}")

    test_suites = [
        ('tests.test_iam_service', 'Unit Tests'),
        ('tests.test_iam_routes', 'Integration Tests'),
        ('tests.test_iam_performance', 'Performance Tests'),
    ]

    results = []
    for module_name, suite_name in test_suites:
        success, tests_run, failures, errors = run_test_suite(module_name, suite_name)
        results.append((suite_name, success, tests_run, failures, errors))

    # Summary
    print_header("Test Execution Summary")

    total_tests = sum(r[2] for r in results)
    total_failures = sum(r[3] for r in results)
    total_errors = sum(r[4] for r in results)
    all_passed = all(r[1] for r in results)

    for suite_name, success, tests_run, failures, errors in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{suite_name:30s} {status:8s} ({tests_run:3d} tests, {failures:2d} failures, {errors:2d} errors)")

    print(f"\nTotal: {total_tests} tests, {total_failures} failures, {total_errors} errors")

    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ SOME TESTS FAILED ({total_failures} failures, {total_errors} errors)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
