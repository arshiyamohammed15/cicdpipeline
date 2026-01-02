from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List


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
    detector: Callable[[Path], List[str]]


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIRS for part in path.parts)


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


def _schema_violations(repo_root: Path) -> List[str]:
    allowed_roots = [
        repo_root / "src" / "cloud_services" / "shared-services" / "contracts-schema-registry",
        repo_root / "contracts",
        repo_root / "config",
        repo_root / "gsmd",
    ]
    hits: List[str] = []
    for path in repo_root.rglob("*.schema.json"):
        if not path.is_file():
            continue
        if _is_excluded(path):
            continue
        if any(_is_under(path, allowed) for allowed in allowed_roots):
            continue
        hits.append(_relative(repo_root, path))
    return sorted(set(hits))


def _policy_violations(repo_root: Path) -> List[str]:
    allowed_roots = [
        repo_root / "config",
        repo_root / "config" / "policies",
        repo_root / "src" / "cloud_services" / "shared-services" / "configuration-policy-management",
        repo_root / "contracts",
    ]
    hits: List[str] = []
    policy_extensions = {".json", ".yaml", ".yml"}
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in policy_extensions:
            continue
        if _is_excluded(path):
            continue
        name_lower = path.name.lower()
        if "policy" not in name_lower:
            continue
        if any(_is_under(path, allowed) for allowed in allowed_roots):
            continue
        hits.append(_relative(repo_root, path))
    return sorted(set(hits))


def _alerting_violations(repo_root: Path) -> List[str]:
    allowed_root = repo_root / "src" / "cloud_services" / "shared-services" / "alerting-notification-service"
    allowed_clients = {
        repo_root
        / "src"
        / "cloud_services"
        / "llm_gateway"
        / "clients"
        / "alerting_client.py"
    }
    hits: List[str] = []
    src_root = repo_root / "src"
    if not src_root.exists():
        return hits
    for path in src_root.rglob("*.py"):
        if not path.is_file():
            continue
        if _is_excluded(path):
            continue
        if path in allowed_clients:
            continue
        if _is_under(path, allowed_root):
            continue
        path_tokens = [part.lower() for part in path.parts]
        if any("alert" in token or "notification" in token for token in path_tokens):
            hits.append(_relative(repo_root, path))
    return sorted(set(hits))


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
            name="JSON schemas outside EPC-12",
            description="*.schema.json files must be under EPC-12 contracts/schema registry roots.",
            detector=_schema_violations,
        ),
        Rule(
            name="Policy files outside EPC-3/config",
            description="Policy definitions must live under config/ or EPC-3 configuration-policy-management.",
            detector=_policy_violations,
        ),
        Rule(
            name="Alerting integrations outside EPC-4",
            description="Alerting/notification code must stay under EPC-4 owners.",
            detector=_alerting_violations,
        ),
    ]

    all_violations: List[str] = []
    report_lines: List[str] = [
        "# EPC Boundary Check (PASS 2)",
        "",
        f"Repo root: {repo_root.as_posix()}",
        "",
        "Rules checked:",
    ]

    detailed_sections: List[str] = []

    for rule in rules:
        report_lines.append(f"- {rule.name}: {rule.description}")
        results = rule.detector(repo_root)
        if results:
            all_violations.append(rule.name)
            detailed_sections.append(f"## Violations: {rule.name}")
            for item in results:
                detailed_sections.append(f"- {item}")
            detailed_sections.append("")

    report_lines.append("")
    if detailed_sections:
        report_lines.extend(detailed_sections)
    else:
        report_lines.append("## Violations: none detected")
        report_lines.append("")

    report_path = out_dir / "epc_boundary_violations.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return 1 if all_violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
