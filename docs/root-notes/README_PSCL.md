# PSCL (Policy Service Client Library) Workflow

## Purpose

The optional PSCL tools included with the ZeroUI VS Code extension generate reproducible build envelopes and pre-commit validation receipts for the current workspace. When enabled (`zeroui.pscl.enabled = true`) the extension can:

- collect the files that participate in a build and produce deterministic `FileEnvelope.json` / `BuildPlan.json`
- run a local validation pass that compares the workspace against the most recent plan and records the outcome as a signed `DecisionReceipt`
- surface the latest status directly in the status bar and decision card UI

By default PSCL is **disabled** so it does not affect existing workflows.

## How to Run

1. Enable the feature in your workspace or user settings:

   ```json
   {
     "zeroui.pscl.enabled": true,
     "zeroui.zuRoot": "C:\\ZeroUI\\storage" // adjust to your environment
   }
   ```

2. Prepare a build plan for the pending changes:

   - **Command Palette** → `ZeroUI: Prepare PSCL Build Plan` (`zeroui.pscl.preparePlan`)

3. Run the pre-commit validation:

   - **Command Palette** → `ZeroUI: Run Pre-commit Validation` (`zeroui.preCommit.validate`)

4. Review the results:

   - Status pill on the status bar reflects `PASS / WARN / BLOCK`
   - `ZeroUI: Show Decision Card` presents the latest details and quick fixes
   - `ZeroUI: Show Receipt Viewer` displays the raw receipt

Manual check suggestion: run `ZeroUI: Show Decision Card` or `ZeroUI: Run Pre-commit Validation` from the palette to see the updated status pill, decision card details, quick fixes, and output channel tailing the latest receipt JSON.

## Artifact Locations

All PSCL artifacts are written under the configured `ZU_ROOT` IDE plane. For a repository ID `sample-repo` the layout is:

- Build plan artifacts:
  - `{ZU_ROOT}/ide/pscl/sample-repo/FileEnvelope.json`
  - `{ZU_ROOT}/ide/pscl/sample-repo/BuildPlan.json`
- Decision receipts (month partitioned):
  - `{ZU_ROOT}/ide/receipts/sample-repo/{YYYY}/{MM}/receipts.jsonl`

The extension also writes human-readable logs to the **ZeroUI Pre-commit** output channel.

## How Receipts Appear

Each `DecisionReceipt` captures:

- `policy_snapshot_id`, `artifact_id`, digests, and build inputs taken from `BuildPlan.json`
- the final status (`pass`, `warn`, `soft_block`, `hard_block`)
- any mismatched file paths and digests when a validation fails
- labels such as `cost_profile`, `routing`, and model cache hints when they are present

The decision card summarises this information and exposes quick-fix actions:

- **Re-run PSCL Plan** – invokes `zeroui.pscl.preparePlan`
- **Open Diff** – opens a diff view for the first mismatched file (if any)
- Evidence and receipt shortcuts for deeper inspection

## Limitations

- PSCL remains **opt-in** (`zeroui.pscl.enabled` is `false` by default); when disabled all commands become harmless no-ops.
- The plan collection relies on local file hashes and does not fetch remote policy data—ensure the local policy cache under `{ZU_ROOT}/ide/policy` is populated.
- Build plans currently gather files based on Git status; staged files outside the repository or generated artifacts that are ignored by Git must be added manually if required.

