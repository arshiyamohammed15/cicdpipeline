from __future__ import annotations
import pytest

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def _extract_missing_modules(inventory_text: str) -> set[str]:
    """Parse the PASS 1 inventory for the MISSING MODULE ROOTS section."""
    missing: set[str] = set()
    in_missing_section = False
    for line in inventory_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and "MISSING MODULE ROOTS" in stripped:
            in_missing_section = True
            continue
        if in_missing_section:
            if stripped.startswith("## "):
                break
            if not stripped:
                continue
            if stripped.startswith("- none"):
                return set()
            if stripped.startswith("- "):
                module_id = stripped.removeprefix("- ").split(":", 1)[0].strip()
                if module_id:
                    missing.add(module_id)
    return missing


@pytest.mark.smoke
@pytest.mark.unit
def test_pass1_and_pass2(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    pass1 = _run(
        [
            sys.executable,
            "scripts/audit/epc_inventory_allowed_paths.py",
            str(REPO_ROOT),
            "--out-dir",
            str(run_dir),
        ]
    )
    inventory = run_dir / "epc_module_inventory.md"
    allowed = run_dir / "epc_allowed_paths.md"
    assert pass1.returncode is not None
    assert inventory.exists()
    assert allowed.exists()

    inventory_text = inventory.read_text(encoding="utf-8")
    allowed_text = allowed.read_text(encoding="utf-8")
    assert inventory_text.strip()
    assert allowed_text.strip()

    unmapped_required = {"EPC-6", "EPC-7", "EPC-10", "EPC-14"}
    missing_modules = _extract_missing_modules(inventory_text)
    if pass1.returncode != 0:
        assert unmapped_required.issubset(missing_modules)
    else:
        assert missing_modules == set()

    pass2 = _run(
        [
            sys.executable,
            "scripts/audit/epc_boundary_check.py",
            str(REPO_ROOT),
            "--out-dir",
            str(run_dir),
        ]
    )
    boundary = run_dir / "epc_boundary_violations.md"
    assert pass2.returncode is not None
    assert boundary.exists()

    boundary_text = boundary.read_text(encoding="utf-8")
    assert boundary_text.strip()
    if pass2.returncode == 0:
        assert "none detected" in boundary_text.lower()
    else:
        assert "Violations" in boundary_text
