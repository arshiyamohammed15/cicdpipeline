#!/usr/bin/env python3
"""
Test runner for the constitution database system.

This module provides utilities to run all tests and generate coverage reports.
"""

import pytest
import sys
import os
from pathlib import Path
import subprocess
import json
import time
from typing import Dict, List, Any


class ConstitutionTestRunner:
    """Test runner for constitution database system."""
    
    def __init__(self, test_dir: str = None):
        """Initialize test runner."""
        if test_dir is None:
            test_dir = Path(__file__).parent
        self.test_dir = Path(test_dir)
        self.project_root = self.test_dir.parents[3]
        
    def run_all_tests(self, verbose: bool = True, coverage: bool = True) -> Dict[str, Any]:
        """Run all constitution database tests."""
        print("Running Constitution Database System Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test files to run
        test_files = [
            "test_database.py",
            "test_constitution_rules_json.py", 
            "test_backend_factory.py",
            "test_sync_manager.py",
            "test_migration.py",
            "test_cli_integration.py",
            "test_integration.py"
        ]
        
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "coverage_percentage": 0.0,
            "test_results": {},
            "duration": 0.0
        }
        
        # Run each test file
        for test_file in test_files:
            test_path = self.test_dir / test_file
            if test_path.exists():
                print(f"\nRunning {test_file}...")
                
                try:
                    # Build pytest command
                    cmd = [
                        sys.executable, "-m", "pytest",
                        str(test_path),
                        "-v" if verbose else "-q",
                        "--tb=short"
                    ]
                    
                    if coverage:
                        cmd.extend([
                            "--cov=config.constitution",
                            "--cov-report=term-missing",
                            "--cov-report=json:coverage.json"
                        ])
                    
                    # Run test
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        cwd=str(self.project_root)
                    )
                    
                    # Parse results
                    test_result = {
                        "file": test_file,
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "success": result.returncode == 0
                    }
                    
                    results["test_results"][test_file] = test_result
                    
                    if result.returncode == 0:
                        print(f"[PASS] {test_file} - PASSED")
                        results["passed"] += 1
                    else:
                        print(f"[FAIL] {test_file} - FAILED")
                        results["failed"] += 1
                        if verbose:
                            print(f"Error output: {result.stderr}")
                    
                except Exception as e:
                    print(f"[ERROR] {test_file} - ERROR: {e}")
                    results["errors"] += 1
                    results["test_results"][test_file] = {
                        "file": test_file,
                        "error": str(e),
                        "success": False
                    }
            else:
                print(f"[WARN] {test_file} - NOT FOUND")
        
        # Calculate total tests
        results["total_tests"] = results["passed"] + results["failed"] + results["errors"]
        
        # Load coverage report if available
        if coverage:
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                try:
                    with open(coverage_file, 'r') as f:
                        coverage_data = json.load(f)
                    results["coverage_percentage"] = coverage_data.get("totals", {}).get("percent_covered", 0.0)
                except Exception as e:
                    print(f"Warning: Could not load coverage report: {e}")
        
        # Calculate duration
        end_time = time.time()
        results["duration"] = end_time - start_time
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def run_specific_test(self, test_file: str, verbose: bool = True) -> Dict[str, Any]:
        """Run a specific test file."""
        test_path = self.test_dir / test_file
        if not test_path.exists():
            raise FileNotFoundError(f"Test file not found: {test_file}")
        
        print(f"Running {test_file}")
        print("=" * 40)
        
        start_time = time.time()
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v" if verbose else "-q",
            "--tb=short"
        ]
        
        # Run test
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        end_time = time.time()
        
        test_result = {
            "file": test_file,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "duration": end_time - start_time
        }
        
        if result.returncode == 0:
            print(f"[PASS] {test_file} - PASSED")
        else:
            print(f"[FAIL] {test_file} - FAILED")
            if verbose:
                print(f"Error output: {result.stderr}")
        
        return test_result
    
    def run_coverage_report(self) -> Dict[str, Any]:
        """Generate detailed coverage report."""
        print("Generating Coverage Report")
        print("=" * 40)
        
        # Run tests with coverage
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_dir),
            "--cov=config.constitution",
            "--cov-report=html:htmlcov",
            "--cov-report=json:coverage.json",
            "--cov-report=term-missing",
            "-q"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.project_root)
        )
        
        coverage_result = {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        # Load coverage data
        coverage_file = self.project_root / "coverage.json"
        if coverage_file.exists():
            try:
                with open(coverage_file, 'r') as f:
                    coverage_data = json.load(f)
                coverage_result["coverage_data"] = coverage_data
            except Exception as e:
                print(f"Warning: Could not load coverage data: {e}")
        
        if result.returncode == 0:
            print("[PASS] Coverage report generated successfully")
            print(f"HTML report: {self.project_root}/htmlcov/index.html")
            print(f"JSON report: {self.project_root}/coverage.json")
        else:
            print("[FAIL] Coverage report generation failed")
            print(f"Error: {result.stderr}")
        
        return coverage_result
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total = results["total_tests"]
        passed = results["passed"]
        failed = results["failed"]
        errors = results["errors"]
        duration = results["duration"]
        coverage = results["coverage_percentage"]
        
        print(f"Total Tests: {total}")
        print(f"[PASS] Passed: {passed}")
        print(f"[FAIL] Failed: {failed}")
        print(f"[ERROR] Errors: {errors}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Coverage: {coverage:.1f}%")
        
        if failed > 0 or errors > 0:
            print(f"\n[FAIL] {failed + errors} tests failed or errored")
            print("Failed tests:")
            for test_file, test_result in results["test_results"].items():
                if not test_result.get("success", False):
                    print(f"  - {test_file}")
        else:
            print(f"\n[SUCCESS] All tests passed!")
        
        if coverage > 0:
            if coverage >= 90:
                print(f"[EXCELLENT] Excellent coverage: {coverage:.1f}%")
            elif coverage >= 80:
                print(f"[GOOD] Good coverage: {coverage:.1f}%")
            elif coverage >= 70:
                print(f"[MODERATE] Moderate coverage: {coverage:.1f}%")
            else:
                print(f"[LOW] Low coverage: {coverage:.1f}%")
        
        print("=" * 60)
    
    def generate_test_report(self, results: Dict[str, Any], output_file: str = None) -> str:
        """Generate detailed test report."""
        if output_file is None:
            output_file = self.project_root / "test_report.json"
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "project": "ZeroUI2.0 Constitution Database System",
            "test_runner": "ConstitutionTestRunner",
            "results": results
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Test report saved to: {output_file}")
        return str(output_file)


def main():
    """Main function for test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Constitution Database System Test Runner")
    parser.add_argument("--test", help="Run specific test file")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--report", help="Generate test report to file")
    
    args = parser.parse_args()
    
    runner = ConstitutionTestRunner()
    
    if args.test:
        # Run specific test
        result = runner.run_specific_test(args.test, args.verbose)
        if args.report:
            runner.generate_test_report({"specific_test": result}, args.report)
    elif args.coverage:
        # Generate coverage report
        result = runner.run_coverage_report()
        if args.report:
            runner.generate_test_report({"coverage": result}, args.report)
    else:
        # Run all tests
        results = runner.run_all_tests(args.verbose, coverage=True)
        if args.report:
            runner.generate_test_report(results, args.report)
        
        # Exit with appropriate code
        if results["failed"] > 0 or results["errors"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
