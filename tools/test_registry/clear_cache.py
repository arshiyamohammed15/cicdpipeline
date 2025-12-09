"""
Utility to clear pytest cache and __pycache__ directories.
"""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _remove(path: Path) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()
    except Exception:
        # Best-effort cleanup; ignore errors to avoid masking test runs.
        pass


def clear_pytest_cache() -> None:
    _remove(PROJECT_ROOT / ".pytest_cache")
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        _remove(cache_dir)


def main() -> int:
    clear_pytest_cache()
    print("Cleared pytest cache and __pycache__ directories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
