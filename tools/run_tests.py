"""Simple runner for named pytest profiles defined in tools/test_profiles.yaml.

Examples:
    python tools/run_tests.py smoke
    python tools/run_tests.py root_validators -- -vv
    python tools/run_tests.py module_alerting -- -k alert
    python tools/run_tests.py full -- -vv
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import yaml


CONFIG_PATH = Path(__file__).resolve().parent / "test_profiles.yaml"


def load_profiles() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict) or "profiles" not in data or not isinstance(data["profiles"], dict):
        raise ValueError(f"Expected top-level 'profiles' mapping in {CONFIG_PATH}")
    return data["profiles"]


def _strip_delimiter(args: list[str]) -> list[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


def _ensure_default_flags(args: list[str]) -> list[str]:
    """Append default pytest flags unless already provided by the user/profile."""
    has_tb = any(a == "--tb" or a.startswith("--tb=") or a == "-tb" for a in args)
    has_disable_warnings = any(a == "--disable-warnings" for a in args)

    result = list(args)
    if not has_tb:
        result.append("--tb=short")
    if not has_disable_warnings:
        result.append("--disable-warnings")
    return result


def build_command(profile: dict, user_args: list[str]) -> list[str]:
    paths = profile.get("paths") or []
    if not paths:
        raise ValueError("Profile must define at least one path")
    extra_args = profile.get("extra_args") or []
    combined_args = _ensure_default_flags([*extra_args, *_strip_delimiter(user_args)])
    return [sys.executable, "-m", "pytest", *paths, *combined_args]


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run pytest with a named profile from tools/test_profiles.yaml",
        add_help=True,
    )
    parser.add_argument("profile_name", help="Name of the profile to run")
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Optional pytest args after -- are passed through unchanged",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        profiles = load_profiles()
    except (OSError, ValueError) as exc:
        print(f"Error loading profiles: {exc}", file=sys.stderr)
        return 1

    profile = profiles.get(args.profile_name)
    if profile is None:
        available = ", ".join(sorted(profiles)) if profiles else "none"
        print(
            f"Unknown profile '{args.profile_name}'. Available profiles: {available}",
            file=sys.stderr,
        )
        return 1

    try:
        cmd = build_command(profile, args.pytest_args)
    except ValueError as exc:
        print(f"Invalid profile '{args.profile_name}': {exc}", file=sys.stderr)
        return 1

    env = os.environ.copy()
    # Fix hashing for deterministic test runs unless caller already set it.
    env.setdefault("PYTHONHASHSEED", "0")
    # Expose the chosen profile for downstream observability; do not override if already set.
    env.setdefault("ZEROUI_TEST_PROFILE", args.profile_name)

    result = subprocess.run(cmd, env=env)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

