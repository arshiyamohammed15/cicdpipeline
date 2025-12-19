# ZeroUI — Modules Mapping & GSMD Guide (Deterministic)

> **Scope:** This file maps **module codes** (M01–M20) to their **VS Code extension folders** and **GSMD snapshot folders**, and records verifiable facts about `gsmd/`. It incorporates the validated architectural rules from `architecture-vscode-modular-extension.md` and the strictly factual review of `ZeroUI2.0/gsmd`.
>
> **⚠️ IMPORTANT**: The authoritative module categorization system is defined in **[ZeroUI Module Categories V 3.0](./ZeroUI%20Module%20Categories%20V%203.0.md)**. This mapping document provides technical folder mappings for implementation purposes, but module categories (FM/PM/EPC/CCP) are defined in the V 3.0 document.
>
> **No assumptions.** Everything here is derived from the attached architecture document and the contents of `ZeroUI2.0.zip` exactly as inspected.

---

## 1) Deterministic fingerprints (for reproducibility)

- Inspected subtree: `ZeroUI2.0/gsmd`
- File count (recursive): **176**
- Total bytes: **385,206**
- Tree fingerprint (SHA-256 over `relative-path:size`):
  `d0ec1b4e0da4e60a52c67011aff3c794462d2eba6ed352810774e37e56fdc67e`

Re-running the same scan over the same archive yields the same values.

---

## 2) Canonical module mapping (codes → names → folders)

> **⚠️ SINGLE SOURCE OF TRUTH**: Module categorization and implementation locations are defined in **[ZeroUI Module Categories V 3.0](./ZeroUI%20Module%20Categories%20V%203.0.md)**. This section provides only GSMD folder mappings for the legacy M01-M20 codes used in GSMD snapshots.

**Single extension artifact** with per-module folders under `src/vscode-extension/modules/` (verified file system paths).
**GSMD module snapshots** live under `gsmd/gsmd/modules/` (from the archive layout).

| Code | Module name | VS Code folder (verified path) | GSMD folder |
|---|---|---|---|
| M01 | MMM Engine | `src/vscode-extension/modules/m01-mmm-engine/` | `gsmd/gsmd/modules/M01/` |
| M02 | Cross-Cutting Concern Services | `src/vscode-extension/modules/m02-cross-cutting-concern-services/` | `gsmd/gsmd/modules/M02/` |
| M03 | Release Failures & Rollbacks | `src/vscode-extension/modules/m03-release-failures-rollbacks/` | `gsmd/gsmd/modules/M03/` |
| M04 | Signal Ingestion & Normalization | `src/vscode-extension/modules/m04-signal-ingestion-normalization/` | `gsmd/gsmd/modules/M04/` |
| M05 | Detection Engine Core | `src/vscode-extension/modules/m05-detection-engine-core/` | `gsmd/gsmd/modules/M05/` |
| M06 | Working Safely with Legacy Systems | `src/vscode-extension/modules/m06-legacy-systems-safety/` | `gsmd/gsmd/modules/M06/` |
| M07 | Technical Debt Accumulation | `src/vscode-extension/modules/m07-technical-debt-accumulation/` | `gsmd/gsmd/modules/M07/` |
| M08 | Merge Conflicts & Delays | `src/vscode-extension/modules/m08-merge-conflicts-delays/` | `gsmd/gsmd/modules/M08/` |
| M09 | Compliance & Security Challenges | `src/vscode-extension/modules/m09-compliance-security-challenges/` | `gsmd/gsmd/modules/M09/` |
| M10 | Integration Adapters | `src/vscode-extension/modules/m10-integration-adapters/` | `gsmd/gsmd/modules/M10/` |
| M11 | Feature Development Blind Spots | `src/vscode-extension/modules/m11-feature-dev-blind-spots/` | `gsmd/gsmd/modules/M11/` |
| M12 | Knowledge Silo Prevention | `src/vscode-extension/modules/m12-knowledge-silo-prevention/` | `gsmd/gsmd/modules/M12/` |
| M13 | Monitoring & Observability Gaps | `src/vscode-extension/modules/m13-monitoring-observability-gaps/` | `gsmd/gsmd/modules/M13/` |
| M14 | Client Admin Dashboard | `src/vscode-extension/modules/m14-client-admin-dashboard/` | `gsmd/gsmd/modules/M14/` |
| M15 | Product Success Monitoring | `src/vscode-extension/modules/m15-product-success-monitoring/` | `gsmd/gsmd/modules/M15/` |
| M16 | ROI Dashboard | `src/vscode-extension/modules/m16-roi-dashboard/` | `gsmd/gsmd/modules/M16/` |
| M17 | Gold Standards | `src/vscode-extension/modules/m17-gold-standards/` | `gsmd/gsmd/modules/M17/` |
| M18 | Knowledge Integrity & Discovery | `src/vscode-extension/modules/m18-knowledge-integrity-discovery/` | `gsmd/gsmd/modules/M18/` |
| M19 | Reporting | `src/vscode-extension/modules/m19-reporting/` | `gsmd/gsmd/modules/M19/` |
| M20 | QA & Testing Deficiencies | `src/vscode-extension/modules/m20-qa-testing-deficiencies/` | `gsmd/gsmd/modules/M20/` |

