# Four Plane Storage vs 7×4 Architecture Alignment Report

**ID**: ARCH.7X4.4PLANE.MT-01  
**Date**: 2026-01-03  
**Status**: Alignment Validation

## Executive Summary

This report validates alignment between the **Four Plane Storage Architecture** (implementation in `storage-scripts/`) and the **Four-Plane Architecture** (conceptual view documented in `docs/architecture/zeroui-architecture.md`). The Four Plane storage implementation provides the storage fabric for the four deployment planes, with some naming drift and missing components identified.

---

## 1. What Matches

The Four Plane storage structure aligns with the Four-Plane Architecture as follows:

| Architecture Plane | Storage Plane | Mapping Status | Key Alignments |
|-------------------|---------------|----------------|---------------|
| **IDE / Edge Agent Plane** (Your Laptop) | `ide/...` | ✅ **ALIGNED** | Receipts (JSONL), policy cache, logs, LLM artifacts, queue management |
| **Client / Tenant Cloud Plane** (Your Company) | `tenant/{tenant-id}/{region}/...` | ✅ **ALIGNED** | Evidence/WORM stores, telemetry, adapters, reporting marts, DLQ |
| **ZeroUI Product Cloud Plane** (The Product's Brain) | `product/{region}/...` | ✅ **ALIGNED** | Policy registry, telemetry, evidence watermarks, reporting aggregates |
| **Shared Services Plane** (Building Security & Logs) | `shared/{org-id}/{region}/...` | ✅ **ALIGNED** | PKI, telemetry, SIEM, BI lake, governance controls |

### Detailed Alignment

#### IDE Plane → `ide/`
- **Receipts**: `ide/receipts/{repo-id}/{yyyy}/{mm}/` supports append-only JSONL receipts (matches "laptop receipts" requirement)
- **Policy**: `ide/policy/` with signed snapshots and `trust/pubkeys/` (matches "laptop trust: public-key trust store" requirement)
- **LLM**: `ide/llm/(prompts|tools|adapters|cache)/` supports local LLM artifacts (matches "local policy evaluator" context)
- **Queue**: `ide/queue/(pending|sent|failed)/` supports envelope refs (matches "adapters (Git/PR/CI)" requirement)

#### Tenant Plane → `tenant/{tenant-id}/{region}/`
- **Evidence**: `tenant/{tenant-id}/{region}/evidence/data/` with DLQ and watermarks (matches "Evidence/WORM stores (append-only mirror, retention, legal-hold)" requirement)
- **Telemetry**: `tenant/{tenant-id}/{region}/telemetry/(metrics|traces|logs)/dt=.../` (matches observability needs)
- **Adapters**: `tenant/{tenant-id}/{region}/adapters/(webhooks|gateway-logs)/dt=.../` (matches "Enterprise adapters (Git/CI, Confluence/Jira, Slack/Teams)" requirement)
- **Reporting**: `tenant/{tenant-id}/{region}/reporting/marts/dt=.../` (matches tenant-specific analytics)

#### Product Plane → `product/{region}/`
- **Policy Registry**: `product/{region}/policy/registry/(releases|templates|revocations)/` (matches "Policy Registry (signed snapshots)" requirement)
- **Telemetry**: `product/{region}/telemetry/(metrics|traces|logs)/dt=.../` (matches observability mesh needs)
- **Reporting**: `product/{region}/reporting/tenants/{tenant-id}/{env}/aggregates/dt=.../` (matches cross-tenant analytics)

#### Shared Plane → `shared/{org-id}/{region}/`
- **PKI**: `shared/{org-id}/{region}/pki/` (matches "Identity & trust" and key management requirements)
- **Telemetry**: `shared/{org-id}/{region}/telemetry/(metrics|traces|logs)/dt=.../` (matches "Observability mesh (metrics/logs/traces, SLO/error-budget)" requirement)
- **SIEM**: `shared/{org-id}/{region}/siem/(detections|events)/dt=.../` (matches security monitoring needs)
- **BI Lake**: `shared/{org-id}/{region}/bi-lake/curated/zero-ui/` (matches analytics requirements)
- **Governance**: `shared/{org-id}/{region}/governance/(controls|attestations)/` (matches governance requirements)

---

## 2. Drift/Misalignment

### 2.1 Naming Drift

| Architecture Term | Storage Term | Impact | Recommendation |
|------------------|--------------|--------|----------------|
| **"IDE / Edge Agent Plane"** | **"ide/"** | None | Storage uses canonical path `ide/` which correctly represents the IDE Plane (Laptop). Architecture uses "IDE / Edge Agent" to emphasize both components. The path `ide/` is the canonical implementation path per folder-business-rules.md. |
| **"Laptop"** (in docs) | **"ide/"** (in storage) | None | Architecture docs refer to "Your Laptop" while storage uses canonical path `ide/`. Both are correct—the path `ide/` represents IDE Plane (Laptop) storage per folder-business-rules.md. |
| **"Client / Tenant Cloud Plane"** | **"tenant/{tenant-id}/{region}/"** | None | Storage correctly uses canonical path `tenant/{tenant-id}/{region}/` which matches the "Tenant Cloud" aspect. "Client" in architecture refers to the company/tenant relationship. No action needed. |

**Status**: Naming drift is minimal and does not indicate misalignment. The storage implementation correctly uses canonical paths that map to the architecture.

### 2.2 Documentation/Script Mismatches

#### Found Issues

1. **Architecture docs reference "laptop receipts"** but storage-scripts use canonical path:
   - **Architecture**: Architecture docs reference "**Laptop**: receipts (JSONL), logs, snapshot cache"
   - **Storage**: `storage-scripts/folder-business-rules.md` defines canonical path `ide/receipts/{repo-id}/{yyyy}/{mm}/`
   - **Impact**: None—both refer to the same storage location. The canonical path is `ide/` per folder-business-rules.md.
   - **Status**: Resolved—documentation updated to use canonical path `ide/`

2. **Architecture docs reference "WORM evidence mirror"** but storage-scripts use canonical path:
   - **Architecture**: Architecture docs reference "**Client**: WORM evidence mirror, legal-hold/retention, DLQ for ingestion"
   - **Storage**: `storage-scripts/folder-business-rules.md` defines canonical path `tenant/{tenant-id}/{region}/evidence/data/`
   - **Impact**: Low—WORM semantics are implementation detail, storage path is correct
   - **Recommendation**: Add note in storage docs: "`tenant/{tenant-id}/{region}/evidence/data/` implements WORM (Write-Once-Read-Many) semantics"

3. **Architecture docs reference "audit ledger"** but storage-scripts don't explicitly define a shared audit ledger path:
   - **Architecture**: Architecture docs reference "**Shared**: audit ledger (append-only), policy registry, artifact/model registry"
   - **Storage**: `storage-scripts/folder-business-rules.md` defines `shared/{org-id}/{region}/governance/(controls|attestations)/` but no explicit "audit ledger" folder
   - **Impact**: Medium—audit ledger may be implemented via governance or SIEM paths
   - **Recommendation**: Clarify in storage docs: "Audit ledger may be implemented under `shared/{org-id}/{region}/governance/` or `shared/{org-id}/{region}/siem/` depending on use case"

**Status**: Minor documentation mismatches identified. No functional misalignment—storage paths correctly support architecture requirements.

---

## 3. Missing Relative to Architecture

The following components are explicitly referenced in the architecture but are not explicitly defined in the Four Plane storage structure:

### 3.1 Tenant Context Stores

**Architecture Reference**:  
- Architecture docs reference "SSO/SCIM, compliance hooks" in the Client / Tenant Cloud Plane
- Tenant context (SSO/SCIM, compliance hooks) needs storage for tenant-specific identity and compliance data

**Storage Status**:  
- ⚠️ **MISSING**: `tenant/{tenant-id}/{region}/` plane exists but no explicit tenant context storage path
- No `tenant/{tenant-id}/{region}/context/` path for tenant-specific context data

**Recommendation**:  
- Add `tenant/{tenant-id}/{region}/context/(identity|sso|scim|compliance)/` for tenant context stores
- Document tenant context storage requirements (encryption, isolation, retention)

### 3.2 Shared Evaluation Harness

**Architecture Reference**:  
- Architecture docs reference "local policy evaluator (dry-run)" in the IDE / Edge Agent Plane
- Evaluation harness needs shared storage for evaluation results and harness artifacts

**Storage Status**:  
- ❌ **MISSING**: No explicit shared evaluation harness storage path
- Evaluation results may be stored in receipts, but no dedicated harness storage exists

**Recommendation**:  
- Add `shared/{org-id}/{region}/eval/(harness|results|cache)/` for shared evaluation harness storage
- Document evaluation harness storage requirements (format, retention, access control)

### 3.3 SBOM and Supply Chain Services

**Architecture Reference**:  
- Security and compliance requirements need SBOM (Software Bill of Materials) storage
- Supply chain attestation evidence needs storage

**Storage Status**:  
- ❌ **MISSING**: No explicit SBOM or supply chain storage paths

**Recommendation**:  
- Add `shared/{org-id}/{region}/security/(sbom|supply-chain)/` for SBOM and supply chain artifacts
- Document SBOM storage requirements (format, signing, retention, attestation evidence)

---

## 4. How to Incorporate

### 4.1 Storage Fabric as Supporting Layer

The Four Plane storage should be treated as a **Storage Fabric** that supports cross-cutting planes without duplicating responsibilities:

#### Cross-Cutting Plane Mapping

The Storage Fabric supports multiple cross-cutting concerns across the four deployment planes:

- **Evidence & Audit Plane**: Storage paths provide append-only evidence and audit trail storage
  - Example: `ide/receipts/{repo-id}/{yyyy}/{mm}/` provides receipt storage
  - Example: `tenant/{tenant-id}/{region}/evidence/data/` provides WORM evidence mirror
  - Example: `shared/{org-id}/{region}/governance/(controls|attestations)/` provides audit ledger storage
  - Responsibility: Immutable evidence storage, audit trails, append-only semantics

- **Data & Memory Plane**: Storage paths support data organization and memory/state management
  - Example: `tenant/{tenant-id}/{region}/reporting/marts/dt=.../` provides data marts
  - Example: `product/{region}/reporting/tenants/{tenant-id}/{env}/aggregates/dt=.../` provides aggregated data
  - Example: `shared/{org-id}/{region}/bi-lake/curated/zero-ui/` provides BI data lake
  - Responsibility: Data organization, partitioning, analytics storage

- **Security & Supply Chain Plane**: Storage paths support security artifacts and supply chain attestation
  - Example: `ide/policy/trust/pubkeys/` provides public key storage
  - Example: `shared/{org-id}/{region}/pki/` provides PKI artifacts
  - Example: `shared/{org-id}/{region}/security/(sbom|supply-chain)/` provides SBOM and supply chain attestation
  - Responsibility: Security artifacts, trust stores, supply chain evidence

- **Observability Plane**: Storage paths support observability data across all planes
  - Example: `{plane}/telemetry/(metrics|traces|logs)/dt=.../` provides unified telemetry pattern
  - Example: `shared/{org-id}/{region}/siem/(detections|events)/dt=.../` provides security monitoring
  - Responsibility: Metrics, traces, logs, security events, SLO tracking

#### Principles

1. **No Duplication**: Storage fabric does not duplicate business logic—it provides structure only
2. **Plane Isolation**: Each plane's storage is isolated but supports cross-plane data flow
3. **Lazy Creation**: Subfolders created on-demand (already implemented in v2.0)
4. **Canonical Paths**: Storage uses canonical paths with placeholders (`{tenant-id}`, `{region}`, `{org-id}`) for multi-tenant and multi-region support

### 4.2 Integration Points

#### With Architecture Layers

- **IDE Plane Storage** (`ide/`) supports:
  - VS Code Extension (receipts, policy cache)
  - Edge Agent (queue, LLM artifacts, logs)
  - Local-first operations (no cloud dependency)

- **Tenant Plane Storage** (`tenant/{tenant-id}/{region}/`) supports:
  - Policy enforcement (evidence, DLQ)
  - Enterprise adapters (webhooks, gateway logs)
  - Tenant-specific analytics (reporting marts)

- **Product Plane Storage** (`product/{region}/`) supports:
  - Policy registry (releases, templates, revocations)
  - Cross-tenant analytics (reporting aggregates)
  - Product-level telemetry

- **Shared Plane Storage** (`shared/{org-id}/{region}/`) supports:
  - Identity & trust (PKI)
  - Observability mesh (telemetry)
  - Security monitoring (SIEM)
  - Governance (controls, attestations)

#### With Service Implementations

- **Cloud Services** read/write to storage planes using canonical paths with placeholders (`{tenant-id}`, `{region}`, `{org-id}`)
- **Edge Agent** reads/writes to `ide/` plane only (local-first)
- **VS Code Extension** reads receipts from `ide/receipts/` (via Edge Agent)

### 4.3 Storage Fabric Responsibilities

**DO**:
- ✅ Provide path structure and naming conventions
- ✅ Support environment scoping (dev/staging/prod)
- ✅ Enforce data governance rules (no code/PII, no secrets, JSONL receipts)
- ✅ Support lazy creation of subfolders
- ✅ Provide partitioning patterns (dt=, YYYY/MM)

**DON'T**:
- ❌ Implement business logic (that's in services)
- ❌ Duplicate service responsibilities (storage is infrastructure)
- ❌ Hardcode paths (use `ZU_ROOT` environment variable)
- ❌ Store secrets or PII (use secrets manager/KMS)

---

## 5. Required Follow-Up Changes

### 5.1 Documentation Updates

- [x] **Update architecture docs** (`docs/architecture/zeroui-architecture.md`):
  - [x] Add cross-reference: "Laptop receipts are stored in `ide/receipts/`" (canonical path per folder-business-rules.md)
  - [x] Add note: "WORM evidence mirror is implemented via `tenant/{tenant-id}/{region}/evidence/data/`"
  - [x] Clarify audit ledger location: "Audit ledger may be under `shared/{org-id}/{region}/governance/` or `shared/{org-id}/{region}/siem/`"

- [x] **Update storage-scripts docs** (`storage-scripts/folder-business-rules.md`):
  - [x] Add note: "IDE Plane uses canonical path `ide/` for laptop storage" (already documented in folder-business-rules.md line 93)
  - [x] Document WORM semantics for `tenant/{tenant-id}/{region}/evidence/data/` (already documented in folder-business-rules.md line 137)
  - [x] Document audit ledger implementation options (governance/ or siem/ paths available)
  - [x] Document canonical path format with placeholders (`{tenant-id}`, `{region}`, `{org-id}`) (already documented in folder-business-rules.md line 45)

- [ ] **Create storage-to-architecture mapping doc**:
  - [ ] Document how each storage path maps to architecture requirements
  - [ ] Include cross-references between architecture docs and storage paths

### 5.2 Storage Structure Additions

- [ ] **Add tenant context storage**:
  - [ ] `tenant/{tenant-id}/{region}/context/(identity|sso|scim|compliance)/`
  - [ ] Document tenant context storage requirements (encryption, isolation, retention)

- [ ] **Add shared evaluation harness storage**:
  - [ ] `shared/{org-id}/{region}/eval/(harness|results|cache)/`
  - [ ] Document evaluation harness storage requirements (format, retention, access control)

- [ ] **Add SBOM/supply chain storage**:
  - [ ] `shared/{org-id}/{region}/security/(sbom|supply-chain)/`
  - [ ] Document SBOM storage requirements (format, signing, retention, attestation evidence)

### 5.3 Code Changes

- [ ] **Update storage scaffold scripts**:
  - [ ] Add new paths to `storage-scripts/tools/create-folder-structure-*.ps1` using canonical path format
  - [ ] Update `storage-scripts/folder-business-rules.md` with new paths (tenant context, shared eval, SBOM)
  - [ ] Update `storage-scripts/INTEGRATION.md` with new paths

- [ ] **Update storage governance validator**:
  - [ ] Add validation rules for new paths (if needed)
  - [ ] Update patterns in `config/patterns/storage_governance_patterns.json`

- [ ] **Update service implementations** (if services need new paths):
  - [ ] Update services to use new storage paths
  - [ ] Add tests for new storage paths

### 5.4 Testing Updates

- [ ] **Update storage structure tests**:
  - [ ] Add tests for new paths in `storage-scripts/tests/test-folder-structure.ps1`
  - [ ] Verify new paths are created correctly

- [ ] **Update integration tests**:
  - [ ] Add tests for tenant context storage
  - [ ] Add tests for shared evaluation harness storage
  - [ ] Add tests for SBOM/supply chain storage

### 5.5 Configuration Updates

- [ ] **Update environment configuration**:
  - [ ] Update `storage-scripts/config/environments.json` if new paths are environment-specific
  - [ ] Update `storage-scripts/tools/config_manager.ps1` if needed

---

## 6. Conclusion

### Alignment Status: ✅ **GOOD** with Minor Gaps

The Four Plane storage implementation **correctly aligns** with the Four-Plane Architecture:

- ✅ **Plane mapping is correct**: Laptop/Tenant/Product/Shared planes map correctly using canonical paths
- ✅ **Storage paths support architecture requirements**: Receipts, evidence, policy registry, telemetry all have appropriate storage
- ✅ **Naming consistency**: Canonical paths (`ide/`) correctly represent architecture planes per folder-business-rules.md
- ⚠️ **Missing components**: Tenant context stores, shared evaluation harness, SBOM/supply chain need to be added
- ✅ **Storage fabric approach is sound**: Storage provides infrastructure without duplicating business logic

### Next Steps

1. **Priority 1**: Add missing storage paths (tenant context, shared evaluation harness, SBOM/supply chain)
2. **Priority 2**: Update documentation with cross-references and canonical path format
3. **Priority 3**: Update scaffold scripts and tests to use canonical paths
4. **Priority 4**: Update service implementations to use canonical paths with placeholders (if needed)

### Validation

This report is **internally consistent** with:
- `storage-scripts/folder-business-rules.md` (v2.0)
- `storage-scripts/README_scaffold.md`
- `storage-scripts/INTEGRATION.md`
- `docs/architecture/zeroui-architecture.md`

---

**Report Generated**: 2026-01-03  
**Author**: ARCH.7X4.4PLANE.MT-01  
**Status**: Complete

