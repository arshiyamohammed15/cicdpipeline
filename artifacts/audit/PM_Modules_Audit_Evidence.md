# PM Modules Audit Evidence

Verdict: PASS (all passes passed).

## Rerun Freshness (2026-01-02T15:41:53+05:30)

USE_REAL_SERVICES=false set for all commands in this session.

PASS rerun status:
- PASS 1: PASS (rerun this session)
- PASS 2: PASS (rerun this session)
- PASS 3: PASS (rerun this session)
- PASS 4: PASS (rerun this session)
- PASS 5: PASS (rerun this session)

Commands executed (this session):
- `python scripts/audit/pm_inventory_allowed_paths.py --out-dir artifacts/audit`
- `python -m pytest --import-mode=importlib tests/contracts/mmm_engine/validate_examples.py tests/contracts/cross_cutting_concern_services/validate_examples.py tests/contracts/signal_ingestion_and_normalization/validate_examples.py tests/contracts/detection_engine_core/validate_examples.py tests/contracts/integration_adaptors/validate_examples.py tests/contracts/llm_gateway/validate_examples.py tests/contracts/evidence_receipt_indexing_service/validate_examples.py -q`
- `python scripts/ci/validate_llm_gateway_schemas.py`
- `USE_REAL_SERVICES=false python -m pytest --import-mode=importlib tests/pm_audit/test_pm_smoke.py -q`
- `USE_REAL_SERVICES=false python -m pytest --import-mode=importlib tests/pm_audit/test_pm_e2e_golden_path.py -q`

Log files created (this session):
- `artifacts/audit/logs/pass1_2_inventory_allowed_paths.log`
- `artifacts/audit/logs/pass3_contracts.log`
- `artifacts/audit/logs/pass3_llm_gateway_schema_validation.log`
- `artifacts/audit/logs/pass4_smoke.log`
- `artifacts/audit/logs/pass5_e2e_golden_path.log`
- `artifacts/audit/logs/pm_smoke_receipts.jsonl`
- `artifacts/audit/logs/pm_e2e_receipts.jsonl`

PASS 1/2 log capture fixed; rerun at 2026-01-02T15:54:55+05:30.

Invariants validated by PASS 4/5:
- receipt_id UUID invariant validated by `artifacts/audit/logs/pm_smoke_receipts.jsonl` and `artifacts/audit/logs/pm_e2e_receipts.jsonl` (PM-1 receipt_id values are UUIDs).
- timestamp_utc single UTC format validated by PASS 5 ingestion success for PM-1 receipt in `artifacts/audit/logs/pm_e2e_receipts.jsonl`.

## Rerun Freshness (Local)

Run the full audit locally:
- `powershell -ExecutionPolicy Bypass -File scripts/audit/run_pm_audit_all.ps1`

Notes:
- The script prints `RUN_DIR=...` and sets `USE_REAL_SERVICES=false`.
- Evidence pack files in RUN_DIR:
  - `pm_module_inventory.md`
  - `pm_allowed_paths.md`
  - `pass1_2_inventory_allowed_paths.log`
  - `pass3_contracts.log`
  - `pass3_llm_gateway_schema_validation.log`
  - `pass4_smoke.log`
  - `pass5_e2e_golden_path.log`
  - `RUN_SUMMARY.md`

## Verify GitHub Actions without gh

If a token is available, use:
- `powershell -ExecutionPolicy Bypass -File scripts/ci/verify_workflow_run.ps1`

Token env vars supported (first found wins): `GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PAT`.
If no token is present, the script prints manual steps for checking the Actions UI.

Pass results:
- PASS 1 (Inventory): `artifacts/audit/pm_module_inventory.md`
- PASS 2 (Allowed paths): `artifacts/audit/pm_allowed_paths.md`
- PASS 3 (Contracts): `artifacts/audit/pm_contract_tests.md`
- PASS 4 (Smoke): `artifacts/audit/pm_smoke.md`
- PASS 5 (Golden path): `artifacts/audit/pm_e2e_golden_path.md`

