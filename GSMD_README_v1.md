# GSMD Policy Snapshots — Repository Guide (v1)

**Generated:** 2025-10-21
**Files:** 190 snapshot.json files across 20 modules

---

## 1) Layout
Snapshots are stored at:

```
./gsmd/modules/M{NN}/{slug}/v{major}/snapshot.json
```

---

## 2) Snapshot JSON (required fields present in this bundle)
Each snapshot contains the following keys (verified on disk):

- `snapshot_id`  (e.g., `SNAP.M03.release_gates.v1`)
- `module_id`    (e.g., `M03`)
- `slug`         (policy slug)
- `version.major`
- `schema_version`
- `policy_version_ids[]`
- `snapshot_hash`  (`sha256:<hex>` of file contents)
- `signature`
- `kid`
- `effective_from` (ISO-8601)
- `deprecates[]` (optional)
- `evaluation_points[]` (pre-commit | pre-merge | pre-deploy | post-deploy)
- `messages.*`
- `overrides.*`
- `rollout.*`
- `observability.*`
- `privacy.*`
- `evidence.map[]`
- `receipts.required[]` (+ `optional[]`)
- `tests.fixtures[]`

---

## 3) Integrity
- `snapshot_hash` equals the SHA-256 of the current file contents.
- Modify any field after signing → rehash & resign; do not change after signature is applied.

### Quick check (PowerShell)
```powershell
$f = '.\gsmd\modules\M03\release_gates\v1\snapshot.json'
$j = Get-Content $f -Raw | ConvertFrom-Json
(Get-FileHash -Algorithm SHA256 $f).Hash.ToLower() | ForEach-Object { 'sha256:' + $_ }
$j.snapshot_hash  # should match
```

---

## 4) Module index (observed)
- **M01** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M02** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M03** → messages, observability, overrides, receipts_schema, release_gates, release_triggers, rollback_requirements, rollout, tests
- **M04** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M05** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M06** → evidence_map, gate_rules, legacy_triggers, messages, receipts_schema, risk_model, tests
- **M07** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M08** → checklist, conflict_predictors, merge_gates, messages, receipts_schema, tests
- **M09** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M10** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M11** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M12** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M13** → coverage_packs, evidence_map, messages, receipts_schema, tests, verification_rules
- **M14** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, reporting_policies, risk_model, rollout, tests, triggers
- **M15** → messages, metrics_definitions, receipts_schema, tests, trend_rules
- **M16** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, tests, triggers
- **M17** → alignment_rules, gs_catalog, messages, receipts_schema, tests
- **M18** → knowledge_signals, messages, nudge_rules, receipts_schema, tests
- **M19** → checklist, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, roi_views, rollout, tests, triggers
- **M20** → checklist, cross_module_policies, evidence_map, gate_rules, messages, observability, overrides, receipts_schema, risk_model, rollout, slo_safety, tests, triggers

---

## 5) Tooling provided
- `tools/gsmd-check.ps1` → validates required fields & `snapshot_hash`.
- `tools/manifest-build.ps1` → builds a Merkle-rooted release manifest.
- `tools/manifest-verify.ps1` → verifies file hashes + Merkle root.

---

## 6) Schemas
- `schema/snapshot.schema.json` — strict minimal schema matching these files.
- `schema/receipt.schema.json` — minimal receipt contract.
- `schema/override.schema.json` — tenant override with TTL + approvals.

---

## 7) Contract essentials
- Edge Agent must include `policy_snapshot_hash` and `policy_version_ids` from the snapshot in every decision receipt.
- Keep versions append-only: introduce `v2/` for breaking changes; do not overwrite `v1/`.
