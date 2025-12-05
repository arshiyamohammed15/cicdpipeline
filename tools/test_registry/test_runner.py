#!/usr/bin/env python3
"""
Fast Test Runner using Test Manifest.

Uses pre-generated manifest to quickly select and execute tests without
slow collection phase.

Usage:
    python tools/test_registry/test_runner.py --marker security
    python tools/test_registry/test_runner.py --module identity-access-management
    python tools/test_registry/test_runner.py --file tests/test_iam_service.py
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Set

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TestRunner:
    """Fast test runner using manifest."""

    def __init__(self, manifest_path: Optional[Path] = None):
        if manifest_path is None:
            manifest_path = PROJECT_ROOT / "artifacts" / "test_manifest.json"

        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Manifest not found: {manifest_path}. Run generate_manifest.py first."
            )

        self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.manifest_path = manifest_path

    def select_tests(
        self,
        markers: Optional[List[str]] = None,
        modules: Optional[List[str]] = None,
        files: Optional[List[str]] = None,
        test_names: Optional[List[str]] = None,
    ) -> List[str]:
        """Select tests based on criteria."""
        selected = set()

        for test_file in self.manifest["test_files"]:
            # Filter by markers
            if markers:
                if not any(marker in test_file["markers"] for marker in markers):
                    continue

            # Filter by module
            if modules:
                file_path = test_file["path"]
                if not any(module in file_path for module in modules):
                    continue

            # Filter by file pattern
            if files:
                file_path = test_file["path"]
                if not any(f in file_path for f in files):
                    continue

            # Filter by test name
            if test_names:
                found = False
                for cls in test_file["test_classes"]:
                    if any(name in cls["name"] for name in test_names):
                        found = True
                        break
                    for method in cls["methods"]:
                        if any(name in method["name"] for name in test_names):
                            found = True
                            break
                if not found:
                    for func in test_file["test_functions"]:
                        if any(name in func["name"] for name in test_names):
                            found = True
                            break
                if not found:
                    continue

            selected.add(test_file["path"])

        return sorted(list(selected))

    def run_tests(
        self,
        test_paths: List[str],
        parallel: bool = False,
        verbose: bool = False,
        **pytest_args,
    ) -> int:
        """Run selected tests using pytest."""
        if not test_paths:
            print("No tests selected")
            return 1

        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        # Add test paths
        cmd.extend(test_paths)

        # Add parallel execution
        if parallel:
            import multiprocessing
            workers = multiprocessing.cpu_count()
            cmd.extend(["-n", str(workers)])

        # Add verbosity
        if verbose:
            cmd.append("-v")
        else:
            cmd.append("-q")

        # Add custom pytest args
        for key, value in pytest_args.items():
            if value is True:
                cmd.append(f"--{key.replace('_', '-')}")
            elif value is not False:
                cmd.append(f"--{key.replace('_', '-')}={value}")

        print(f"Running {len(test_paths)} test files...")
        print(f"Command: {' '.join(cmd)}")

        # Execute pytest
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        return result.returncode


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Fast test runner using manifest")
    parser.add_argument(
        "--marker",
        action="append",
        help="Filter by pytest marker (can be specified multiple times)",
    )
    parser.add_argument(
        "--module",
        action="append",
        help="Filter by module name (can be specified multiple times)",
    )
    parser.add_argument(
        "--file",
        action="append",
        help="Filter by file pattern (can be specified multiple times)",
    )
    parser.add_argument(
        "--test",
        action="append",
        help="Filter by test name pattern (can be specified multiple times)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel using pytest-xdist",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to test manifest (default: artifacts/test_manifest.json)",
    )

    args = parser.parse_args()

    # Create runner
    runner = TestRunner(args.manifest)

    # Select tests
    test_paths = runner.select_tests(
        markers=args.marker,
        modules=args.module,
        files=args.file,
        test_names=args.test,
    )

    if not test_paths:
        print("No tests match the criteria")
        return 1

    print(f"Selected {len(test_paths)} test files")

    # Run tests
    return runner.run_tests(
        test_paths,
        parallel=args.parallel,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    sys.exit(main())

