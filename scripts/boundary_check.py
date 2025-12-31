#!/usr/bin/env python3
"""Boundary check for No-Duplicate Implementation Map enforcement paths."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional


MAP_FILENAME = "ZeroUI_No_Duplicate_Implementation_Map.md"


@dataclass
class PhaseSpec:
    name: str
    owner_paths: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    do_not_touch_paths: list[str] = field(default_factory=list)
    choke_point_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PathSpec:
    raw: str
    normalized: str
    is_dir: bool


@dataclass(frozen=True)
class Issue:
    severity: str
    phase: str
    file_path: str
    rule: str
    message: str


def _normalize_path(value: str) -> str:
    path = value.replace("\\", "/")
    if path.startswith("./"):
        path = path[2:]
    return path.strip("/")


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    return start


def _run_git(args: list[str], cwd: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        return []
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _get_changed_files(
    repo_root: Path,
    diff_range: Optional[str],
    staged: bool,
    unstaged: bool,
) -> list[str]:
    if diff_range:
        return _run_git(
            ["diff", "--name-only", diff_range, "--diff-filter=ACMR"], repo_root
        )

    files: list[str] = []
    if staged:
        files.extend(
            _run_git(
                ["diff", "--cached", "--name-only", "--diff-filter=ACMR"], repo_root
            )
        )
    if unstaged:
        files.extend(
            _run_git(["diff", "--name-only", "--diff-filter=ACMR"], repo_root)
        )
    return sorted(set(files))


def _extract_backticks(line: str) -> list[str]:
    return re.findall(r"`([^`]+)`", line)


def _parse_map(map_text: str) -> list[PhaseSpec]:
    phases: list[PhaseSpec] = []
    current: Optional[PhaseSpec] = None
    current_list: Optional[str] = None

    for line in map_text.splitlines():
        if line.startswith("## "):
            if line.startswith("## PH-"):
                if current:
                    phases.append(current)
                current = PhaseSpec(name=line[3:].strip())
                current_list = None
            else:
                if current:
                    phases.append(current)
                    current = None
                current_list = None
            continue

        if current is None:
            continue

        stripped = line.strip()
        if stripped.startswith("Owner Module") or stripped.startswith("Invoker Module"):
            for item in _extract_backticks(stripped):
                current.owner_paths.append(item)
            continue

        if stripped == "Allowed Repo Paths (ONLY these):":
            current_list = "allowed"
            continue
        if stripped == "Do NOT Touch modules:":
            current_list = "do_not_touch"
            continue
        if stripped == "Enforcement Choke-Point(s):":
            current_list = "choke_points"
            continue

        if current_list and stripped.startswith("- "):
            for item in _extract_backticks(stripped):
                if current_list == "allowed":
                    current.allowed_paths.append(item)
                elif current_list == "do_not_touch":
                    current.do_not_touch_paths.append(item)
                elif current_list == "choke_points":
                    if "::" in item:
                        current.choke_point_files.append(item.split("::", 1)[0])
            continue

        if stripped == "" or not stripped.startswith("- "):
            current_list = None

    if current:
        phases.append(current)
    return phases


def _build_path_specs(paths: Iterable[str], repo_root: Path) -> list[PathSpec]:
    specs: list[PathSpec] = []
    for raw in paths:
        normalized = _normalize_path(raw)
        candidate = repo_root / normalized
        if raw.endswith("/"):
            is_dir = True
        elif candidate.exists():
            is_dir = candidate.is_dir()
        else:
            is_dir = False
        specs.append(PathSpec(raw=raw, normalized=normalized.rstrip("/"), is_dir=is_dir))
    return specs


def _path_matches(path: str, spec: PathSpec) -> bool:
    normalized = _normalize_path(path)
    if spec.is_dir:
        base = spec.normalized
        return normalized == base or normalized.startswith(base + "/")
    return normalized == spec.normalized


def _paths_match_any(path: str, specs: Iterable[PathSpec]) -> bool:
    return any(_path_matches(path, spec) for spec in specs)


def _normalize_files(paths: Iterable[str]) -> list[str]:
    return sorted({_normalize_path(path) for path in paths})


def _collect_issues(
    phases: list[PhaseSpec],
    changed_files: list[str],
    repo_root: Path,
    strict: bool,
) -> list[Issue]:
    issues: list[Issue] = []
    changed_files_norm = _normalize_files(changed_files)

    for phase in phases:
        owner_specs = _build_path_specs(phase.owner_paths, repo_root)
        allowed_specs = _build_path_specs(phase.allowed_paths, repo_root)
        do_not_touch_specs = _build_path_specs(phase.do_not_touch_paths, repo_root)
        choke_points = set(_normalize_files(phase.choke_point_files))

        phase_touched = any(
            _paths_match_any(path, allowed_specs) or _paths_match_any(path, owner_specs)
            for path in changed_files_norm
        )
        if not phase_touched:
            continue

        for path in changed_files_norm:
            if _paths_match_any(path, owner_specs) and not _paths_match_any(
                path, allowed_specs
            ):
                issues.append(
                    Issue(
                        severity="ERROR",
                        phase=phase.name,
                        file_path=path,
                        rule="outside_allowed_paths",
                        message=(
                            "Change is outside allowed paths for "
                            f"{phase.name}: {path}"
                        ),
                    )
                )
            if _paths_match_any(path, do_not_touch_specs):
                issues.append(
                    Issue(
                        severity="ERROR",
                        phase=phase.name,
                        file_path=path,
                        rule="do_not_touch",
                        message=(
                            f"Change touches Do NOT Touch path for {phase.name}: {path}"
                        ),
                    )
                )

        if not choke_points:
            continue

        for path in changed_files_norm:
            if not _paths_match_any(path, allowed_specs):
                continue
            if path in choke_points:
                continue
            if not path.startswith("src/"):
                continue
            severity = "ERROR" if strict else "WARN"
            issues.append(
                Issue(
                    severity=severity,
                    phase=phase.name,
                    file_path=path,
                    rule="outside_chokepoint",
                    message=(
                        "Change is outside listed choke-point paths for "
                        f"{phase.name}: {path}"
                    ),
                )
            )

    return issues


def _print_issues(issues: list[Issue]) -> None:
    if not issues:
        return

    severity_order = {"ERROR": 0, "WARN": 1}
    issues_sorted = sorted(
        issues,
        key=lambda issue: (
            severity_order.get(issue.severity, 99),
            issue.phase,
            issue.file_path,
            issue.rule,
        ),
    )

    for issue in issues_sorted:
        print(f"[{issue.severity}] {issue.message}")


def _parse_args(argv: Optional[list[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate changed files against the No-Duplicate Implementation Map."
        )
    )
    parser.add_argument(
        "--map",
        default=MAP_FILENAME,
        help=f"Path to the map file (default: {MAP_FILENAME})",
    )
    parser.add_argument(
        "--diff-range",
        help="Git diff range to inspect (e.g., HEAD~1..HEAD)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Inspect staged changes (default when no mode is selected)",
    )
    parser.add_argument(
        "--unstaged",
        action="store_true",
        help="Inspect unstaged changes",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect staged + unstaged changes",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat chokepoint warnings as errors",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    repo_root = _find_repo_root(Path(__file__).resolve().parent)

    map_path = repo_root / args.map
    if not map_path.exists():
        print(f"[ERROR] Map file not found: {map_path}", file=sys.stderr)
        return 1

    map_text = map_path.read_text(encoding="utf-8")
    phases = _parse_map(map_text)
    if not phases:
        print("[ERROR] No phases parsed from map.", file=sys.stderr)
        return 1

    staged = args.staged
    unstaged = args.unstaged
    if args.all:
        staged = True
        unstaged = True
    if not args.diff_range and not staged and not unstaged:
        staged = True

    changed_files = _get_changed_files(repo_root, args.diff_range, staged, unstaged)
    if not changed_files:
        print("No changed files detected. Boundary check passed.")
        return 0

    issues = _collect_issues(phases, changed_files, repo_root, args.strict)
    _print_issues(issues)

    has_errors = any(issue.severity == "ERROR" for issue in issues)
    if has_errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
