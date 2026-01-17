"""
Utility to clear all test caches: pytest, Jest, Node.js, VS Code, and coverage.
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
    """Remove a file or directory, ignoring errors."""
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()
    except Exception as e:
        # Best-effort cleanup; ignore errors to avoid masking test runs.
        logger.debug(f"Best-effort cleanup failed for {path}: {e}", exc_info=True)


def clear_pytest_cache() -> None:
    """Clear pytest cache directories."""
    _remove(PROJECT_ROOT / ".pytest_cache")
    # Exclude node_modules to avoid symlink issues
    try:
        for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
            if "node_modules" not in str(cache_dir):
                _remove(cache_dir)
    except (OSError, PermissionError) as e:
        # Ignore errors from symlinks or permission issues
        logger.debug(f"Error during __pycache__ cleanup: {e}")
    logger.info("Cleared pytest cache and __pycache__ directories")


def clear_jest_cache() -> None:
    """Clear Jest cache directories."""
    # Jest cache is typically in node_modules/.cache/jest
    jest_cache = PROJECT_ROOT / "node_modules" / ".cache" / "jest"
    _remove(jest_cache)
    
    # Also check for .jest-cache in root
    _remove(PROJECT_ROOT / ".jest-cache")
    
    logger.info("Cleared Jest cache directories")


def clear_node_cache() -> None:
    """Clear Node.js cache directories."""
    node_cache = PROJECT_ROOT / "node_modules" / ".cache"
    if node_cache.exists():
        # Remove all subdirectories but keep the .cache directory itself
        for item in node_cache.iterdir():
            _remove(item)
        logger.info("Cleared Node.js cache directories")


def clear_vscode_test_cache() -> None:
    """Clear VS Code test cache directories."""
    vscode_test_cache = PROJECT_ROOT / ".vscode-test"
    _remove(vscode_test_cache)
    
    # Also check in vscode-extension directory
    vscode_ext_cache = PROJECT_ROOT / "src" / "vscode-extension" / ".vscode-test"
    _remove(vscode_ext_cache)
    
    logger.info("Cleared VS Code test cache directories")


def clear_coverage_cache() -> None:
    """Clear coverage report directories."""
    _remove(PROJECT_ROOT / "coverage")
    _remove(PROJECT_ROOT / "htmlcov")
    _remove(PROJECT_ROOT / ".coverage")
    
    # Clear coverage in subdirectories, avoiding node_modules
    try:
        for cov_dir in PROJECT_ROOT.rglob("coverage"):
            if "node_modules" not in str(cov_dir):
                _remove(cov_dir)
    except (OSError, PermissionError):
        # Ignore errors from symlinks or permission issues
        pass
    
    logger.info("Cleared coverage directories")


def clear_all_caches() -> None:
    """Clear all test-related caches."""
    clear_pytest_cache()
    clear_jest_cache()
    clear_node_cache()
    clear_vscode_test_cache()
    clear_coverage_cache()
    logger.info("All test caches cleared")


def main() -> int:
    clear_all_caches()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
