#!/usr/bin/env python3
"""
Clear pytest cache and __pycache__ directories.

Fixes import file mismatch errors caused by duplicate module names.
"""

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def clear_pytest_cache():
    """Clear pytest cache directories."""
    cache_dirs = [
        PROJECT_ROOT / ".pytest_cache",
        PROJECT_ROOT / "__pycache__",
    ]

    # Find all __pycache__ directories
    for pycache_dir in PROJECT_ROOT.rglob("__pycache__"):
        cache_dirs.append(pycache_dir)

    cleared = []
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                if cache_dir.is_dir():
                    shutil.rmtree(cache_dir)
                else:
                    cache_dir.unlink()
                cleared.append(str(cache_dir.relative_to(PROJECT_ROOT)))
            except Exception as e:
                print(f"Warning: Could not remove {cache_dir}: {e}", file=sys.stderr)

    return cleared


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Clear pytest cache")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    if args.verbose:
        print("Clearing pytest cache...")

    cleared = clear_pytest_cache()

    if cleared:
        print(f"Cleared {len(cleared)} cache directories:")
        for cache_dir in cleared:
            print(f"  - {cache_dir}")
    else:
        print("No cache directories found")

    print("Cache cleared successfully")


if __name__ == "__main__":
    main()

