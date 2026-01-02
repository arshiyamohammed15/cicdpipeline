from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".vscode-test",
    "dist",
    "build",
    "artifacts",
    ".pytest_cache",
    "__pycache__",
    "docs",
    "contracts",
    "tests",
    "scripts",
    "tools",
    "tmp",
    "tmpdir",
    "temp",
    ".specstory",
    ".cursor",
    ".idea",
    ".vscode",
}


@dataclass(frozen=True)
class Rule:
    name: str
    description: str
    roots: Sequence[Path]
    allowed_roots: Sequence[Path]
    extensions: Sequence[str]
    patterns: Sequence[re.Pattern]
    check_filename: bool = False


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


def _iter_files(roots: Iterable[Path], extensions: Sequence[str]) -> Iterable[Path]:
    ext_set = set(extensions)
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_dir():
                continue
            if _is_excluded(path):
                continue
            if ext_set and path.suffix not in ext_set:
                continue
            yield path


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _scan_rule(repo_root: Path, rule: Rule) -> List[str]:
    violations: List[str] = []
    for path in _iter_files(rule.roots, rule.extensions):
        if any(_is_under(path, allowed) for allowed in rule.allowed_roots):
            continue
        matched: List[str] = []
        if rule.check_filename:
            name = path.name.lower()
            if any(pattern.search(name) for pattern in rule.patterns):
                matched.append("filename")
        else:
            content = _read_text(path)
            if not content:
                continue
            for pattern in rule.patterns:
                if pattern.search(content):
                    matched.append(pattern.pattern)
        if matched:
            rel_path = _relative(repo_root, path)
            detail = f"{rel_path} (match={','.join(sorted(set(matched)))})"
            violations.append(detail)
    return sorted(set(violations))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    parser.add_argument("--out-dir", default="artifacts/audit")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rules = [
        Rule(
            name="Policy files outside EPC-3/config",
            description="Policy rule files must live under EPC-3 or config/policies.",
            roots=[repo_root / "config", repo_root / "src"],
            allowed_roots=[
                repo_root / "config" / "policies",
                repo_root / "src" / "cloud_services" / "shared-services" / "configuration-policy-management",
            ],
            extensions=[".json"],
            patterns=[re.compile(r"policy", re.IGNORECASE)],
            check_filename=True,
        ),
        Rule(
            name="JSON schemas outside EPC-12",
            description="JSON schema definitions must live under EPC-12.",
            roots=[repo_root / "src"],
            allowed_roots=[
                repo_root / "src" / "cloud_services" / "shared-services" / "contracts-schema-registry",
            ],
            extensions=[".json"],
            patterns=[re.compile(r'"\$schema"')],
        ),
        Rule(
            name="IAM logic outside EPC-1",
            description="IAM evaluators must remain in EPC-1.",
            roots=[repo_root / "src"],
            allowed_roots=[
                repo_root / "src" / "cloud_services" / "shared-services" / "identity-access-management",
            ],
            extensions=[".py"],
            patterns=[
                re.compile(r"\bIAMService\b"),
                re.compile(r"\bRBACEvaluator\b"),
                re.compile(r"\bABACEvaluator\b"),
                re.compile(r"\bTokenValidator\b"),
            ],
        ),
        Rule(
            name="Token budgets outside PM-6",
            description="Token budgeting and counting must stay in PM-6.",
            roots=[repo_root / "src" / "cloud_services"],
            allowed_roots=[repo_root / "src" / "cloud_services" / "llm_gateway"],
            extensions=[".py"],
            patterns=[re.compile(r"token_(budget|counter)", re.IGNORECASE)],
        ),
        Rule(
            name="External tool reliability outside PM-5",
            description="Integration adapter circuit breakers must stay in PM-5.",
            roots=[repo_root / "src" / "cloud_services"],
            allowed_roots=[
                repo_root / "src" / "cloud_services" / "client-services" / "integration-adapters",
            ],
            extensions=[".py"],
            patterns=[re.compile(r"get_circuit_breaker_manager")],
        ),
        Rule(
            name="Receipt generation outside PM-2",
            description="Receipt generation must stay in CCCS (PM-2).",
            roots=[repo_root / "src"],
            allowed_roots=[repo_root / "src" / "shared_libs" / "cccs"],
            extensions=[".py"],
            patterns=[re.compile(r"\bwrite_receipt\s*\(")],
        ),
        Rule(
            name="Receipt indexing outside PM-7",
            description="Receipt ingestion must stay in PM-7.",
            roots=[repo_root / "src"],
            allowed_roots=[
                repo_root / "src" / "cloud_services" / "shared-services" / "evidence-receipt-indexing-service",
            ],
            extensions=[".py"],
            patterns=[
                re.compile(r"\bReceiptIngestionService\b"),
                re.compile(r"\bingest_receipt\b"),
            ],
        ),
        Rule(
            name="Governed memory writes outside EPC-2",
            description="Governed memory writes must stay in EPC-2 and emit receipts.",
            roots=[repo_root / "src"],
            allowed_roots=[
                repo_root / "src" / "cloud_services" / "shared-services" / "data-governance-privacy",
            ],
            extensions=[".py"],
            patterns=[
                re.compile(r"\bDataGovernanceService\b"),
                re.compile(r"\bGovernanceReceiptGenerator\b"),
            ],
        ),
    ]

    all_violations: List[str] = []
    report_lines: List[str] = [
        "# CCP Boundary Check (PASS 2)",
        "",
        f"Repo root: {repo_root.as_posix()}",
        "",
        "Rules checked:",
    ]

    for rule in rules:
        report_lines.append(f"- {rule.name}")
        violations = _scan_rule(repo_root, rule)
        if violations:
            all_violations.append(rule.name)
            report_lines.append("")
            report_lines.append(f"## Violations: {rule.name}")
            for item in violations:
                report_lines.append(f"- {item}")
            report_lines.append("")

    if not all_violations:
        report_lines.append("")
        report_lines.append("## Violations: none detected")

    report_path = out_dir / "ccp_boundary_violations.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return 1 if all_violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
