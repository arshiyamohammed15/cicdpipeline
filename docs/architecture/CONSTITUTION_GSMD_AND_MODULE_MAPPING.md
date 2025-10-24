# ZeroUI — GSMD & Module Mapping **Constitution** (Derived, Deterministic)

> **Source of Truth:** This Constitution is derived **solely** from `MODULES_MAPPING_AND_GSMD_GUIDE.md`. It encodes, as enforceable rules, only what that guide states about module–folder mappings and the `gsmd/` contents. No additions.

---

## 1. Scope

1.1 This Constitution governs: (a) the **authoritative mapping** between **module codes M01–M20**, their **VS Code extension folders**, and their **GSMD folders**; and (b) the **validated invariants** and **checks** for `gsmd/` snapshot content.

1.2 It does **not** define behavior outside those topics.

---

## 2. Canonical Mapping (Authoritative)

**Rule 2.1 — One-to-one binding (code ↔ folders).** For each module code `MXX`, the following **MUST** exist and are authoritative:
- VS Code extension folder (slug exactness required):
  - `M01 → src/modules/m01-mmm-engine/`
  - `M02 → src/modules/m02-cross-cutting-concern-services/`
  - `M03 → src/modules/m03-release-failures-rollbacks/`
  - `M04 → src/modules/m04-signal-ingestion-normalization/`
  - `M05 → src/modules/m05-detection-engine-core/`
  - `M06 → src/modules/m06-legacy-systems-safety/`
  - `M07 → src/modules/m07-technical-debt-accumulation/`
  - `M08 → src/modules/m08-merge-conflicts-delays/`
  - `M09 → src/modules/m09-compliance-security-challenges/`
  - `M10 → src/modules/m10-integration-adapters/`
  - `M11 → src/modules/m11-feature-dev-blind-spots/`
  - `M12 → src/modules/m12-knowledge-silo-prevention/`
  - `M13 → src/modules/m13-monitoring-observability-gaps/`
  - `M14 → src/modules/m14-client-admin-dashboard/`
  - `M15 → src/modules/m15-product-success-monitoring/`
  - `M16 → src/modules/m16-roi-dashboard/`
  - `M17 → src/modules/m17-gold-standards/`
  - `M18 → src/modules/m18-knowledge-integrity-discovery/`
  - `M19 → src/modules/m19-reporting/`
  - `M20 → src/modules/m20-qa-testing-deficiencies/`
- GSMD folder:
  - `M01 → gsmd/gsmd/modules/M01/`
  - `M02 → gsmd/gsmd/modules/M02/`
  - `M03 → gsmd/gsmd/modules/M03/`
  - `M04 → gsmd/gsmd/modules/M04/`
  - `M05 → gsmd/gsmd/modules/M05/`
  - `M06 → gsmd/gsmd/modules/M06/`
  - `M07 → gsmd/gsmd/modules/M07/`
  - `M08 → gsmd/gsmd/modules/M08/`
  - `M09 → gsmd/gsmd/modules/M09/`
  - `M10 → gsmd/gsmd/modules/M10/`
  - `M11 → gsmd/gsmd/modules/M11/`
  - `M12 → gsmd/gsmd/modules/M12/`
  - `M13 → gsmd/gsmd/modules/M13/`
  - `M14 → gsmd/gsmd/modules/M14/`
  - `M15 → gsmd/gsmd/modules/M15/`
  - `M16 → gsmd/gsmd/modules/M16/`
  - `M17 → gsmd/gsmd/modules/M17/`
  - `M18 → gsmd/gsmd/modules/M18/`
  - `M19 → gsmd/gsmd/modules/M19/`
  - `M20 → gsmd/gsmd/modules/M20/`

**Rule 2.2 — Code as primary key.** The **module code (M01–M20)** is the primary identifier binding the extension folder and the GSMD folder.

---

## 3. GSMD Snapshot **Invariants** (Must-haves)

**Rule 3.1 — Presence of core files by module.**
- Every module **MUST** provide `messages/v1/snapshot.json` containing a `messages` object with **all** keys: `problems`, `status_pill`, `cards`.
- Every module **MUST** provide `receipts_schema/v1/snapshot.json` containing a `receipts` object with **both** keys: `required`, `optional`.

**Rule 3.2 — Required top-level fields in every `.../v1/snapshot.json`.**  
Each snapshot JSON **MUST** include **all** of the following top-level fields:
`snapshot_id`, `module_id`, `slug`, `version`, `schema_version`, `policy_version_ids`, `snapshot_hash`, `signature`, `kid`, `effective_from`, `evaluation_points`, `messages`, `rollout`, `observability`, `privacy`, `evidence`, `receipts`, `tests`.

**Rule 3.3 — Versioning constraints.**
- `schema_version` **MUST** equal `"1.0.0"`.
- `version.major` **MUST** equal `1`.

**Rule 3.4 — Policy linkage cardinality.**  
`policy_version_ids` **MUST** be an array of **length 1**.

**Rule 3.5 — Key identifier format.**  
`kid` **MUST** contain the substring `"ed25519"`.

**Rule 3.6 — Evaluation points shape.**  
`evaluation_points` **MUST** be a list.

---

## 4. CI Checks (Deterministic, Fail-Fast)

**Rule 4.1 — Mapping existence.** Verify existence of all extension and GSMD folders listed in §2 for **M01…M20**.

**Rule 4.2 — Snapshot schema fields.** Validate presence of **all** fields in §3.2 for every `.../v1/snapshot.json`.

**Rule 4.3 — Messages keys.** Assert `messages.problems`, `messages.status_pill`, `messages.cards` in all `messages/v1/snapshot.json` (per module).

**Rule 4.4 — Receipts schema keys.** Assert `receipts.required` and `receipts.optional` in all `receipts_schema/v1/snapshot.json` (per module).

**Rule 4.5 — Version matches.** Check `schema_version == "1.0.0"` and `version.major == 1` for all snapshots.

**Rule 4.6 — KID format.** Check `kid` contains `"ed25519"` in all snapshots.

**Rule 4.7 — Evaluation points type.** Check `evaluation_points` is a list for all snapshots.

---

## 5. Category Listing (Descriptive Only)

The following category names exist across modules (for navigation only, no normative effect):  
`alignment_rules, checklist, conflict_predictors, coverage_packs, cross_module_policies, evidence_map, gate_rules, gs_catalog, knowledge_signals, legacy_triggers, merge_gates, messages, metrics_definitions, nudge_rules, observability, overrides, receipts_schema, release_gates, release_triggers, reporting_policies, risk_model, roi_views, rollback_requirements, rollout, slo_safety, trend_rules, triggers, verification_rules`.

---

## 6. Change Management (Deterministic)

**Rule 6.1 — Adding a module.** Create both folders per §2, add `messages` and `receipts_schema` snapshots with required keys, add any additional categories as needed, and pass **all** CI checks in §4.

**Rule 6.2 — Removing a module.** Remove both folders per §2 and update any mapping enumerations accordingly.

---

**End of Constitution.**