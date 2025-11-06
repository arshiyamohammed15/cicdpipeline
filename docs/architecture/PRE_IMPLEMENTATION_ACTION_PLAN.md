# Pre-Implementation Action Plan
## Recommended Next Steps Before Functional Modules Implementation

**Based On**: `TRIPLE_ANALYSIS_REPORT.md` findings  
**Date**: 2025-01-27  
**Methodology**: Factual analysis only, no assumptions

---

## EXECUTIVE SUMMARY

**Status**: ❌ **NOT READY** for Functional Modules Implementation

**Blockers Identified**: 18 critical items must be resolved before implementation can begin.

**Recommended Approach**: Complete all Phase 1 items (Critical Blockers) before starting any functional module implementation.

---

## PHASE 1: CRITICAL BLOCKERS (MUST COMPLETE FIRST)

### Priority 1.1: Resolve Architecture Contradictions

**Status**: ❌ **BLOCKING** - Cannot implement with conflicting specifications

#### 1.1.1 VS Code Extension Directory Structure Contradiction

**Issue**: Two different structures documented
- **Option A**: `src/modules/mXX-<slug>/` (from `architecture-vscode-modular-extension.md`)
- **Option B**: `src/vscode-extension/ui/<module-name>/` (from `zeroui-hla.md`, `vs-code-extension-architecture.md`)

