# Rule Definition Discrepancy Analysis Report

**Analysis Date:** Based on current file contents  
**Files Analyzed:**
- `docs/constitution/MODULES AND GSMD MAPPING RULES.json`
- `docs/constitution/GSMD AND MODULE MAPPING RULES.json`

---

## 1. CRITICAL: Duplicate Rule IDs with Different Definitions

### STR-001 (DUPLICATE - CONFLICTING DEFINITIONS)

**MODULES FILE (2024-01-01):**
- **Title:** "Enforce One-to-One Module↔Folder Binding"
- **Category:** Structural Mapping
- **Description:** "For each module code MXX, bind exactly one extension folder and exactly one GSMD folder to that code."
- **Requirements:** Empty array `[]`
- **Policy Linkage:** `["POL-MOD-GSMD-1.0"]`
- **Validation:** "Automated checks verify compliance with stated requirements."

**GSMD FILE (2024-06-15):**
- **Title:** "Enforce Module-Folder Binding"
- **Category:** Structural Mapping
- **Description:** "Specifies exact folder paths for each module code (M01–M20) in both VS Code extension and GSMD directories."
- **Requirements:** 
  - "Each M01-M20 MUST map to exactly one VS Code extension folder"
  - "Each M01-M20 MUST map to exactly one GSMD folder"
  - "Folder paths MUST match canonical mapping exactly"
- **Policy Linkage:** `["POL-STR-001"]`
- **Validation:** "Automated check verifies folder existence against canonical mapping."

**DISCREPANCIES:**
1. **Title:** Different wording ("One-to-One Module↔Folder Binding" vs "Module-Folder Binding")
2. **Description:** Different phrasing and specificity
3. **Requirements:** MODULES file has empty requirements array; GSMD file has 3 detailed requirements
4. **Update Date:** MODULES is older (2024-01-01) vs GSMD is newer (2024-06-15)
5. **Policy Linkage:** Different policy IDs (unified policy vs individual policy)

---

### STR-002 (DUPLICATE - CONFLICTING DEFINITIONS)

**MODULES FILE (2024-01-01):**
- **Title:** "Use Module Code as Authoritative Primary Key"
- **Category:** Structural Mapping
- **Description:** "Treat module code (M01…M20) as the sole authoritative identifier for joins/lookups across tools, folders, and snapshots."
- **Requirements:** Empty array `[]`
- **Policy Linkage:** `["POL-MOD-GSMD-1.0"]`
- **Validation:** "Automated checks verify compliance with stated requirements."

**GSMD FILE (2024-06-15):**
- **Title:** "Enforce Module Code as Primary Key"
- **Category:** Identifier Authority (DIFFERENT CATEGORY)
- **Description:** "Establishes module code (M01–M20) as primary identifier for all folder bindings."
- **Requirements:**
  - "Module code MUST be used as primary identifier for all folder bindings"
  - "No alternative identifiers may supersede module codes"
- **Policy Linkage:** `["POL-STR-002"]`
- **Validation:** "Automated check verifies module code consistency across mappings."

**DISCREPANCIES:**
1. **Title:** "Use...as Authoritative" vs "Enforce...as"
2. **Category:** "Structural Mapping" vs "Identifier Authority"
3. **Description:** Different scope ("joins/lookups across tools, folders, and snapshots" vs "all folder bindings")
4. **Requirements:** MODULES has none; GSMD has 2 requirements
5. **Update Date:** MODULES is older (2024-01-01) vs GSMD is newer (2024-06-15)
6. **Policy Linkage:** Different policy IDs

---

## 2. Semantic Overlaps (Same Topic, Different Rule IDs)

### Core Snapshot Files Requirement

**MODULES FILE:**
- **SCH-001:** "Require Core Snapshot Files"
- **Category:** Schema Requirements
- **Description:** "Each GSMD module MUST contain: `messages/v1/snapshot.json` with `messages.problems`, `messages.status_pill`, `messages.cards` • `receipts_schema/v1/snapshot.json` with `receipts.required`, `receipts.optional`"
- **Requirements:** Empty array

**GSMD FILE:**
- **INV-001:** "Require Core Snapshot Files"
- **Category:** Content Validation
- **Description:** "Requires specific snapshot files with defined key structures for each module."
- **Requirements:**
  - "Every module MUST provide `messages/v1/snapshot.json` with `problems`, `status_pill`, `cards` keys"
  - "Every module MUST provide `receipts_schema/v1/snapshot.json` with `required` and `optional` keys"

