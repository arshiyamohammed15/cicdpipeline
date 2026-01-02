from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple


REQUIRED_OWNER_PATHS: List[Tuple[str, str]] = [
    ("EPC-1", "src/cloud_services/shared-services/identity-access-management/"),
    ("EPC-2", "src/cloud_services/shared-services/data-governance-privacy/"),
    ("EPC-3", "src/cloud_services/shared-services/configuration-policy-management/"),
    ("CONFIG", "config/"),
    ("EPC-5", "src/cloud_services/shared-services/health-reliability-monitoring/"),
    ("EPC-11", "src/cloud_services/shared-services/key-management-service/"),
    ("EPC-12", "src/cloud_services/shared-services/contracts-schema-registry/"),
    ("EPC-13", "src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/"),
    ("PM-2", "src/shared_libs/cccs/"),
    ("PM-5", "src/cloud_services/client-services/integration-adapters/"),
    ("PM-6", "src/cloud_services/llm_gateway/"),
    ("PM-7", "src/cloud_services/shared-services/evidence-receipt-indexing-service/"),
]

CCP_MODULES: List[Tuple[str, str, List[Tuple[str, str]]]] = [
    (
        "CCP-1",
        "Identity & Trust Plane",
        [
            ("EPC-1", "src/cloud_services/shared-services/identity-access-management/"),
        ],
    ),
    (
        "CCP-2",
        "Policy & Configuration Plane",
        [
            ("EPC-3", "src/cloud_services/shared-services/configuration-policy-management/"),
            ("CONFIG", "config/"),
            ("EPC-12", "src/cloud_services/shared-services/contracts-schema-registry/"),
        ],
    ),
    (
        "CCP-3",
        "Evidence & Audit Plane",
        [
            ("PM-2", "src/shared_libs/cccs/"),
            ("PM-7", "src/cloud_services/shared-services/evidence-receipt-indexing-service/"),
        ],
    ),
    (
        "CCP-4",
        "Observability & Reliability Plane",
        [
            ("EPC-5", "src/cloud_services/shared-services/health-reliability-monitoring/"),
            ("PM-5", "src/cloud_services/client-services/integration-adapters/"),
        ],
    ),
    (
        "CCP-5",
        "Security & Supply Chain Plane",
        [
            ("EPC-11", "src/cloud_services/shared-services/key-management-service/"),
            ("EPC-2", "src/cloud_services/shared-services/data-governance-privacy/"),
        ],
    ),
    (
        "CCP-6",
        "Data & Memory Plane",
        [
            ("EPC-2", "src/cloud_services/shared-services/data-governance-privacy/"),
        ],
    ),
    (
        "CCP-7",
        "AI Lifecycle & Safety Plane",
        [
            ("PM-6", "src/cloud_services/llm_gateway/"),
            ("EPC-13", "src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/"),
        ],
    ),
]


def _resolve(repo_root: Path, rel_path: str) -> Path:
    return (repo_root / rel_path).resolve()


def _exists_str(path: Path) -> str:
    return str(path.exists()).lower()


def _write_inventory(out_path: Path, repo_root: Path) -> None:
    lines: List[str] = []
    lines.append("# CCP Modules Inventory (PASS 1)")
    lines.append("")
    for ccp_id, title, owners in CCP_MODULES:
        lines.append(f"## {ccp_id} - {title}")
        lines.append("- Owner modules/paths:")
        for module_id, rel_path in owners:
            abs_path = _resolve(repo_root, rel_path)
            lines.append(f"  - {module_id}: `{rel_path}` (exists={_exists_str(abs_path)})")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_allowed_paths(out_path: Path, repo_root: Path) -> None:
    lines: List[str] = []
    lines.append("# CCP Allowed Paths (PASS 1)")
    lines.append("")
    for ccp_id, title, owners in CCP_MODULES:
        lines.append(f"## {ccp_id} - {title}")
        lines.append("- Allowed roots:")
        for module_id, rel_path in owners:
            abs_path = _resolve(repo_root, rel_path)
            lines.append(f"  - {module_id}: `{rel_path}` (exists={_exists_str(abs_path)})")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _missing_required_paths(repo_root: Path) -> List[str]:
    missing: List[str] = []
    for module_id, rel_path in REQUIRED_OWNER_PATHS:
        abs_path = _resolve(repo_root, rel_path)
        if not abs_path.exists():
            missing.append(f"{module_id}: {rel_path}")
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_root", nargs="?", default=".")
    parser.add_argument("--out-dir", default="artifacts/audit")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    _write_inventory(out_dir / "ccp_module_inventory.md", repo_root)
    _write_allowed_paths(out_dir / "ccp_allowed_paths.md", repo_root)

    missing = _missing_required_paths(repo_root)
    if missing:
        missing_report = "\n".join(missing)
        raise SystemExit(f"Missing required owner paths:\n{missing_report}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