**Rule:** These mappings are for GSMD folder navigation only. For module categorization (FM/PM/EPC/CCP) and cloud service implementations, see **[ZeroUI Module Categories V 3.0](./ZeroUI%20Module%20Categories%20V%203.0.md)**.

---

## 3) GSMD — verified facts (strict)

- **Modules present:** 20 (`M01`…`M20`).
- **Snapshot files:** 170 total (`.../v1/snapshot.json` across modules/categories).
- **Schema/version fields (across all snapshots):**
  - `schema_version` = `"1.0.0"`
  - `version.major` = `1`
  - `policy_version_ids` length = `1`
  - `kid` contains `"ed25519"` in all snapshots
  - `evaluation_points` is a **list** in all snapshots

- **Uniform sections (present in 20/20 modules):**
  - `messages/v1/snapshot.json` contains a `messages` object with keys: `problems`, `status_pill`, `cards`.
  - `receipts_schema/v1/snapshot.json` contains a `receipts` object with keys: `required`, `optional`.

- **Category coverage (number of modules providing the category):**
  - High-frequency (≥13 modules):
    - `messages` (20), `receipts_schema` (20), `evidence_map` (15),
      `checklist` (14), `gate_rules` (14), `observability` (14), `overrides` (14),
      `risk_model` (14), `rollout` (14), `triggers` (13).
  - Unique to one module (exactly 1):
    - `alignment_rules (M17)`, `conflict_predictors (M08)`, `coverage_packs (M13)`, `cross_module_policies (M20)`,
      `gs_catalog (M17)`, `knowledge_signals (M18)`, `legacy_triggers (M06)`, `merge_gates (M08)`,
      `metrics_definitions (M15)`, `nudge_rules (M18)`, `release_gates (M03)`, `release_triggers (M03)`,
      `reporting_policies (M14)`, `roi_views (M19)`, `rollback_requirements (M03)`, `slo_safety (M20)`,
      `trend_rules (M15)`, `verification_rules (M13)`.

---

## 4) Minimal invariants for every snapshot.json (observed)

Every `.../v1/snapshot.json` inspected includes the following **top-level fields** (presence verified across the 170 snapshots):
- `snapshot_id`, `module_id`, `slug`, `version`, `schema_version`, `policy_version_ids`,
- `snapshot_hash`, `signature`, `kid`, `effective_from`,
- `evaluation_points`, `messages`, `rollout`, `observability`, `privacy`, `evidence`, `receipts`, `tests`

> This list reflects actual presence in the current archive; it is not an extrapolation.

---

## 5) Enforcement rules (derived from verified facts & architecture)

These rules keep the **extension mapping** and **GSMD** content aligned and valid.

### 5.1 Mapping & structure
- For each code `MXX`, the extension folder **MUST** exist at: `src/modules/mXX-<slug>/` (slugs as in §2).
- For each code `MXX`, the GSMD folder **MUST** exist at: `gsmd/gsmd/modules/MXX/`.

### 5.2 GSMD snapshot invariants
- Each GSMD module **MUST** contain `messages/v1/snapshot.json` with `messages.problems`, `messages.status_pill`, `messages.cards`.
- Each GSMD module **MUST** contain `receipts_schema/v1/snapshot.json` with `receipts.required`, `receipts.optional`.
- Every `.../v1/snapshot.json` **MUST** include all fields listed in §4.
- `schema_version` **MUST** equal `"1.0.0"`.
- `version.major` **MUST** equal `1`.
- `policy_version_ids` **MUST** be an array of length **1**.
- `kid` **MUST** contain the string `"ed25519"`.
- `evaluation_points` **MUST** be a list.

### 5.3 CI checks (deterministic)
1. **Folder mapping check:** verify the existence of folders in §2 for all M01…M20.
2. **Snapshot schema check:** validate required fields in §4 for all `.../v1/snapshot.json`.
3. **Messages check:** ensure `problems`, `status_pill`, `cards` keys exist for all `messages/v1/snapshot.json`.
4. **Receipts schema check:** ensure `required` and `optional` keys exist for all `receipts_schema/v1/snapshot.json`.
5. **Versioning check:** assert `schema_version == "1.0.0"` and `version.major == 1` for all snapshots.
6. **Key format check:** assert `kid` contains `"ed25519"` for all snapshots.
7. **Evaluation list check:** assert `evaluation_points` is a list for all snapshots.

> All checks above are exact matches to what the current repository already satisfies, based on inspection.

---

## 6) Notes on category coverage (for navigation)

This section is **descriptive** only (no requirements implied). Categories seen across modules:
`alignment_rules, checklist, conflict_predictors, coverage_packs, cross_module_policies, evidence_map, gate_rules, gs_catalog, knowledge_signals, legacy_triggers, merge_gates, messages, metrics_definitions, nudge_rules, observability, overrides, receipts_schema, release_gates, release_triggers, reporting_policies, risk_model, roi_views, rollback_requirements, rollout, slo_safety, trend_rules, triggers, verification_rules`

Use this as a directory guide when navigating `gsmd/gsmd/modules/MXX/*/v1/snapshot.json`.

---

## 7) Change management (deterministic)

- **Adding a module:** create both folders per §2, add `messages` and `receipts_schema` snapshots with required keys, add other category snapshots as needed, and pass CI checks in §5.3.
- **Removing a module:** remove both folders per §2 and update any mapping references that enumerate all modules.

---

**End of file.**