**DISCREPANCY:** Same topic, different rule IDs (SCH-001 vs INV-001), different categories, GSMD file has explicit requirements array.

---

### Snapshot Schema Completeness

**MODULES FILE:**
- **SCH-002:** "Require Top-Level Fields in All Snapshots"
- **Category:** Schema Requirements
- **Description:** "Every `.../v1/snapshot.json` MUST include all required top-level fields defined in the Constitution."
- **Requirements:** Empty array

**GSMD FILE:**
- **INV-002:** "Enforce Snapshot Schema Completeness"
- **Category:** Schema Requirements
- **Description:** "Mandates all top-level fields in every snapshot JSON file."
- **Requirements:** Lists 18 specific fields: `snapshot_id`, `module_id`, `slug`, `version`, `schema_version`, `policy_version_ids`, `snapshot_hash`, `signature`, `kid`, `effective_from`, `evaluation_points`, `messages`, `rollout`, `observability`, `privacy`, `evidence`, `receipts`, `tests`

**DISCREPANCY:** Same topic, different rule IDs (SCH-002 vs INV-002), GSMD file provides explicit field list.

---

### Version Constraints

**MODULES FILE:**
- **SCH-003:** "Enforce Snapshot Versioning"
- **Category:** Schema Requirements
- **Description:** "`schema_version` MUST equal \"1.0.0\" and `version.major` MUST equal `1`."
- **Requirements:** Empty array

**GSMD FILE:**
- **INV-003:** "Enforce Version Constraints"
- **Category:** Version Compliance (DIFFERENT CATEGORY)
- **Description:** "Specifies versioning constraints for schema and major versions."
- **Requirements:**
  - "`schema_version` MUST equal \"1.0.0\""
  - "`version.major` MUST equal 1"

**DISCREPANCY:** Same topic, different rule IDs (SCH-003 vs INV-003), different categories, GSMD has explicit requirements.

---

### Policy Version ID Cardinality

**MODULES FILE:**
- **SCH-004:** "Enforce Single Policy Version ID"
- **Category:** Schema Requirements
- **Description:** "`policy_version_ids` MUST be an array of length 1."
- **Requirements:** Empty array

**GSMD FILE:**
- **INV-004:** "Enforce Policy Linkage Cardinality"
- **Category:** Relationship Cardinality (DIFFERENT CATEGORY)
- **Description:** "Requires policy_version_ids to be array of length 1."
- **Requirements:** "`policy_version_ids` MUST be array of length 1"

**DISCREPANCY:** Same topic, different rule IDs (SCH-004 vs INV-004), different categories.

---

### KID Format

**MODULES FILE:**
- **SCH-005:** "Enforce KID Format ("ed25519")"
- **Category:** Schema Requirements
- **Description:** "`kid` MUST contain the substring \"ed25519\"."
- **Requirements:** Empty array

**GSMD FILE:**
- **INV-005:** "Enforce Key Identifier Format"
- **Category:** Security (DIFFERENT CATEGORY)
- **Description:** "Mandates KID must contain \"ed25519\" substring."
- **Requirements:** "`kid` field MUST contain \"ed25519\" substring"

**DISCREPANCY:** Same topic, different rule IDs (SCH-005 vs INV-005), different categories (Schema Requirements vs Security).

---

### Evaluation Points Type

**MODULES FILE:**
- **SCH-006:** "Enforce Evaluation Points List Type"
- **Category:** Schema Requirements
- **Description:** "`evaluation_points` MUST be a list/array."
- **Requirements:** Empty array

**GSMD FILE:**
- **INV-006:** "Enforce Evaluation Points Structure"
- **Category:** Data Structure (DIFFERENT CATEGORY)
- **Description:** "Requires evaluation_points to be list data structure."
- **Requirements:** "`evaluation_points` MUST be a list"

**DISCREPANCY:** Same topic, different rule IDs (SCH-006 vs INV-006), different categories.

---

### Module Addition Procedure

**MODULES FILE:**
- **LCM-001:** "Add Module Procedure"
- **Category:** Lifecycle Management
- **Description:** "To add a module: create both canonical folders (STR-003/STR-004); add required snapshots and keys (SCH-001…SCH-006); then pass all CI checks (VAL-001…VAL-007)."
- **Requirements:** Empty array
- **References:** STR-003, STR-004, SCH-001 through SCH-006, VAL-001 through VAL-007

