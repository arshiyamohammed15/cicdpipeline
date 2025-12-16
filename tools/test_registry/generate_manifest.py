"""
Manifest generator for ZeroUI tests.

Creates a lightweight JSON index of discovered tests to speed up filtering.
If the manifest already exists, it is overwritten unless --update is provided
to confirm regeneration.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import logging
import sys
from pathlib import Path
from typing import Iterable, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = PROJECT_ROOT / "tests"
DEFAULT_OUTPUT = PROJECT_ROOT / "artifacts" / "test_manifest.json"
EXCLUDED_PREFIXES = ("tests/mmm_engine/",)


def _infer_module(rel_path: Path) -> str | None:
    parts = rel_path.parts
    if "cloud_services" in parts:
        idx = parts.index("cloud_services")
        if idx + 2 < len(parts):
            return parts[idx + 2]
    return None


def _extract_tests(text: str) -> tuple[list[str], list[tuple[str, str]]]:
    """
    Parse a test file and return module-level test functions and class test methods.
    """
    funcs: list[str] = []
    class_methods: list[tuple[str, str]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return funcs, class_methods

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    class_methods.append((node.name, item.name))
    return funcs, class_methods


def _discover_tests(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    marker_re = re.compile(r"@pytest\.mark\.([a-zA-Z0-9_]+)")

    for base in paths:
        if not base.exists():
            continue
        for file in base.rglob("test_*.py"):
            rel = file.relative_to(PROJECT_ROOT)
            rel_posix = rel.as_posix()
            if rel_posix.startswith(EXCLUDED_PREFIXES):
                continue
            text = ""
            try:
                text = file.read_text(encoding="utf-8")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Failed to read file {file}: {e}", exc_info=True)

            markers = sorted(set(marker_re.findall(text)))
            module = _infer_module(rel)
            func_names, class_methods = _extract_tests(text)

            # Module-level test functions
            for func in func_names:
                tests.append(
                    {
                        "path": rel_posix,
                        "nodeid": f"{rel_posix}::{func}",
                        "markers": markers,
                        "module": module,
                    }
                )

            # Class-based tests (individual methods)
            for cls, method in class_methods:
                tests.append(
                    {
                        "path": rel_posix,
                        "nodeid": f"{rel_posix}::{cls}::{method}",
                        "markers": markers,
                        "module": module,
                    }
                )

            # If no functions/classes matched, still index the file.
            if not func_names and not class_methods:
                tests.append(
                    {
                        "path": rel_posix,
                        "nodeid": rel_posix,
                        "markers": markers,
                        "module": module,
                    }
                )
    return tests


def write_manifest(tests: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "root": PROJECT_ROOT.as_posix(),
        "statistics": {
            "files": len({t["path"] for t in tests}),
            "tests": len(tests),
            "markers": sorted(
                {
                    m
                    for t in tests
                    for m in (t.get("markers") or [])
                }
            ),
        },
        "tests": tests,
    }
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate pytest manifest for faster selection.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Regenerate manifest even if it already exists.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[TEST_ROOT],
        help="Optional paths to scan (defaults to tests/).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.output.exists() and not args.update:
        logger.info(f"Manifest already exists at {args.output}; use --update to regenerate.")
        return 0

    tests = _discover_tests(args.paths)
    write_manifest(tests, args.output)

    stats = {
        "files": len({t['path'] for t in tests}),
        "tests": len(tests),
        "markers": len(
            {
                m
                for t in tests
                for m in (t.get("markers") or [])
            }
        ),
    }
    logger.info(f"Generated manifest at {args.output}")
    logger.info(f"Files: {stats['files']}  Tests: {stats['tests']}  Markers: {stats['markers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
