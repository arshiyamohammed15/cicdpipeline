from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


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
class EPCModule:
    module_id: str
    module_name: str
    expected_owner_roots: Sequence[str]
    required: bool = True


EPC_MANIFEST: Sequence[EPCModule] = (
    EPCModule(
        module_id="EPC-1",
        module_name="Identity & Access Management",
        expected_owner_roots=["src/cloud_services/shared-services/identity-access-management/"],
    ),
    EPCModule(
        module_id="EPC-2",
        module_name="Data Governance & Privacy",
        expected_owner_roots=["src/cloud_services/shared-services/data-governance-privacy/"],
    ),
    EPCModule(
        module_id="EPC-3",
        module_name="Configuration & Policy Management",
        expected_owner_roots=["src/cloud_services/shared-services/configuration-policy-management/"],
    ),
    EPCModule(
        module_id="EPC-4",
        module_name="Alerting & Notification Service",
        expected_owner_roots=["src/cloud_services/shared-services/alerting-notification-service/"],
    ),
    EPCModule(
        module_id="EPC-5",
        module_name="Health & Reliability Monitoring",
        expected_owner_roots=["src/cloud_services/shared-services/health-reliability-monitoring/"],
    ),
    EPCModule(
        module_id="EPC-6",
        module_name="API Gateway & Webhooks",
        expected_owner_roots=["src/cloud_services/shared-services/api-gateway-webhooks/"],
    ),
    EPCModule(
        module_id="EPC-7",
        module_name="Backup & Disaster Recovery",
        expected_owner_roots=["src/bdr/"],
    ),
    EPCModule(
        module_id="EPC-8",
        module_name="Deployment & Infrastructure",
        expected_owner_roots=["src/cloud_services/shared-services/deployment-infrastructure/"],
    ),
    EPCModule(
        module_id="EPC-9",
        module_name="User Behaviour Intelligence",
        expected_owner_roots=["src/cloud_services/product_services/user_behaviour_intelligence/"],
    ),
    EPCModule(
        module_id="EPC-10",
        module_name="Gold Standards",
        expected_owner_roots=[
            "src/vscode-extension/modules/m17-gold-standards/",
            "contracts/gold_standards/",
        ],
    ),
    EPCModule(
        module_id="EPC-11",
        module_name="Key & Trust Management (KMS & Trust Stores)",
        expected_owner_roots=["src/cloud_services/shared-services/key-management-service/"],
    ),
    EPCModule(
        module_id="EPC-12",
        module_name="Contracts & Schema Registry",
        expected_owner_roots=["src/cloud_services/shared-services/contracts-schema-registry/"],
    ),
    EPCModule(
        module_id="EPC-13",
        module_name="Budgeting, Rate-Limiting & Cost Observability",
        expected_owner_roots=["src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/"],
    ),
    EPCModule(
        module_id="EPC-14",
        module_name="Trust as a Capability",
        expected_owner_roots=["src/cloud_services/shared-services/trust-as-capability/"],
    ),
)


def _resolve(repo_root: Path, rel_path: str) -> Path:
    return (repo_root / rel_path).resolve()


def _exists_flag(path: Path) -> str:
    return str(path.exists()).lower()


