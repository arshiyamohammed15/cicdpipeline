from __future__ import annotations
import pytest

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.integration
def test_runner_outputs_summary() -> None:
    env = os.environ.copy()
    env.setdefault("USE_REAL_SERVICES", "false")
    result = subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "scripts/audit/run_epc_audit_all.ps1"),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )

    stdout = result.stdout or ""
    run_dir_line = next((line for line in stdout.splitlines() if line.strip().startswith("RUN_DIR=")), None)
    assert run_dir_line is not None

    run_dir = Path(run_dir_line.split("=", 1)[1].strip())
    summary_path = run_dir / "RUN_SUMMARY.md"
    assert summary_path.exists()

    summary_text = summary_path.read_text(encoding="utf-8")
    for label in ("PASS 1", "PASS 2", "PASS 3", "PASS 4", "PASS 5"):
        assert label in summary_text

    log_map = {
        "PASS 1": "pass1_inventory_allowed_paths.log",
        "PASS 2": "pass2_boundary_check.log",
        "PASS 3": "pass3_contracts_and_schemas.log",
        "PASS 4": "pass4_chokepoint_invariants.log",
        "PASS 5": "pass5_e2e_golden_path.log",
    }
    for label, log_name in log_map.items():
        status_line = next((line for line in summary_text.splitlines() if line.strip().startswith(f"- {label}:")), None)
        if status_line and "SKIPPED" not in status_line:
            assert (run_dir / log_name).exists()

    inventory = run_dir / "epc_module_inventory.md"
    assert inventory.exists()
    assert inventory.read_text(encoding="utf-8").strip()

    if result.returncode != 0:
        assert "FAIL" in summary_text or "SKIPPED" in summary_text
    else:
        assert "PASS" in summary_text
