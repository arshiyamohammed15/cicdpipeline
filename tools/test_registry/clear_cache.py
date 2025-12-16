"""
Utility to clear pytest cache and __pycache__ directories.
"""

from __future__ import annotations

import shutil
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _remove(path: Path) -> None:
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()
    except Exception as e:
        # Best-effort cleanup; ignore errors to avoid masking test runs.
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Best-effort cleanup failed for {path}: {e}", exc_info=True)


def clear_pytest_cache() -> None:
    _remove(PROJECT_ROOT / ".pytest_cache")
    for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
        _remove(cache_dir)


def main() -> int:
    clear_pytest_cache()
    logger.info("Cleared pytest cache and __pycache__ directories")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
