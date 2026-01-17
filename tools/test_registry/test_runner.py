"""
Fast test runner wrapper.

Supports filtering by marker, module, file pattern, or explicit test nodeid.
Falls back to plain pytest discovery if the manifest is missing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import logging
from pathlib import Path
from typing import Iterable, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

EXCLUDED_PREFIXES = ("tests/mmm_engine/",)

# Support execution as a script (python tools/test_registry/test_runner.py)
if __package__ in (None, ""):
    CURRENT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = CURRENT_DIR.parents[1]
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(CURRENT_DIR))
    from tools.test_registry.generate_manifest import (  # type: ignore
        DEFAULT_OUTPUT,
        PROJECT_ROOT,
        TEST_ROOT,
        _discover_tests,
    )
    from tools.test_registry.path_normalizer import setup_path_normalization  # type: ignore
else:
    from .generate_manifest import DEFAULT_OUTPUT, PROJECT_ROOT, TEST_ROOT, _discover_tests
    from .path_normalizer import setup_path_normalization


def load_manifest(path: Path) -> dict | None:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to load manifest from {path}: {e}", exc_info=True)
        return None
    return None


def _normalize_module_name(name: str) -> str:
    return name.replace("-", "_")


def _filter_tests(tests: Iterable[Dict[str, Any]], args: argparse.Namespace) -> List[Dict[str, Any]]:
    normalized_excludes = tuple(EXCLUDED_PREFIXES)

    selected: list[dict[str, Any]] = []
    for test in tests:
        path = test.get("path") or ""
        if path.replace("\\", "/").startswith(normalized_excludes):
            continue
        if args.module:
            mod = _normalize_module_name(args.module)
            test_mod = (test.get("module") or "").replace("-", "_")
            if mod not in test_mod:
                continue
        if args.file:
            if args.file not in test["path"]:
                continue
        if args.test and args.test not in test["nodeid"]:
            continue
        if args.marker:
            markers = set(test.get("markers") or [])
            if args.marker not in markers:
                continue
        selected.append(test)
    return selected


def _collect_tests_from_disk() -> List[Dict[str, Any]]:
    return _discover_tests([TEST_ROOT])


def build_pytest_command(args: argparse.Namespace, nodeids: list[str] | None = None) -> list[str]:
    cmd = [sys.executable, "-m", "pytest"]

    if args.marker:
        cmd.extend(["-m", args.marker])
    if args.parallel:
        # Use explicit workers count if provided, otherwise use auto
        if args.workers:
            cmd.extend(["-n", str(args.workers)])
        else:
            cmd.extend(["-n", "auto"])
    if args.verbose:
        cmd.append("-v")
    if args.extra:
        cmd.extend(args.extra)

    if nodeids:
        cmd.extend(nodeids)
    else:
        # Default to the paths specified or the tests root.
        targets = args.paths or [str(TEST_ROOT)]
        cmd.extend(targets)
    return cmd


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pytest with optional manifest-based selection.")
    parser.add_argument("--marker", help="Pytest marker to select")
    parser.add_argument("--module", help="Module name (hyphen or underscore) to select tests for")
    parser.add_argument("--file", help="Substring or filename to filter tests/files")
    parser.add_argument("--test", help="Substring of test nodeid to filter")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel with xdist (-n auto)")
    parser.add_argument("--workers", type=int, help="Number of parallel workers (requires --parallel). Default: auto")
    parser.add_argument("--verbose", action="store_true", help="Enable pytest verbose output")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT, help="Path to manifest JSON")
    parser.add_argument("--regenerate-manifest", action="store_true", help="Regenerate manifest before running")
    parser.add_argument("paths", nargs="*", help="Optional test paths; defaults to tests/")
    parser.add_argument(
        "--",
        dest="extra",
        nargs=argparse.REMAINDER,
        help="Additional pytest arguments after --",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    setup_path_normalization(PROJECT_ROOT)

    manifest = None
    if args.regenerate_manifest or not args.manifest.exists():
        try:
            if __package__ in (None, ""):
                import tools.test_registry.generate_manifest as gen_mod  # type: ignore
            else:
                from . import generate_manifest as gen_mod
            gen_mod.main(["--output", str(args.manifest), "--update"])
        except Exception as exc:
            logger.warning(f"Warning: could not regenerate manifest: {exc}")

    manifest = load_manifest(args.manifest)
    tests: list[dict[str, Any]]
    if manifest and "tests" in manifest:
        tests = list(manifest["tests"])
    else:
        tests = _collect_tests_from_disk()

    selected_tests = _filter_tests(tests, args)
    nodeids = [t["nodeid"] for t in selected_tests] if selected_tests else None
    file_paths = sorted({t["path"] for t in selected_tests}) if selected_tests else None

    if selected_tests:
        logger.info(f"Selected {len(selected_tests)} tests")
    else:
        logger.info("No filtered tests found; falling back to pytest selection")

    # Use file-level selection if the nodeid list would create an overly long command.
    use_nodeids = nodeids
    if nodeids and len(nodeids) > 300:
        use_nodeids = None
    cmd = build_pytest_command(args, use_nodeids or file_paths)
    logger.info("Running: %s", " ".join(cmd))
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