**Action Required**:
1. Choose one structure (recommend Option A per `architecture-vscode-modular-extension.md` as it's more detailed)
2. Update all 5 documents referencing extension structure:
   - `zeroui-hla.md`
   - `zeroui-lla.md`
   - `vs-code-extension-architecture.md`
   - `MODULE_IMPLEMENTATION_GUIDE.md`
   - `architecture-vscode-modular-extension.md`

**Verification**: All documents reference same structure

#### 1.1.2 Module Implementation Pattern Contradiction

**Issue**: Two different implementation patterns documented
- **Option A**: Manifest-based (`module.manifest.json` + `registerModule()`) from `architecture-vscode-modular-extension.md`
- **Option B**: Interface-based (`ExtensionInterface.ts` pattern) from `MODULE_IMPLEMENTATION_GUIDE.md`

**Action Required**:
1. Choose one pattern (recommend Option A per `architecture-vscode-modular-extension.md` as it's VS Code-specific)
2. Update `MODULE_IMPLEMENTATION_GUIDE.md` to match chosen pattern
3. Remove conflicting examples

**Verification**: Single implementation pattern documented

#### 1.1.3 OpenAPI/Schema Location Path Mismatch

**Issue**: Architecture documents reference `docs/architecture/openapi/` and `docs/architecture/schemas/` but actual files exist in `contracts/`

**Action Required**:
1. **Option A**: Move all OpenAPI specs from `contracts/<module>/openapi/` to `docs/architecture/openapi/`
2. **Option B**: Update all architecture documents to reference `contracts/` paths
3. **Recommended**: Option B (keep existing structure, update docs)

**Files to Update**:
- `ZeroUI_Architecture_V0_converted.md` (lines 461-473, 499, 533, 623, 676-681)
- `scripts/ci/verify_architecture_artifacts.py` (lines 16-24)
- Any other documents referencing these paths

**Verification**: All references point to actual file locations

---

### Priority 1.2: Create Missing Critical Artifacts

**Status**: ❌ **BLOCKING** - Required for implementation

#### 1.2.1 Gate Tables (CRITICAL - Completely Missing)

**Issue**: 0 CSV files found. Required for deterministic gate decisions.

**Action Required**:
1. Create `docs/architecture/gate_tables/` directory
2. Create `docs/architecture/gate_tables/README.md` (lists all gates)
3. Create at minimum `docs/architecture/gate_tables/gate_pr_size.csv` with rubric rows
4. Define CSV format specification (columns, data types, validation rules)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 475-479, 503, 537, 627, 683-684

**Verification**: At least one gate table CSV exists and is parseable

#### 1.2.2 Trust & Security Documentation

**Action Required**:
1. Create `docs/architecture/trust/` directory
2. Create `docs/architecture/trust/signing_process.md` (who signs, where)
3. Create `docs/architecture/trust/verify_path.md` (how verify happens in each plane)
4. Create `docs/architecture/trust/crl_rotation.md` (rotation & revocation plan)
5. Create `docs/architecture/trust/public_keys/` directory
6. Create `docs/architecture/trust/public_keys/README.md` (point to real public keys by KID)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 481-487, 505, 539, 629, 686-690

**Verification**: All 4 trust documentation files exist

#### 1.2.3 SLO Definitions

**Action Required**:
1. Create `docs/architecture/slo/` directory
2. Create `docs/architecture/slo/slos.md` (targets per service/surface)
3. Create `docs/architecture/slo/alerts.md` (alert rules, throttle, auto-quieting)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 489-493, 507, 541, 631, 692-693

**Verification**: Both SLO files exist with stub content

#### 1.2.4 Policy Artifacts

**Action Required**:
1. Create `docs/architecture/policy/` directory
2. Create `docs/architecture/policy/policy_snapshot_v1.json` (seed artifact)
3. Create `docs/architecture/policy/rollback.md` (how to roll back bad policy)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 517, 545, 607, 635, 695-696

**Verification**: Policy snapshot JSON exists and is valid JSON

#### 1.2.5 Sample Artifacts

**Action Required**:
1. Create `docs/architecture/samples/` directory
2. Create `docs/architecture/samples/receipts/` directory
3. Create `docs/architecture/samples/receipts/receipts_example.jsonl` (2-3 lines)
4. Create `docs/architecture/samples/evidence/` directory
5. Create `docs/architecture/samples/evidence/evidence_pack_example.json`

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 521, 523, 611, 613, 698-701

**Verification**: Sample files exist and are valid JSON/JSONL

---

### Priority 1.3: Create Core Schemas (If Not Using contracts/)

**Status**: ⚠️ **CONDITIONAL** - Only if choosing Option A in 1.1.3

**Action Required** (if moving schemas to `docs/architecture/schemas/`):
1. Create `docs/architecture/schemas/` directory
2. Create `docs/architecture/schemas/decision_receipt.schema.json`
3. Create `docs/architecture/schemas/policy_snapshot.schema.json`
4. Create `docs/architecture/schemas/evidence_pack.schema.json`

**Note**: If keeping schemas in `contracts/`, skip this and update references only.

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 467-473, 501, 535, 625, 679-681

---

### Priority 1.4: Create Operational Documentation

**Action Required**:
1. Create `docs/architecture/ops/` directory
2. Create `docs/architecture/ops/runbooks.md` (top 3 incident playbooks:
   - Receipt not written
   - Gate blocks all PRs
   - Policy fetch fails)
3. Create `docs/architecture/ops/branching.md` (trunk + small PRs model)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 547, 637, 653, 703-704

**Verification**: Both ops files exist

---

### Priority 1.5: Create Development Documentation

**Action Required**:
1. Create `docs/architecture/dev/` directory
2. Create `docs/architecture/dev/standards.md` (coding standards)
3. Create `docs/architecture/dev/quickstart_windows.md` (Windows-first commands)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 569, 571, 659, 661, 706-707

**Verification**: Both dev files exist

---

### Priority 1.6: Create Security Documentation

**Action Required**:
1. Create `docs/architecture/security/` directory
2. Create `docs/architecture/security/rbac.md` (who can do what)
3. Create `docs/architecture/security/data_classes.md` (what's in receipts/evidence)
4. Create `docs/architecture/security/privacy_note.md` (metadata-only stance)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 575, 577, 579, 665, 667, 669, 709-711

**Verification**: All 3 security files exist

---

### Priority 1.7: Create Testing Infrastructure

**Action Required**:
1. Create `docs/architecture/tests/` directory
2. Create `docs/architecture/tests/test_plan.md` (test matrix: unit, integration, e2e)
3. Create `docs/architecture/tests/golden/` directory (for golden test data)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 551, 553, 641, 643, 713-714

**Verification**: Test plan exists, golden directory exists

---

### Priority 1.8: Create CI/CD Infrastructure

**Action Required**:
1. Create root-level `Jenkinsfile` (lint → tests → build → export diagrams → package artifacts)

**Reference**: `ZeroUI_Architecture_V0_converted.md` line 649

**Verification**: Jenkinsfile exists at repository root

---

## PHASE 2: ARCHITECTURE DIAGRAMS (RECOMMENDED BEFORE IMPLEMENTATION)

**Status**: ⚠️ **RECOMMENDED** - Not blocking but highly recommended

### 2.1 Baseline Architecture Diagrams

**Action Required**: Create 10 baseline diagrams in `docs/architecture/`:

1. `01_context.mmd` - System Context (C4-L0)
2. `02_planes_containers.mmd` - Planes & Containers (C4-L1)
3. `03_deployment_envs.mmd` - Deployment & Environment Ladder
4. `04_e2e_t0t1t2.puml` - Core E2E Sequence (T0/T1/T2)
5. `05_data_privacy_split.mmd` - Data & Privacy Split (DFD + Lineage)
6. `06_policy_lifecycle.mmd` - Policy Lifecycle & Registry (State Machine)
7. `07_gate_fsm.mmd` - Gate Decision FSM (per Gate)
8. `08_trust_keys.mmd` - Trust & Key/Attestation Flow
9. `09_observability_slo.mmd` - Observability & SLO Topology
10. `10_storage_retention.mmd` - Storage & Retention Map

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 371-411, 439-459

**Verification**: All 10 diagram files exist

### 2.2 Exports Directory

**Action Required**:
1. Create `docs/architecture/exports/` directory (for SVG/PDF renders)

**Reference**: `ZeroUI_Architecture_V0_converted.md` lines 509, 555, 645, 715

**Verification**: Exports directory exists

---

## PHASE 3: HARDENING MEASURES (RECOMMENDED)

**Status**: ⚠️ **RECOMMENDED** - Documented as pending but not blocking

**Source**: `HARDENING_IMPLEMENTATION_SUMMARY.md` lines 23-113

### 3.1 Trust & Supply-Chain Integrity

**Action Required**:
- Implement signed snapshot verification library
- Implement public key trust store
- Implement CRL/rotation checks

**Status**: ⏳ Pending (requires cryptographic library integration)

### 3.2 Deterministic Gate Decisions

**Action Required**:
- Implement CSV gate table loader
- Create golden test data
- Implement deterministic decision functions

**Status**: ⏳ Pending (requires gate table CSV format definition - see 1.2.1)

### 3.3 Rollback and Override Paths

**Action Required**:
- Implement policy rollback CLI
- Create override documentation
- Implement receipt-based audit trail

**Status**: ⏳ Pending (requires policy registry implementation)

### 3.4 Observability SLO Integration

**Action Required**:
- Integrate OTel metrics/traces
- Implement SLO error budgets
- Integrate IDE alert integration

**Status**: ⏳ Pending (requires observability infrastructure)

### 3.5 Strict API Contracts

**Action Required**:
- Implement OpenAPI spec validation
- Create contract tests
- Implement schema versioning

**Status**: ⏳ Pending (requires OpenAPI specs - see 1.1.3)

---

## PHASE 4: ADR 0001 FOUNDATION (RECOMMENDED)

**Status**: ⚠️ **RECOMMENDED** - ADR is "Proposed", not "Accepted"

**Source**: `adr/0001-foundation-infrastructure.md`

### 4.1 Rule Pipeline Hardening

**Action Required**:
- Implement Markdown extraction routine
- Generate all derived artifacts from Markdown
- Add CI checks for consistency

### 4.2 Toolchain Alignment

**Action Required**:
- Set Python 3.11 as minimum
- Split dependencies (runtime vs dev)
- Maintain single lock file

### 4.3 Testing Pipeline

**Action Required**:
- Remove `--collect-only` from pytest
- Add coverage enforcement
- Add smoke test for zero tests

### 4.4 Packaging Refactor

**Action Required**:
- Remove `sys.path` mutations
- Implement proper Python packaging
- Provide CLI entry point

### 4.5 Pre-commit Updates

**Action Required**:
- Eliminate duplicate hooks
- Replace GNU utilities with cross-platform
- Document prerequisites

### 4.6 Metadata Corrections

**Action Required**:
- Align version numbers
- Add MIT LICENSE file
- Track ADRs properly

---

## IMPLEMENTATION READINESS CHECKLIST

### Critical Blockers (Must Complete)

- [ ] **1.1.1** VS Code Extension structure contradiction resolved
- [ ] **1.1.2** Module implementation pattern contradiction resolved
- [ ] **1.1.3** OpenAPI/Schema location path mismatch resolved
- [ ] **1.2.1** Gate tables created (at least one CSV)
- [ ] **1.2.2** Trust documentation created (4 files)
- [ ] **1.2.3** SLO definitions created (2 files)
- [ ] **1.2.4** Policy artifacts created (2 files)
- [ ] **1.2.5** Sample artifacts created (2 files)
- [ ] **1.4** Operational documentation created (2 files)
- [ ] **1.5** Development documentation created (2 files)
- [ ] **1.6** Security documentation created (3 files)
- [ ] **1.7** Testing infrastructure created (1 file + directory)
- [ ] **1.8** CI/CD infrastructure created (Jenkinsfile)

### Recommended (Before Implementation)

- [ ] **2.1** Baseline architecture diagrams created (10 files)
- [ ] **2.2** Exports directory created
- [ ] **3.1-3.5** Hardening measures (5 items, can be done in parallel)
- [ ] **4.1-4.6** ADR 0001 foundation items (6 items, can be done in parallel)

---

## RECOMMENDED SEQUENCE

### Week 1: Resolve Contradictions
1. Day 1-2: Resolve VS Code Extension structure (1.1.1)
2. Day 2-3: Resolve module implementation pattern (1.1.2)
3. Day 3-4: Resolve OpenAPI/Schema location (1.1.3)
4. Day 5: Update all documents, verify consistency

### Week 2: Create Critical Artifacts
1. Day 1: Gate tables (1.2.1) - **CRITICAL**
2. Day 2: Trust documentation (1.2.2)
3. Day 3: SLO definitions (1.2.3)
4. Day 4: Policy artifacts (1.2.4)
5. Day 5: Sample artifacts (1.2.5)

### Week 3: Create Supporting Documentation
1. Day 1: Operational documentation (1.4)
2. Day 2: Development documentation (1.5)
3. Day 3: Security documentation (1.6)
4. Day 4: Testing infrastructure (1.7)
5. Day 5: CI/CD infrastructure (1.8)

### Week 4: Architecture Diagrams (Optional but Recommended)
1. Days 1-5: Create baseline architecture diagrams (2.1)

### Ongoing: Hardening & Foundation (Can Run Parallel)
- Hardening measures (Phase 3) - Can be done in parallel with implementation
- ADR 0001 items (Phase 4) - Can be done in parallel with implementation

---

## VERIFICATION CRITERIA

### Before Starting Functional Modules Implementation

**Must Have**:
- ✅ All Phase 1 items complete (18 critical blockers resolved)
- ✅ All contradictions resolved and documents updated
- ✅ At least one gate table CSV exists and is parseable
- ✅ All trust, SLO, policy, sample artifacts exist
- ✅ All operational, dev, security documentation exists
- ✅ Testing infrastructure exists
- ✅ CI/CD infrastructure exists

**Should Have**:
- ⚠️ Baseline architecture diagrams (10 files)
- ⚠️ Exports directory for diagram renders

**Nice to Have** (Can be done in parallel):
- ⚠️ Hardening measures (Phase 3)
- ⚠️ ADR 0001 foundation (Phase 4)

---

## RISK ASSESSMENT

### High Risk (Block Implementation)
- **Missing Gate Tables**: Cannot implement deterministic gate decisions
- **Unresolved Contradictions**: Will cause implementation conflicts
- **Missing Trust Documentation**: Security implementation cannot proceed

### Medium Risk (Cause Rework)
- **Missing Architecture Diagrams**: May cause misunderstanding during implementation
- **Missing Operational Documentation**: May cause operational issues later

### Low Risk (Can Be Deferred)
- **Hardening Measures**: Can be implemented in parallel
- **ADR 0001 Items**: Can be implemented in parallel

---

## CONCLUSION

**Status**: ❌ **NOT READY** for Functional Modules Implementation

**Minimum Required**: Complete all Phase 1 items (18 critical blockers)

**Estimated Time**: 3 weeks for Phase 1 (critical blockers)

**Recommendation**: **DO NOT START** functional module implementation until all Phase 1 items are complete and verified.

---

**Report Status**: ✅ Complete - Based on factual analysis from `TRIPLE_ANALYSIS_REPORT.md`

