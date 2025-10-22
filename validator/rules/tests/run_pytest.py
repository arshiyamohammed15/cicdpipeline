#!/usr/bin/env python3
"""
Pytest runner for ZeroUI 2.0 validator tests.

This script provides a unified way to run both unittest and pytest-style tests,
with proper configuration and reporting.
"""

import sys
import os
import subprocess
from pathlib import Path
from typing import List, Optional


def run_pytest_with_unittest_support(
    test_path: str = "validator/rules/tests",
    verbose: bool = True,
    coverage: bool = True,
    html_report: bool = True,
    markers: Optional[List[str]] = None
) -> int:
    """
    Run pytest with unittest support and coverage reporting.
    
    Args:
        test_path: Path to test directory
        verbose: Enable verbose output
        coverage: Enable coverage reporting
        html_report: Generate HTML coverage report
        markers: List of pytest markers to filter tests
        
    Returns:
        Exit code from pytest
    """
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test path
    cmd.append(test_path)
    
    # Add verbosity
    if verbose:
        cmd.extend(["-v", "--tb=short"])
    
    # Add coverage options
    if coverage:
        cmd.extend([
            "--cov=config",
            "--cov=validator", 
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
        
        if html_report:
            cmd.append("--cov-report=html:htmlcov")
    
    # Add markers if specified
    if markers:
        marker_expr = " or ".join(markers)
        cmd.extend(["-m", marker_expr])
    
    # Add other useful options
    cmd.extend([
        "--strict-markers",
        "--strict-config",
        "--disable-warnings",
        "--color=yes"
    ])
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run pytest
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent.parent)
    return result.returncode


def run_specific_test(test_file: str, test_class: Optional[str] = None, 
                     test_method: Optional[str] = None) -> int:
    """
    Run a specific test file, class, or method.
    
    Args:
        test_file: Test file to run
        test_class: Specific test class (optional)
        test_method: Specific test method (optional)
        
    Returns:
        Exit code from pytest
    """
    cmd = ["python", "-m", "pytest", "-v"]
    
    # Build test path
    test_path = f"validator/rules/tests/{test_file}"
    if test_class:
        test_path += f"::{test_class}"
    if test_method:
        test_path += f"::{test_method}"
    
    cmd.append(test_path)
    
    print(f"Running specific test: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent.parent)
    return result.returncode


def run_with_unittest_discovery() -> int:
    """
    Run tests using unittest discovery (fallback method).
    
    Returns:
        Exit code from unittest
    """
    cmd = [
        "python", "-m", "unittest", "discover",
        "-s", "validator/rules/tests",
        "-p", "test_*.py",
        "-v"
    ]
    
    print(f"Running with unittest discovery: {' '.join(cmd)}")
    print("-" * 60)
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent.parent)
    return result.returncode


def main():
    """Main entry point for the pytest runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ZeroUI 2.0 validator tests")
    parser.add_argument("--test-file", help="Run specific test file")
    parser.add_argument("--test-class", help="Run specific test class")
    parser.add_argument("--test-method", help="Run specific test method")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--no-html", action="store_true", help="Disable HTML coverage report")
    parser.add_argument("--markers", nargs="+", help="Pytest markers to filter tests")
    parser.add_argument("--unittest-fallback", action="store_true", help="Use unittest discovery as fallback")
    
    args = parser.parse_args()
    
    # Change to project root directory
    project_root = Path(__file__).parent.parent.parent.parent
    os.chdir(project_root)
    
    try:
        if args.unittest_fallback:
            return run_with_unittest_discovery()
        elif args.test_file:
            return run_specific_test(
                args.test_file, 
                args.test_class, 
                args.test_method
            )
        else:
            return run_pytest_with_unittest_support(
                verbose=True,
                coverage=not args.no_coverage,
                html_report=not args.no_html,
                markers=args.markers
            )
    except KeyboardInterrupt:
        print("\nTest run interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
