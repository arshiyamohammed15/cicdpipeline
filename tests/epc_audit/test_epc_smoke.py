from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


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
    if pass1.returncode != 0:
        assert "MISSING MODULE ROOTS" in inventory_text
        for module_id in unmapped_required:
            assert module_id in inventory_text
    else:
        assert all(module_id not in inventory_text for module_id in unmapped_required)

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
