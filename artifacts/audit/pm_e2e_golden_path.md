# PM Modules E2E Golden Path (PASS 5)

Result: PASS

Command:
- `USE_REAL_SERVICES=false python -m pytest --import-mode=importlib tests/pm_audit/test_pm_e2e_golden_path.py -q`

Logs:
- `artifacts/audit/logs/pass5_e2e_golden_path.log`
- `artifacts/audit/logs/pm_e2e_receipts.jsonl`

Receipt IDs recorded:
- PM-3: `receipt_0000000000000000`
- PM-4: `00000000-0000-0000-0000-000000000004`
- PM-1: `00000000-0000-0000-0000-000000000001`
- PM-5: `00000000-0000-0000-0000-000000000005`
- PM-7 ingestion:
  - PM-4 receipt success
  - PM-1 receipt success
  - PM-5 receipt success
