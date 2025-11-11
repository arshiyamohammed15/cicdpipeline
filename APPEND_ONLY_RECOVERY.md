## Append-only Recovery Playbook (WORM Continuity)

Repository: `D:\Projects\ZeroUI2.0`  
Receipts file currently in scope: `D:\Projects\ZeroUI2.0\.zeroui\pscl-runtime\ide\receipts\zeroui2-0\2025\11\receipts.jsonl`

### 0. Prepare PowerShell logging helper

```powershell
$receiptPath = 'D:\Projects\ZeroUI2.0\.zeroui\pscl-runtime\ide\receipts\zeroui2-0\2025\11\receipts.jsonl'
$logPath = 'D:\Projects\ZeroUI2.0\pscl_receipt_log.txt'

function Show-ReceiptState {
    param([string]$Label)
    if (Test-Path -LiteralPath $receiptPath) {
        $info = Get-Item -LiteralPath $receiptPath
        $hash = (Get-FileHash -LiteralPath $receiptPath -Algorithm SHA256).Hash
        $entry = "{0} | Length={1} | SHA256={2}" -f $Label, $info.Length, $hash
    } else {
        $entry = "{0} | MISSING" -f $Label
    }
    $entry | Tee-Object -FilePath $logPath -Append
}
```

Use `Show-ReceiptState '<tag>'` immediately **before and after** each numbered step below to capture byte length and hash transitions.

---

### 1. Ensure PSCL feature flag is enabled

- VS Code Settings (JSON or UI): set `"zeroui.pscl.enabled": true`.
- Verify once with `Show-ReceiptState '01-before-flag-check'`, confirm again after the change with `'01-after-flag-check'`.

### 2. Run the PSCL plan command (first Green run)

- Command Palette → `ZeroUI: Prepare PSCL Build Plan` (`command id: zeroui.pscl.preparePlan`).
- Log state:
  - `Show-ReceiptState '02-before-plan-1'`
  - Run the command.
  - `Show-ReceiptState '02-after-plan-1'`

### 3. Trigger the pre-commit validation pipeline (first Green run)

- Command Palette → `ZeroUI: Run Pre-commit Validation` (`command id: zeroui.preCommit.validate`).
- Log state with `Show-ReceiptState '03-before-precommit-1'` and `'03-after-precommit-1'`.

### 4. Repeat the plan + pre-commit sequence (second Green run)

- `Show-ReceiptState '04-before-plan-2'`
- `ZeroUI: Prepare PSCL Build Plan`
- `Show-ReceiptState '04-after-plan-2'`
- `Show-ReceiptState '05-before-precommit-2'`
- `ZeroUI: Run Pre-commit Validation`
- `Show-ReceiptState '05-after-precommit-2'`

### 5. Re-run the verification harness (Green scenario)

- Harness script: `node .\.zeroui\verify\verify_pscl_check.mjs --repo zeroui2-0 --scenario green --zu-root D:\Projects\ZeroUI2.0\.zeroui\pscl-runtime`
- Capture pre/post state with `Show-ReceiptState '06-before-harness'` and `'06-after-harness'`.
- Review outputs:
  - Machine report: `.zeroui\verify\verification_results.json`
  - Human report: `VERIFICATION_PSCL_REPORT.md`

---

### Notes

- All commands are Windows-first and deterministic; no source edits required.
- `ZU_ROOT` must resolve to `D:\Projects\ZeroUI2.0\.zeroui\pscl-runtime` for the harness and plan execution agent to operate on the intended WORM directory.
- The appended `pscl_receipt_log.txt` file preserves before/after telemetry for audit purposes.