def _relative(repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize_root(rel_path: str) -> str:
    return rel_path.replace("\\", "/").rstrip("/").lower()


def _iter_candidate_dirs(repo_root: Path) -> Iterable[Path]:
    search_roots = [repo_root / "src", repo_root / "contracts", repo_root / "config"]
    for root in search_roots:
        if not root.exists():
            continue
        for candidate in root.rglob("*"):
            if not candidate.is_dir():
                continue
            if any(part in EXCLUDE_DIRS for part in candidate.parts):
                continue
            yield candidate


def _candidate_dirs(repo_root: Path, module: EPCModule) -> List[str]:
    if module.expected_owner_roots:
        return []
    tokens = [
        module.module_id.lower().replace("-", ""),
        module.module_name.lower().replace(" ", "").replace("&", "").replace("-", ""),
    ]
    matches: List[str] = []
    for candidate in _iter_candidate_dirs(repo_root):
        normalized = candidate.name.lower().replace("-", "").replace("_", "")
        if any(token in normalized for token in tokens):
            matches.append(candidate.relative_to(repo_root).as_posix() + "/")
    return sorted(set(matches))[:10]


def _collect_missing(repo_root: Path, manifest: Sequence[EPCModule]) -> Dict[str, List[str]]:
    missing: Dict[str, List[str]] = {}
    for module in manifest:
        if not module.required:
            continue
        if not module.expected_owner_roots:
            missing[module.module_id] = ["(no owner roots mapped; required)"]
            continue
        absent: List[str] = []
        for rel_path in module.expected_owner_roots:
            abs_path = _resolve(repo_root, rel_path)
            if not abs_path.exists():
                absent.append(rel_path)
        if absent:
            missing[module.module_id] = absent
    return missing


def _collect_duplicates(manifest: Sequence[EPCModule]) -> Dict[str, List[str]]:
    seen: Dict[str, List[str]] = {}
    for module in manifest:
        for rel_path in module.expected_owner_roots:
            normalized = _normalize_root(rel_path)
            seen.setdefault(normalized, []).append(module.module_id)
    return {root: modules for root, modules in seen.items() if len(modules) > 1}


def _write_inventory(
    out_path: Path,
    repo_root: Path,
    manifest: Sequence[EPCModule],
    missing: Dict[str, List[str]],
    candidates: Dict[str, List[str]],
) -> None:
    lines: List[str] = []
    lines.append("# EPC Modules Inventory (PASS 1)")
    lines.append("")
    lines.append(f"Repo root: {repo_root.as_posix()}")
    lines.append("")
    for module in manifest:
        lines.append(f"## {module.module_id} - {module.module_name}")
        lines.append(f"- Required: {str(module.required).lower()}")
        lines.append("- Owner roots:")
        if not module.expected_owner_roots:
            lines.append("  - (missing mapping; required for audit)")
        else:
            for rel_path in module.expected_owner_roots:
                abs_path = _resolve(repo_root, rel_path)
                lines.append(f"  - `{rel_path}` (exists={_exists_flag(abs_path)})")
        lines.append("")
    if missing:
        lines.append("## MISSING MODULE ROOTS")
        for module_id, rel_paths in sorted(missing.items()):
            lines.append(f"- {module_id}:")
            for rel_path in rel_paths:
                lines.append(f"  - {rel_path}")
            if module_id in candidates:
                lines.append("  - Candidates:")
                if candidates[module_id]:
                    for candidate in candidates[module_id]:
                        lines.append(f"    - `{candidate}`")
                else:
                    lines.append("    - (none found)")
        lines.append("")
    else:
        lines.append("## MISSING MODULE ROOTS")
        lines.append("- none")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_allowed_paths(
    out_path: Path,
    repo_root: Path,
    manifest: Sequence[EPCModule],
    duplicates: Dict[str, List[str]],
) -> None:
    lines: List[str] = []
    lines.append("# EPC Allowed Paths (PASS 1)")
    lines.append("")
    lines.append(f"Repo root: {repo_root.as_posix()}")
    lines.append("")
    for module in manifest:
        lines.append(f"## {module.module_id} - {module.module_name}")
        lines.append("- Allowed roots:")
        if not module.expected_owner_roots:
            lines.append("  - (missing mapping; required for audit)")
        else:
            for rel_path in module.expected_owner_roots:
                abs_path = _resolve(repo_root, rel_path)
                lines.append(f"  - `{rel_path}` (exists={_exists_flag(abs_path)})")
        lines.append("")
    lines.append("## Duplicate owner root assignments")
    if duplicates:
        for root, modules in sorted(duplicates.items()):
            joined = ", ".join(sorted(modules))
            lines.append(f"- `{root}` shared by: {joined}")
    else:
        lines.append("- none detected (7x4 no-duplicate ownership upheld)")
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    parser.add_argument("--out-dir", default="artifacts/audit")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = _collect_missing(repo_root, EPC_MANIFEST)
    duplicates = _collect_duplicates(EPC_MANIFEST)
    candidates: Dict[str, List[str]] = {}
    for module in EPC_MANIFEST:
        if module.module_id in missing and not module.expected_owner_roots:
            candidates[module.module_id] = _candidate_dirs(repo_root, module)

    _write_inventory(out_dir / "epc_module_inventory.md", repo_root, EPC_MANIFEST, missing, candidates)
    _write_allowed_paths(out_dir / "epc_allowed_paths.md", repo_root, EPC_MANIFEST, duplicates)

    if missing or duplicates:
        reasons: List[str] = []
        if missing:
            missing_list = "; ".join(f"{mid}: {', '.join(paths)}" for mid, paths in sorted(missing.items()))
            reasons.append(f"missing owner roots -> {missing_list}")
        if duplicates:
            dup_list = "; ".join(f"{root} shared by {', '.join(mods)}" for root, mods in sorted(duplicates.items()))
            reasons.append(f"duplicate ownership -> {dup_list}")
        raise SystemExit(f"FAILED PASS 1: {'; '.join(reasons)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
