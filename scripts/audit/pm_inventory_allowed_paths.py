from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List

MODULE_DOC = Path("docs/architecture/ZeroUI Module Categories V 3.0.md")


def _extract_backticks(text: str) -> List[str]:
    return re.findall(r"`([^`]+)`", text)


def _parse_pm_modules(doc_text: str) -> Dict[str, Dict[str, List[str]]]:
    modules: Dict[str, Dict[str, List[str]]] = {}
    current = None
    for line in doc_text.splitlines():
        if line.startswith("### PM-"):
            heading = line.strip().removeprefix("### ")
            module_id = heading.split(" - ", 1)[0]
            modules[module_id] = {"heading": [heading], "vs_code": [], "cloud": []}
            current = module_id
            continue
        if current is None:
            continue
        stripped = line.strip()
        if stripped.startswith("- VS Code Extension:"):
            modules[current]["vs_code"].extend(_extract_backticks(stripped))
        if stripped.startswith("- Cloud Service:"):
            modules[current]["cloud"].extend(_extract_backticks(stripped))
        if stripped.startswith("### EPC-"):
            current = None
    return modules


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def _resolve_root(path: Path) -> Path:
    return path.parent if path.suffix else path


def _find_slug_dirs(root: Path, slug: str) -> List[Path]:
    matches: List[Path] = []
    if not root.exists():
        return matches
    for candidate in root.rglob("*"):
        if candidate.is_dir() and candidate.name == slug:
            matches.append(candidate)
    return sorted(set(matches))


def _write_inventory(out_path: Path, modules: Dict[str, Dict[str, List[str]]]) -> None:
    lines: List[str] = []
    lines.append("# PM Modules Inventory (PASS 1)\n")
    for module_id, info in modules.items():
        heading = info["heading"][0]
        lines.append(f"## {heading}")
        vs_paths = info["vs_code"]
        cloud_paths = info["cloud"]
        lines.append("- Declared paths:")
        if vs_paths:
            for path in vs_paths:
                lines.append(f"  - VS Code Extension: `{path}`")
        else:
            lines.append("  - VS Code Extension: (none listed)")
        if cloud_paths:
            for path in cloud_paths:
                lines.append(f"  - Cloud Service: `{path}`")
        else:
            lines.append("  - Cloud Service: (none listed)")
        lines.append("- Entry points:")
        for path in cloud_paths:
            candidate = Path(path)
            if candidate.suffix:
                exists = candidate.exists()
                lines.append(f"  - `{path}` (exists={str(exists).lower()})")
            else:
                entry = candidate / "__init__.py"
                exists = entry.exists()
                lines.append(f"  - `{entry.as_posix()}` (exists={str(exists).lower()})")
        lines.append("- Tests:")
        for test_path in info.get("tests", []):
            lines.append(f"  - `{test_path}`")
        if not info.get("tests"):
            lines.append("  - (none found)")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_allowed_paths(out_path: Path, modules: Dict[str, Dict[str, List[str]]]) -> None:
    lines: List[str] = []
    lines.append("# PM Modules Allowed Paths (PASS 2)\n")
    for module_id, info in modules.items():
        heading = info["heading"][0]
        lines.append(f"## {heading}")
        allowed_roots: List[Path] = []
        for path in info["vs_code"] + info["cloud"]:
            allowed_roots.append(_resolve_root(Path(path)))
        lines.append("- Allowed roots:")
        for root in allowed_roots:
            lines.append(f"  - `{root.as_posix()}` (exists={str(root.exists()).lower()})")
        violations: List[str] = []
        for root in allowed_roots:
            slug = root.name
            root_posix = root.as_posix()
            if root_posix.startswith("src/vscode-extension/modules"):
                search_root = Path("src/vscode-extension/modules")
            elif root_posix.startswith("src/cloud_services"):
                search_root = Path("src/cloud_services")
            elif root_posix.startswith("src/shared_libs"):
                search_root = Path("src/shared_libs")
            else:
                search_root = Path("src")
            matches = _find_slug_dirs(search_root, slug)
            for match in matches:
                if not any(str(match).startswith(str(allowed)) for allowed in allowed_roots):
                    violations.append(match.as_posix())
        if violations:
            lines.append("- Violations:")
            for violation in sorted(set(violations)):
                lines.append(f"  - `{violation}`")
        else:
            lines.append("- Violations: none detected by slug scan")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/audit")
    args = parser.parse_args()

    doc_text = MODULE_DOC.read_text(encoding="utf-8")
    modules = _parse_pm_modules(doc_text)

    test_candidates = {
        "PM-1": [
            "tests/mmm_engine",
            "tests/cloud_services/product_services/mmm_engine",
        ],
        "PM-2": [
            "tests/cccs",
        ],
        "PM-3": [
            "tests/sin",
            "tests/cloud_services/product_services/signal_ingestion_normalization",
        ],
        "PM-4": [
            "tests/cloud_services/product_services/detection_engine_core",
        ],
        "PM-5": [
            "tests/cloud_services/client_services/integration_adapters",
        ],
        "PM-6": [
            "tests/llm_gateway",
        ],
        "PM-7": [
            "tests/cloud_services/shared_services/evidence_receipt_indexing_service",
        ],
    }

    for module_id, candidates in test_candidates.items():
        existing = [path for path in candidates if Path(path).exists()]
        modules.setdefault(module_id, {"heading": [module_id], "vs_code": [], "cloud": []})
        modules[module_id]["tests"] = existing

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    _write_inventory(out_dir / "pm_module_inventory.md", modules)
    _write_allowed_paths(out_dir / "pm_allowed_paths.md", modules)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