**GSMD FILE:**
- **CHG-001:** "Enforce Module Addition Procedure"
- **Category:** Change Management
- **Description:** "Specifies standardized procedure for adding new modules."
- **Requirements:**
  - "Create both extension and GSMD folders per canonical mapping"
  - "Add messages and receipts_schema snapshots with required keys"
  - "Pass all automated checks"

**DISCREPANCY:** Same topic, different rule IDs (LCM-001 vs CHG-001), different categories, MODULES file references specific rule IDs that may not exist in GSMD file.

---

### Module Removal Procedure

**MODULES FILE:**
- **LCM-002:** "Remove Module Procedure"
- **Category:** Lifecycle Management
- **Description:** "To remove a module: delete both canonical folders; update any enumerations/mappings; re-run CI to ensure no dangling references (VAL-001)."
- **Requirements:** Empty array
- **References:** VAL-001

**GSMD FILE:**
- **CHG-002:** "Enforce Module Removal Procedure"
- **Category:** Change Management
- **Description:** "Specifies standardized procedure for removing modules."
- **Requirements:**
  - "Remove both extension and GSMD folders"
  - "Update mapping enumerations"
  - "Clean up all references"

**DISCREPANCY:** Same topic, different rule IDs (LCM-002 vs CHG-002), different categories.

---

## 3. Rules Exclusively in MODULES File

1. **STR-003:** "Require Extension Folder Path" - Not in GSMD file
2. **STR-004:** "Require GSMD Folder Path" - Not in GSMD file
3. **VAL-001 through VAL-007:** Seven CI validation rules - Not in GSMD file

**Note:** The GSMD file's STR-001 may cover STR-003/STR-004 concepts but doesn't explicitly define them as separate rules.

---

## 4. Rules Exclusively in GSMD File

All rules in GSMD file (INV-001 through INV-006, CHG-001, CHG-002) have semantic equivalents or overlaps in MODULES file, but with different rule IDs and categories.

---

## 5. Structural Discrepancies

### Requirements Field Usage

- **MODULES FILE:** All 19 rules have empty `requirements` arrays `[]`
- **GSMD FILE:** All 10 rules have populated `requirements` arrays with explicit requirements

**Impact:** MODULES file relies on descriptions for requirements; GSMD file has explicit, structured requirements.

### Category System

- **MODULES FILE:** Uses 4 categories:
  - Structural Mapping
  - Schema Requirements
  - CI / Automated Validation
  - Lifecycle Management

- **GSMD FILE:** Uses 9 categories:
  - Structural Mapping
  - Identifier Authority
  - Content Validation
  - Schema Requirements
  - Version Compliance
  - Relationship Cardinality
  - Security
  - Data Structure
  - Change Management

### Policy Linkage System

- **MODULES FILE:** All rules linked to unified policy `["POL-MOD-GSMD-1.0"]`
- **GSMD FILE:** Each rule linked to individual policy ID (e.g., `["POL-STR-001"]`, `["POL-INV-001"]`)

### Update Dates

- **MODULES FILE:** All rules last updated `2024-01-01T00:00:00Z`
- **GSMD FILE:** All rules last updated `2024-06-15T14:30:00Z` (newer)

---

## 6. Summary of Discrepancies

### Critical Issues:
1. **Duplicate Rule IDs:** STR-001 and STR-002 exist in both files with conflicting definitions
2. **Semantic Duplicates:** 6+ rules cover the same topics but with different IDs (SCH-001 vs INV-001, SCH-002 vs INV-002, etc.)
3. **Cross-References:** LCM-001 in MODULES file references rule IDs (STR-003, STR-004, SCH-001 through SCH-006, VAL-001 through VAL-007) that don't exist in GSMD file

### Definition Quality Differences:
1. **Requirements Field:** MODULES file has empty requirements arrays; GSMD file has explicit requirements
2. **Category Granularity:** GSMD file uses more specific categories (9 vs 4)
3. **Specificity:** GSMD file provides more detailed, explicit requirements

### Consistency Issues:
1. **Policy Linkage:** Unified policy in MODULES vs individual policies in GSMD
2. **Update Dates:** All rules in MODULES are older; all rules in GSMD are newer
3. **Validation Text:** Slight differences in wording

---

## 7. Impact Assessment

When both files are loaded by `rule_count_loader.py`:
- **Duplicate rule_ids** (STR-001, STR-002) will be loaded twice, causing conflicts
- **Semantic duplicates** create confusion about which rule is authoritative
- **Cross-references** in LCM-001 may fail if GSMD file is used exclusively
- **Inconsistent definitions** make it unclear which version of a rule should be enforced

---

**END OF REPORT**

