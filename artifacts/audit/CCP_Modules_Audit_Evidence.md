# CCP Modules Audit Evidence

This evidence pack defines the deterministic CCP Modules Audit for CCP-1 through CCP-7 and the required file-based outputs.

## Passes (1-5)
- PASS 1: Inventory + allowed paths via `scripts/audit/ccp_inventory_allowed_paths.py` producing `ccp_module_inventory.md` and `ccp_allowed_paths.md`.
- PASS 2: Boundary check (no duplicate controls) via `scripts/audit/ccp_boundary_check.py` producing `ccp_boundary_violations.md`.
- PASS 3: Contracts + schema validation via contract example tests and `scripts/ci/validate_llm_gateway_schemas.py` producing `ccp_contracts_and_schemas.md`.
- PASS 4: Chokepoint invariants via `tests/ccp_audit/test_ccp_smoke.py` producing `ccp_chokepoint_invariants.md`.
- PASS 5: E2E golden path via `tests/ccp_audit/test_ccp_e2e_golden_path.py` producing `ccp_e2e_golden_path.md`.

PASS means zero known gaps in these checks at the time of execution, not zero risk.

## Run locally (deterministic, offline)
Run the full audit:
- `powershell -ExecutionPolicy Bypass -File scripts/audit/run_ccp_audit_all.ps1`

Notes:
- The script sets `USE_REAL_SERVICES=false`.
- Evidence is written to `artifacts/audit_runs/ccp_audit_<yyyyMMdd_HHmmss>/`.
- The run directory always includes `RUN_SUMMARY.md`.

## Verify GitHub Actions without gh (REST-based)
Use the existing REST helper (token-based):
- `powershell -ExecutionPolicy Bypass -File scripts/ci/verify_workflow_run.ps1 -WorkflowFile ccp_modules_audit.yml`

Override `-Owner` and `-Repo` when validating forks or renamed repositories.

Token env vars supported: `GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PAT`.
If no token is present, the script prints manual UI steps.