Commands executed:
- `python scripts/audit/pm_inventory_allowed_paths.py --out-dir artifacts/audit`
- `python -m pytest --import-mode=importlib tests/contracts/mmm_engine/validate_examples.py tests/contracts/cross_cutting_concern_services/validate_examples.py tests/contracts/signal_ingestion_and_normalization/validate_examples.py tests/contracts/detection_engine_core/validate_examples.py tests/contracts/integration_adaptors/validate_examples.py tests/contracts/llm_gateway/validate_examples.py tests/contracts/evidence_receipt_indexing_service/validate_examples.py -q`
- `python scripts/ci/validate_llm_gateway_schemas.py`
- `USE_REAL_SERVICES=false python -m pytest --import-mode=importlib tests/pm_audit/test_pm_smoke.py -q`
- `USE_REAL_SERVICES=false python -m pytest --import-mode=importlib tests/pm_audit/test_pm_e2e_golden_path.py -q`

Log files:
- `artifacts/audit/logs/pass1_2_inventory_allowed_paths.log`
- `artifacts/audit/logs/pass3_contracts.log`
- `artifacts/audit/logs/pass3_llm_gateway_schema_validation.log`
- `artifacts/audit/logs/pass4_smoke.log`
- `artifacts/audit/logs/pass5_e2e_golden_path.log`
- `artifacts/audit/logs/pm_smoke_receipts.jsonl`
- `artifacts/audit/logs/pm_e2e_receipts.jsonl`

Receipt IDs referenced (smoke):
- PM-1: `00000000-0000-0000-0000-000000000001`
- PM-2: `00000000-0000-0000-0000-000000000002`
- PM-3: `receipt_0000000000000000`
- PM-4: `00000000-0000-0000-0000-000000000004`
- PM-5: `00000000-0000-0000-0000-000000000005`
- PM-6: `rcpt-req-smoke-001`
- PM-7: `00000000-0000-0000-0000-000000000007`

Receipt IDs referenced (golden path):
- PM-3: `receipt_0000000000000000`
- PM-4: `00000000-0000-0000-0000-000000000004`
- PM-1: `00000000-0000-0000-0000-000000000001`
- PM-5: `00000000-0000-0000-0000-000000000005`
- PM-7 ingest status for PM-4: success
- PM-7 ingest status for PM-1: success
- PM-7 ingest status for PM-5: success

Choke-point evidence:
- PM-6 (LLM Gateway): choke points listed in `docs/architecture/ZeroUI_No_Duplicate_Implementation_Map.md` include `src/cloud_services/llm_gateway/services/llm_gateway_service.py::LLMGatewayService._process` and `_call_provider`.
- PM-5 (Integration Adapters): choke point listed in map is `src/cloud_services/client-services/integration-adapters/services/integration_service.py::IntegrationService.execute_action`.
- PM-1/PM-2/PM-3/PM-4/PM-7: no choke points listed in the No-Duplicate Implementation Map; entrypoints are recorded in `artifacts/audit/pm_module_inventory.md`.

CI gate alignment (workflow-level):
- `.github/workflows/llm_gateway_ci.yml` path filters and install steps reference `src/cloud-services/llm_gateway/**` and `src/cloud-services/llm_gateway/requirements.txt`, but actual paths are under `src/cloud_services/llm_gateway/`.
- `.github/workflows/platform_gate.yml` installs dependencies from `src/cloud-services/llm_gateway/requirements.txt` and `src/cloud-services/client-services/integration-adapters/requirements.txt` (hyphenated paths not present in repo).
- `.github/workflows/pm_modules_audit.yml` runs PASS 1-5 audit commands on PRs/pushes for PM modules and audit assets.

Allowed paths scope note:
- PASS 2 uses a slug scan limited to `src/cloud_services`, `src/shared_libs`, and `src/vscode-extension/modules` based on paths declared in `docs/architecture/ZeroUI Module Categories V 3.0.md`.

Historical notes (pre-2026-01-02 rerun):
- Prior log path references included `artifacts/audit/logs/pass1_pass2_inventory_allowed_paths.log`, `artifacts/audit/logs/pass3_contract_tests.log`, and `artifacts/audit/logs/pass3_llm_gateway_schema.log`.
