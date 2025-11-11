## PSCL Verification Report

### Discovery Summary (Phase A)
- **PSCL command id**: `zeroui.pscl.preparePlan` (`src/vscode-extension/package.json`, `src/vscode-extension/extension.ts`).
- **Pre-commit validation entry point**: `PreCommitValidationPipeline.run()` invoked by `zeroui.preCommit.validate` (`src/vscode-extension/extension.ts`, `src/vscode-extension/shared/validation/PreCommitValidationPipeline.ts`).
- **Receipt storage path**: `StoragePathResolver.resolveReceiptPath()` → `ide/receipts/{repo-id}/{yyyy}/{mm}/receipts.jsonl`.
- **Trust store (public keys)**: `product/policy/trust/pubkeys/` and `tenant/policy/trust/pubkeys/` (private keys via `<ZU_ROOT>/ide/trust/private/{kid}.pem`).
- **Signature verification utility**: `src/vscode-extension/shared/storage/ReceiptVerifier.ts` (canonical buffer + Ed25519 verification).
- **Policy snapshot reader/cache**: `src/vscode-extension/shared/storage/PolicySnapshotReader.ts` (IDE cache + env fallback).
- **Feature flag**: `zeroui.pscl.enabled` (package.json contributes; extension.ts guards commands).
- **Receipts JSONL append-only**: `ReceiptStorageService.appendToJsonl()` writes via append-only stream.

### Status
Status: **PENDING** — execute the PSCL verification harness for each scenario (green, red, flag-off) to populate results.

### Verification Matrix
| # | Item | Status | Key Evidence |
|---|------|--------|--------------|
| 1 | DoD checklist | N/A ⚪️ | — |
| 2 | Manual E2E proof (Green) | N/A ⚪️ | — |
| 3 | Manual E2E proof (Red) | N/A ⚪️ | — |
| 4 | Receipt integrity & signature verification | N/A ⚪️ | — |
| 5 | Determinism stress | N/A ⚪️ | — |
| 6 | Feature-flag bypass | N/A ⚪️ | — |
| 7 | Success matrix | N/A ⚪️ | — |
| 8 | Remediation | N/A ⚪️ | — |

### Evidence
- No verification runs recorded yet.

### Remediation
- None. Run the harness to generate evidence.
