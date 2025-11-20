"""Render the ZeroUI constitution enforcement prompt from JSON sources.

This script ensures the enforcement instructions always reflect the current
rule set under ``docs/constitution``.  By default the prompt is printed to
stdout, but ``--output`` can persist it to a file (e.g. in docs/root-notes).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION_DIR = ROOT / "docs" / "constitution"


@dataclass(frozen=True)
class RuleStats:
    total: int
    enabled: int


def load_rules() -> list[dict]:
    rules: list[dict] = []
    for path in sorted(CONSTITUTION_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - configuration guard
            raise SystemExit(f"Unable to parse {path}: {exc}") from exc
        entries: Iterable[dict] = payload.get("constitution_rules", [])
        rules.extend(entries)
    return rules


def collect_stats(rules: Iterable[dict]) -> tuple[int, int, dict[str, RuleStats]]:
    total = 0
    enabled = 0
    categories: dict[str, list[bool]] = defaultdict(list)
    for rule in rules:
        total += 1
        is_enabled = bool(rule.get("enabled", True))
        if is_enabled:
            enabled += 1
        category = str(rule.get("category", "UNSPECIFIED")).strip() or "UNSPECIFIED"
        categories[category].append(is_enabled)
    per_category: dict[str, RuleStats] = {}
    for category, flags in sorted(categories.items()):
        per_category[category] = RuleStats(total=len(flags), enabled=sum(flags))
    return total, enabled, per_category


def build_prompt(total: int, enabled: int, per_category: dict[str, RuleStats]) -> str:
    lines: list[str] = []
    lines.append("# ZeroUI Constitution Enforcement Prompt")
    lines.append("")
    lines.append(
        f"You must validate every prompt against **all {enabled} enabled rules "
        f"({total} total)** defined in `docs/constitution/*.json` before generating "
        "any code or documentation."
    )
    lines.append("")
    lines.append("## Required Workflow")
    lines.append("1. Load the latest rule definitions from the JSON source of truth.")
    lines.append("2. Evaluate the incoming prompt against every enabled rule.")
    lines.append(
        "3. If any rule is violated, stop immediately and return "
        "`ERROR:CONSTITUTION_VIOLATION - <Rule ID>: <Rule Title>`."
    )
    lines.append("4. Only proceed with generation when **zero** violations are detected.")
    lines.append("")
    lines.append("## Coverage Expectations by Category")
    for category, stats in per_category.items():
        lines.append(
            f"- {category}: {stats.enabled} enabled / {stats.total} total rules enforceable."
        )
    lines.append("")
    lines.append("## Critical Guardrails")
    lines.append("- No hardcoded secrets or credentials (R-003).")
    lines.append("- No assumptions beyond provided information (R-002).")
    lines.append("- Keep all configuration in files/settings, never inline constants (R-004).")
    lines.append("- Enforce observability, testing, and documentation rules matching rule metadata.")
    lines.append("")
    lines.append(
        "Always cite the specific rule ID that failed and reference the JSON source "
        "to keep responses auditable."
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Optional path to save the rendered prompt (default: stdout).",
    )
    args = parser.parse_args()

    rules = load_rules()
    total, enabled, per_category = collect_stats(rules)
    prompt = build_prompt(total, enabled, per_category)

    if args.output:
        args.output.write_text(prompt, encoding="utf-8")
    else:
        print(prompt)


if __name__ == "__main__":
    main()

