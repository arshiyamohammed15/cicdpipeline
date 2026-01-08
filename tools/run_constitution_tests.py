#!/usr/bin/env python3
"""
Constitution Test Runner CLI

A command-line tool to execute Constitution test cases with various options.

This tool provides:
- Execution of all Constitution test suites
- Selective test execution by category
- Coverage reporting
- Detailed test results
- Multiple output formats

Usage:
    python tools/run_constitution_tests.py [options]
    python tools/run_constitution_tests.py --suite system
    python tools/run_constitution_tests.py --suite config --verbose
    python tools/run_constitution_tests.py --all --coverage
"""

import argparse
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set UTF-8 encoding for Windows compatibility
if sys.platform == "win32":
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'


class ConstitutionTestRunner:
    """Runner for Constitution test cases."""

    def __init__(self, project_root: Path):
        """
        Initialize the test runner.

        Args:
            project_root: Path to project root directory
        """
        self.project_root = project_root
        self.test_paths = {
            'system': project_root / 'tests' / 'system' / 'constitution',
            'config': project_root / 'tests' / 'config' / 'constitution',
            'positive_negative': project_root / 'tests' / 'constitution_positive_negative',
        }

    def validate_test_paths(self) -> Dict[str, bool]:
        """
        Validate that test paths exist.

        Returns:
            Dictionary mapping suite names to existence status
        """
        status = {}
        for suite, path in self.test_paths.items():
            status[suite] = path.exists() and path.is_dir()
        return status

    def run_pytest(
        self,
        test_path: Path,
        verbose: bool = False,
        coverage: bool = False,
        markers: Optional[List[str]] = None,
        output_file: Optional[Path] = None
    ) -> subprocess.CompletedProcess:
        """
        Run pytest on a test path.

        Args:
            test_path: Path to test directory or file
            verbose: Enable verbose output
            coverage: Generate coverage report
            markers: List of pytest markers to filter tests
            output_file: Optional file to write output to

        Returns:
            CompletedProcess result
        """
        cmd = [sys.executable, '-m', 'pytest', str(test_path)]

        if verbose:
            cmd.append('-v')
        else:
            cmd.append('-q')

        if coverage:
            cmd.extend([
                '--cov=config.constitution',
                '--cov-report=term-missing',
                '--cov-report=html',
            ])

        if markers:
            for marker in markers:
                cmd.extend(['-m', marker])

        # Add standard pytest options
        cmd.extend([
            '--tb=short',  # Short traceback format
            '--strict-markers',  # Strict marker validation
        ])

        print(f"\n{'='*70}")
        print(f"Running tests: {test_path}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*70}\n")

        # Run pytest
        result = subprocess.run(
            cmd,
            cwd=str(self.project_root),
            capture_output=False,
            text=True
        )

        return result

    def run_unittest_runner(
        self,
        test_module: str,
        verbose: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run unittest-based test runner (for comprehensive runner).

        Args:
            test_module: Module path to test runner
            verbose: Enable verbose output

        Returns:
            CompletedProcess result
        """
        cmd = [sys.executable, '-m', 'unittest', test_module]

        if verbose:
            cmd.append('-v')

        print(f"\n{'='*70}")
        print(f"Running unittest: {test_module}")
        print(f"Command: {' '.join(cmd)}")
        print(f"{'='*70}\n")

        result = subprocess.run(
            cmd,
            cwd=str(self.project_root),
            capture_output=False,
            text=True
        )

        return result

    def run_system_tests(
        self,
        verbose: bool = False,
        coverage: bool = False,
        comprehensive: bool = False
    ) -> int:
        """
        Run system constitution tests.

        Args:
            verbose: Enable verbose output
            coverage: Generate coverage report
            comprehensive: Use comprehensive test runner instead of pytest

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        if comprehensive:
            # Use the comprehensive test runner
            test_module = 'tests.system.constitution.test_constitution_comprehensive_runner'
            result = self.run_unittest_runner(test_module, verbose=verbose)
            return result.returncode
        else:
            # Use pytest
            result = self.run_pytest(
                self.test_paths['system'],
                verbose=verbose,
                coverage=coverage
            )
            return result.returncode

    def run_config_tests(
        self,
        verbose: bool = False,
        coverage: bool = False
    ) -> int:
        """
        Run config constitution tests.

        Args:
            verbose: Enable verbose output
            coverage: Generate coverage report

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        result = self.run_pytest(
            self.test_paths['config'],
            verbose=verbose,
            coverage=coverage
        )
        return result.returncode

    def run_positive_negative_tests(
        self,
        verbose: bool = False,
        coverage: bool = False
    ) -> int:
        """
        Run positive/negative constitution tests.

        Args:
            verbose: Enable verbose output
            coverage: Generate coverage report

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        result = self.run_pytest(
            self.test_paths['positive_negative'],
            verbose=verbose,
            coverage=coverage
        )
        return result.returncode

    def run_all_tests(
        self,
        verbose: bool = False,
        coverage: bool = False,
        comprehensive: bool = False
    ) -> int:
        """
        Run all constitution test suites.

        Args:
            verbose: Enable verbose output
            coverage: Generate coverage report
            comprehensive: Use comprehensive test runner for system tests

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        print("\n" + "="*70)
        print("CONSTITUTION TEST SUITE - RUNNING ALL TESTS")
        print("="*70)

        exit_codes = []

        # Run system tests
        print("\n[1/3] Running System Constitution Tests...")
        exit_code = self.run_system_tests(
            verbose=verbose,
            coverage=coverage,
            comprehensive=comprehensive
        )
        exit_codes.append(exit_code)

        # Run config tests
        print("\n[2/3] Running Config Constitution Tests...")
        exit_code = self.run_config_tests(
            verbose=verbose,
            coverage=coverage
        )
        exit_codes.append(exit_code)

        # Run positive/negative tests
        print("\n[3/3] Running Positive/Negative Constitution Tests...")
        exit_code = self.run_positive_negative_tests(
            verbose=verbose,
            coverage=coverage
        )
        exit_codes.append(exit_code)

        # Summary
        print("\n" + "="*70)
        print("TEST EXECUTION SUMMARY")
        print("="*70)
        print(f"System Tests:        {'PASSED' if exit_codes[0] == 0 else 'FAILED'}")
        print(f"Config Tests:         {'PASSED' if exit_codes[1] == 0 else 'FAILED'}")
        print(f"Positive/Negative:    {'PASSED' if exit_codes[2] == 0 else 'FAILED'}")
        print("="*70)

        # Return non-zero if any test suite failed
        return 0 if all(ec == 0 for ec in exit_codes) else 1


def main():
    """Main entry point for Constitution test runner CLI."""
    parser = argparse.ArgumentParser(
        description='Execute Constitution test cases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all Constitution tests
  python tools/run_constitution_tests.py --all

  # Run only system tests
  python tools/run_constitution_tests.py --suite system

  # Run with verbose output and coverage
  python tools/run_constitution_tests.py --suite config --verbose --coverage

  # Run comprehensive test runner for system tests
  python tools/run_constitution_tests.py --suite system --comprehensive

  # Run all tests with comprehensive runner
  python tools/run_constitution_tests.py --all --comprehensive --coverage
        """
    )

    # Test suite selection
    suite_group = parser.add_mutually_exclusive_group(required=True)
    suite_group.add_argument(
        '--all',
        action='store_true',
        help='Run all Constitution test suites'
    )
    suite_group.add_argument(
        '--suite',
        choices=['system', 'config', 'positive_negative'],
        help='Run specific test suite'
    )

    # Options
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Generate coverage report'
    )
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Use comprehensive test runner for system tests (unittest-based)'
    )
    parser.add_argument(
        '--markers', '-m',
        nargs='+',
        help='Pytest markers to filter tests (e.g., -m "unit integration")'
    )

    args = parser.parse_args()

    # Initialize runner
    runner = ConstitutionTestRunner(project_root)

    # Validate test paths
    path_status = runner.validate_test_paths()
    missing_paths = [suite for suite, exists in path_status.items() if not exists]
    if missing_paths:
        print(f"Warning: Test paths not found: {', '.join(missing_paths)}", file=sys.stderr)

    # Run tests based on arguments
    exit_code = 0

    try:
        if args.all:
            exit_code = runner.run_all_tests(
                verbose=args.verbose,
                coverage=args.coverage,
                comprehensive=args.comprehensive
            )
        elif args.suite == 'system':
            exit_code = runner.run_system_tests(
                verbose=args.verbose,
                coverage=args.coverage,
                comprehensive=args.comprehensive
            )
        elif args.suite == 'config':
            exit_code = runner.run_config_tests(
                verbose=args.verbose,
                coverage=args.coverage
            )
        elif args.suite == 'positive_negative':
            exit_code = runner.run_positive_negative_tests(
                verbose=args.verbose,
                coverage=args.coverage
            )
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.", file=sys.stderr)
        exit_code = 130
    except Exception as e:
        print(f"\n\nError executing tests: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        exit_code = 1

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
