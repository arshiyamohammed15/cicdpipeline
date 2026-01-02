# EPC Modules Audit Evidence

- PASS 1: Inventory & Allowed Paths (`epc_module_inventory.md`, `epc_allowed_paths.md`)
- PASS 2: Boundary Check (`epc_boundary_violations.md`)
- PASS 3: Contracts & Schemas (`epc_contracts_and_schemas.md`)
- PASS 4: Chokepoint Invariants (`epc_chokepoint_invariants.md`)
- PASS 5: Offline Golden Path (`epc_e2e_golden_path.md`)

Local run (offline, USE_REAL_SERVICES=false):
- `powershell -ExecutionPolicy Bypass -File scripts/audit/run_epc_audit_all.ps1`
- Runner prints `RUN_DIR=<absolute path>` and writes evidence under `artifacts/audit_runs/epc_audit_YYYYMMDD_HHMMSS`.

Expected RUN_DIR contents:
- pass1_inventory_allowed_paths.log, pass2_boundary_check.log, pass3_contracts_and_schemas.log, pass4_chokepoint_invariants.log, pass5_e2e_golden_path.log
- epc_module_inventory.md
- epc_allowed_paths.md
- epc_boundary_violations.md
- epc_contracts_and_schemas.md
- epc_chokepoint_invariants.md
- epc_e2e_golden_path.md
- RUN_SUMMARY.md

Verify GitHub Actions status (token required):
- `pwsh -File scripts/ci/verify_workflow_run.ps1 -Repo ZeroUI2.1 -WorkflowFile epc_modules_audit.yml -Branch <branch> -Token $env:GITHUB_TOKEN`
- Script calls GitHub REST API and reports the latest run; set a PAT with Actions read + repo scope.

EPC-6 and EPC-14 are now mapped to shared-service stubs:
- EPC-6 → `src/cloud_services/shared-services/api-gateway-webhooks/`
- EPC-14 → `src/cloud_services/shared-services/trust-as-capability/`

Freshness: rerun `scripts/audit/run_epc_audit_all.ps1` to regenerate RUN_DIR before publishing results.

## Enforcing EPC Audit in GitHub (Manual)
- Confirm the EPC Modules Audit workflow run in GitHub Actions.
- In repository Settings → Branches, enable branch protection for `main`:
  - Require status checks to pass before merging.
  - Require branches to be up to date before merging.
  - Add required status check: `EPC Modules Audit` (workflow file: `.github/workflows/epc_modules_audit.yml`).
- Open a pull request to verify the required check blocks merges until the workflow succeeds.
