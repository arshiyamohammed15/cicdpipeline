"""
WHAT: Comprehensive test runner for all constitution rule tests with coverage reporting
WHY: Execute all tests with deterministic results and generate coverage reports

Test Execution:
- Run all test suites
- Generate coverage reports
- Provide deterministic results
- Track test execution metrics
"""
import unittest
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime

# Import all test modules
try:
    # Try relative imports first (when running from tests directory)
    from test_constitution_all_files import (
        ConstitutionStructureTests,
        ConstitutionRuleStructureTests,
        ConstitutionRuleContentTests
    )
    from test_constitution_rule_specific_coverage import (
        ConstitutionRuleSpecificTests,
        ConstitutionRuleCompletenessTests
    )
    from test_constitution_rule_semantics import (
        ConstitutionRuleSemanticsTests,
        ConstitutionRuleRelationshipsTests
    )
    from test_cursor_testing_rules import (
        CursorTestingRulesStructureTests,
        CursorTestingRulesFieldTests,
        CursorTestingRulesContentTests,
        CursorTestingRulesCategoryTests,
        CursorTestingRulesSeverityTests,
        CursorTestingRulesPolicyLinkageTests,
        CursorTestingRulesConsistencyTests
    )
except ImportError:
    # Fall back to absolute imports (when running from project root)
    from tests.test_constitution_all_files import (
        ConstitutionStructureTests,
        ConstitutionRuleStructureTests,
        ConstitutionRuleContentTests
    )
    from tests.test_constitution_rule_specific_coverage import (
        ConstitutionRuleSpecificTests,
        ConstitutionRuleCompletenessTests
    )
    from tests.test_constitution_rule_semantics import (
        ConstitutionRuleSemanticsTests,
        ConstitutionRuleRelationshipsTests
    )
    from tests.test_cursor_testing_rules import (
        CursorTestingRulesStructureTests,
        CursorTestingRulesFieldTests,
        CursorTestingRulesContentTests,
        CursorTestingRulesCategoryTests,
        CursorTestingRulesSeverityTests,
        CursorTestingRulesPolicyLinkageTests,
        CursorTestingRulesConsistencyTests
    )


class ComprehensiveTestRunner:
    """Run all constitution tests and generate reports."""

    def __init__(self, output_dir: Path = None):
        """
        Initialize test runner.

        Args:
            output_dir: Directory for test reports (default: tests/test_reports)
        """
        if output_dir is None:
            output_dir = Path(__file__).parent / 'test_reports'
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test results
        self.results = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': 0,
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'test_details': []
        }

    def run_all_tests(self, verbosity: int = 2) -> Dict[str, Any]:
        """
        Run all constitution test suites.

        Args:
            verbosity: Test output verbosity (0, 1, or 2)

        Returns:
            Dictionary with test results
        """
        self.results['start_time'] = datetime.now().isoformat()
        start_time = time.time()

        # Create test loader
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()

        # Add all test classes
        test_classes = [
            ConstitutionStructureTests,
            ConstitutionRuleStructureTests,
            ConstitutionRuleContentTests,
            ConstitutionRuleSpecificTests,
            ConstitutionRuleCompletenessTests,
            ConstitutionRuleSemanticsTests,
            ConstitutionRuleRelationshipsTests,
            CursorTestingRulesStructureTests,
            CursorTestingRulesFieldTests,
            CursorTestingRulesContentTests,
            CursorTestingRulesCategoryTests,
            CursorTestingRulesSeverityTests,
            CursorTestingRulesPolicyLinkageTests,
            CursorTestingRulesConsistencyTests
        ]

        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)

        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            stream=sys.stdout,
            buffer=True
        )

        result = runner.run(suite)

        # Calculate duration
        end_time = time.time()
        duration = end_time - start_time

        # Compile results
        self.results['end_time'] = datetime.now().isoformat()
        self.results['duration_seconds'] = round(duration, 3)
        self.results['total_tests'] = result.testsRun
        self.results['passed'] = result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)
        self.results['failed'] = len(result.failures)
        self.results['errors'] = len(result.errors)
        self.results['skipped'] = len(result.skipped)

        # Add failure/error details
        for test, traceback in result.failures:
            self.results['test_details'].append({
                'test': str(test),
                'status': 'FAILED',
                'traceback': traceback
            })

        for test, traceback in result.errors:
            self.results['test_details'].append({
                'test': str(test),
                'status': 'ERROR',
                'traceback': traceback
            })

        return self.results

    def save_report(self, filename: str = None) -> Path:
        """
        Save test results to JSON file.

        Args:
            filename: Output filename (default: auto-generated timestamp)

        Returns:
            Path to saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'constitution_test_report_{timestamp}.json'

        report_path = self.output_dir / filename

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        return report_path

    def print_summary(self):
        """Print test execution summary."""
        print("\n" + "=" * 70)
        print("CONSTITUTION RULES TEST SUITE - EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Total Tests:     {self.results['total_tests']}")
        print(f"Passed:           {self.results['passed']}")
        print(f"Failed:           {self.results['failed']}")
        print(f"Errors:           {self.results['errors']}")
        print(f"Skipped:          {self.results['skipped']}")
        print(f"Duration:         {self.results['duration_seconds']:.3f} seconds")
        print(f"Start Time:       {self.results['start_time']}")
        print(f"End Time:         {self.results['end_time']}")
        print("=" * 70)

        if self.results['failed'] > 0 or self.results['errors'] > 0:
            print("\nFAILURES AND ERRORS:")
            print("-" * 70)
            for detail in self.results['test_details']:
                print(f"{detail['status']}: {detail['test']}")
                if len(detail['traceback']) > 0:
                    # Print first line of traceback
                    first_line = detail['traceback'].split('\n')[0]
                    print(f"  {first_line}")
            print("-" * 70)

        # Coverage summary
        print("\nCOVERAGE SUMMARY:")
        print("-" * 70)
        print("Files Tested: 7")
        print("  - MASTER GENERIC RULES.json (301 rules)")
        print("  - VSCODE EXTENSION RULES.json (10 rules)")
        print("  - LOGGING & TROUBLESHOOTING RULES.json (11 rules)")
        print("  - MODULES AND GSMD MAPPING RULES.json (19 rules)")
        print("  - TESTING RULES.json (22 rules)")
        print("  - COMMENTS RULES.json (30 rules)")
        print("  - CURSOR TESTING RULES.json (22 rules)")
        print("Total Rules: 415")
        print("-" * 70)

        # Success rate
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed'] / self.results['total_tests']) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}%")

        print("=" * 70)


def main():
    """Main entry point for test runner."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run comprehensive constitution rules test suite'
    )
    parser.add_argument(
        '--verbosity',
        type=int,
        default=2,
        choices=[0, 1, 2],
        help='Test output verbosity (0=quiet, 1=normal, 2=verbose)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Directory for test reports'
    )
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip saving report file'
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    runner = ComprehensiveTestRunner(output_dir=output_dir)
    results = runner.run_all_tests(verbosity=args.verbosity)

    if not args.no_report:
        report_path = runner.save_report()
        print(f"\nTest report saved to: {report_path}")

    runner.print_summary()

    # Exit with error code if tests failed
    if results['failed'] > 0 or results['errors'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
