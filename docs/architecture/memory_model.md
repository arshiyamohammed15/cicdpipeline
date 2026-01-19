# ZeroUI Memory Model

**Status**: Required for Functional Modules Implementation  
**Date**: 2026-01-03  
**Alignment**: 7×4 Architecture, 4-Plane DB Contract, AI Agent/RAG System

## Overview

This document maps all memory types required for ZeroUI's AI agent/RAG system to concrete stores with clear plane ownership and governance rules. All memory types must be mapped before Functional Modules implementation begins.

---

## Memory Types

### 1. Working Memory (AgentState in Graph Runtime)

**Definition**: Runtime state for agent execution context, including tenant/repo/actor identities and current session state.

**Store Mapping**:
- **IDE Plane**: Postgres (`core.tenant`, `core.repo`, `core.actor` tables)
  - **Path**: `zeroui_ide_pg` database, `core` schema
  - **Access**: Edge Agent runtime
  - **Governance**: Local-only, no cloud sync, ephemeral (can be cleared on restart)
- **Tenant Plane**: Postgres (`core.tenant`, `core.repo`, `core.actor` tables)
  - **Path**: `zeroui_tenant_pg` database, `core` schema
  - **Access**: Tenant services
  - **Governance**: Tenant-scoped, ACID transactions, durable
- **Product Plane**: Postgres (`core.tenant`, `core.repo`, `core.actor` tables)
  - **Path**: `zeroui_product_pg` database, `core` schema
  - **Access**: Product services
  - **Governance**: Product-scoped, ACID transactions, durable
- **Shared Plane**: Postgres (`core.tenant`, `core.repo`, `core.actor` tables)
  - **Path**: `zeroui_shared_pg` database, `core` schema
  - **Access**: Shared services
  - **Governance**: Shared-scoped, ACID transactions, durable

**Note**: "Graph Runtime" refers to the core schema tables that maintain tenant/repo/actor relationships. No separate graph database is required; the relational schema serves as the graph structure.

**Evidence**: `infra/db/schema_pack/migrations/pg/001_core.sql`

---

### 2. Episodic Memory (Receipts + BKG Edges)

**Definition**: Historical records of decisions, events, and relationships. Includes signed receipts (append-only) and Background Knowledge Graph (BKG) edges that connect entities.

**Store Mapping**:
- **IDE Plane**: 
  - **Receipts**: JSONL files (`ZU_ROOT/ide/receipts/{repo-id}/{yyyy}/{mm}/`)
  - **Receipt Index**: Postgres (`core.receipt_index` table)
  - **BKG Edges**: Postgres (`core.bkg_edge` table - Phase 0 stub)
  - **Access**: Edge Agent, VS Code Extension
  - **Governance**: Append-only receipts, signed, local-only
- **Tenant Plane**:
  - **Receipts**: JSONL files (`ZU_ROOT/tenant/{tenant-id}/{region}/evidence/data/`)
  - **Receipt Index**: Postgres (`core.receipt_index`, `app.tenant_receipt_index` tables)
  - **BKG Edges**: Postgres (`core.bkg_edge` table - Phase 0 stub)
  - **Access**: Tenant services, evidence indexing service
  - **Governance**: WORM semantics, append-only, tenant-scoped
- **Product Plane**:
  - **Receipt Index**: Postgres (`core.receipt_index` table)
  - **BKG Edges**: Postgres (`core.bkg_edge` table - Phase 0 stub)
  - **Access**: Product services
  - **Governance**: Policy-governed access, product-scoped
- **Shared Plane**:
  - **Receipt Index**: Postgres (`core.receipt_index` table)
  - **BKG Edges**: Postgres (`core.bkg_edge` table - Phase 0 stub)
  - **Access**: Shared services
  - **Governance**: Shared access, no tenant payloads

**BKG Status**: Phase 0 stub (contracts + schema placeholders). Full graph logic not yet implemented.

**Evidence**: 
- Receipts: `storage-scripts/folder-business-rules.md` (line 125, 137)
- Receipt Index: `infra/db/schema_pack/migrations/pg/001_core.sql` (line 27-42)
- BKG Edges: `infra/db/migrations/tenant/002_bkg_phase0.sql` (Phase 0 stub - to be created)

---

### 3. Vector DB Memory (pgvector/embeddings)

**Definition**: Vector embeddings for semantic similarity search, used by Context Service for RAG (Retrieval-Augmented Generation).

**Store Mapping**:
- **IDE Plane**: N/A (no vector DB in IDE plane)
- **Tenant Plane**: N/A (no vector DB in tenant plane)
- **Product Plane**: Postgres (`app.embedding_document`, `app.embedding_vector` tables)
  - **Path**: `zeroui_product_pg` database, `app` schema
  - **Extension**: pgvector (dimension 1536)
  - **Access**: Context Service (via Product services)
  - **Governance**: pgvector extension, HNSW index for similarity search, product-scoped
- **Shared Plane**: N/A (no vector DB in shared plane)

**Evidence**: `infra/db/migrations/product/002_embeddings.sql`, `infra/docker/postgres/initdb/product-init.sh`

---

### 4. SQL DB Memory (structured metadata + BKG tables)

**Definition**: Structured relational data including core entities, receipt indexes, policy bundles, and BKG tables (when implemented).

**Store Mapping**:
- **IDE Plane**: Postgres
  - **Tables**: `meta.schema_version`, `core.tenant`, `core.repo`, `core.actor`, `core.receipt_index`, `core.bkg_edge` (Phase 0 stub)
  - **Path**: `zeroui_ide_pg` database
  - **Access**: Edge Agent
  - **Governance**: Local-only, no cloud sync
- **Tenant Plane**: Postgres
  - **Tables**: `meta.schema_version`, `core.tenant`, `core.repo`, `core.actor`, `core.receipt_index`, `core.bkg_edge` (Phase 0 stub), `app.tenant_receipt_index`, `app.tenant_integration_cursor`
  - **Path**: `zeroui_tenant_pg` database
  - **Access**: Tenant services
  - **Governance**: ACID transactions, tenant-scoped
- **Product Plane**: Postgres
  - **Tables**: `meta.schema_version`, `core.tenant`, `core.repo`, `core.actor`, `core.receipt_index`, `core.bkg_edge` (Phase 0 stub), `app.policy_bundle`, `app.policy_release`, `app.embedding_document`, `app.embedding_vector`
  - **Path**: `zeroui_product_pg` database
  - **Access**: Product services
  - **Governance**: ACID transactions, product-scoped
- **Shared Plane**: Postgres
  - **Tables**: `meta.schema_version`, `core.tenant`, `core.repo`, `core.actor`, `core.receipt_index`, `core.bkg_edge` (Phase 0 stub), `app.provider_registry`, `app.eval_run`, `app.supply_chain_artifact`
  - **Path**: `zeroui_shared_pg` database
  - **Access**: Shared services
  - **Governance**: ACID transactions, shared-scoped

**BKG Tables**: `core.bkg_edge` table is a Phase 0 stub. Full graph logic not yet implemented.

**Evidence**: 
- Core schema: `infra/db/schema_pack/migrations/pg/001_core.sql`
- App schemas: `infra/db/migrations/tenant/001_core.sql`, `infra/db/migrations/product/001_core.sql`, `infra/db/migrations/shared/001_core.sql`
- BKG stub: `infra/db/migrations/tenant/002_bkg_phase0.sql` (to be created)

---

### 5. File Store (raw artifacts, archives)

**Definition**: Raw file storage for receipts, evidence, policy snapshots, SBOMs, and other artifacts. JSONL receipts are the source of truth.

**Store Mapping**:
- **IDE Plane**: `ZU_ROOT/ide/`
  - **Paths**: 
    - Receipts: `ide/receipts/{repo-id}/{yyyy}/{mm}/`
    - Policy: `ide/policy/` (cache + trust/pubkeys)
    - LLM artifacts: `ide/llm/(prompts|tools|adapters|cache)/`
    - Queue: `ide/queue/(pending|sent|failed)/`
    - Logs: `ide/logs/`
  - **Access**: Edge Agent, VS Code Extension
  - **Governance**: Local-only, JSONL receipts are source of truth, no cloud sync
- **Tenant Plane**: `ZU_ROOT/tenant/{tenant-id}/{region}/`
  - **Paths**:
    - Evidence: `tenant/{tenant-id}/{region}/evidence/data/` (WORM semantics)
    - Telemetry: `tenant/{tenant-id}/{region}/telemetry/(metrics|traces|logs)/dt=.../`
    - Adapters: `tenant/{tenant-id}/{region}/adapters/(webhooks|gateway-logs)/dt=.../`
    - Reporting: `tenant/{tenant-id}/{region}/reporting/marts/dt=.../`
    - Context: `tenant/{tenant-id}/{region}/context/(identity|sso|scim|compliance)/`
  - **Access**: Tenant services, adapters
  - **Governance**: WORM semantics for evidence, retention policies, tenant-scoped
- **Product Plane**: `ZU_ROOT/product/{region}/`
  - **Paths**:
    - Policy registry: `product/{region}/policy/registry/(releases|templates|revocations)/`
    - Telemetry: `product/{region}/telemetry/(metrics|traces|logs)/dt=.../`
    - Evidence watermarks: `product/{region}/evidence/watermarks/{consumer-id}/`
    - Reporting: `product/{region}/reporting/tenants/{tenant-id}/{env}/aggregates/dt=.../`
  - **Access**: Product services
  - **Governance**: Policy-governed access, signed snapshots, product-scoped
- **Shared Plane**: `ZU_ROOT/shared/{org-id}/{region}/`
  - **Paths**:
    - PKI: `shared/{org-id}/{region}/pki/`
    - Telemetry: `shared/{org-id}/{region}/telemetry/(metrics|traces|logs)/dt=.../`
    - SIEM: `shared/{org-id}/{region}/siem/(detections|events)/dt=.../`
    - BI Lake: `shared/{org-id}/{region}/bi-lake/curated/zero-ui/`
    - Governance: `shared/{org-id}/{region}/governance/(controls|attestations)/`
    - Provider registry: `shared/{org-id}/{region}/provider-registry/`
    - Eval: `shared/{org-id}/{region}/eval/(harness|results|cache)/`
    - Security: `shared/{org-id}/{region}/security/(sbom|supply-chain)/`
  - **Access**: Shared services
  - **Governance**: Shared access, no tenant payloads

**Evidence**: `storage-scripts/folder-business-rules.md` (lines 125-189)

---

### 6. Semantic Q&A Cache (cache rules + location + governance)

**Definition**: Cache for semantic Q&A results to improve response time. **Hard rule: NOT used for gating decisions.**

**Store Mapping**:
- **IDE Plane**: N/A (no Q&A cache in IDE plane)
- **Tenant Plane**: N/A (no Q&A cache in tenant plane)
- **Product Plane**: Postgres (`app.semantic_qa_cache` table - Phase 0 stub)
  - **Path**: `zeroui_product_pg` database, `app` schema
  - **Access**: Context Service (via Product services)
  - **Governance**: 
    - **Hard Rule**: NOT used for gating decisions (informational only)
    - TTL-based expiration (configurable)
    - Product-scoped
- **Shared Plane**: N/A (no Q&A cache in shared plane)

**Status**: Phase 0 stub (schema placeholder). Full cache logic not yet implemented.

**Evidence**: `infra/db/migrations/product/003_semantic_qa_cache_phase0.sql` (to be created)

---

## Memory Type Summary

| Memory Type | IDE Plane | Tenant Plane | Product Plane | Shared Plane | Status |
|-------------|-----------|--------------|---------------|--------------|--------|
| **Working Memory** | Postgres (core tables) | Postgres (core tables) | Postgres (core tables) | Postgres (core tables) | ✅ Implemented |
| **Episodic Memory** | JSONL + Postgres index + BKG stub | JSONL + Postgres index + BKG stub | Postgres index + BKG stub | Postgres index + BKG stub | ⚠️ Partial (BKG Phase 0 stub) |
| **Vector DB Memory** | N/A | N/A | Postgres (pgvector) | N/A | ✅ Implemented |
| **SQL DB Memory** | Postgres (core + BKG stub) | Postgres (core + app + BKG stub) | Postgres (core + app + BKG stub) | Postgres (core + app + BKG stub) | ⚠️ Partial (BKG Phase 0 stub) |
| **File Store** | `ZU_ROOT/ide/` | `ZU_ROOT/tenant/` | `ZU_ROOT/product/` | `ZU_ROOT/shared/` | ✅ Implemented |
| **Semantic Q&A Cache** | N/A | N/A | Postgres (Phase 0 stub) | N/A | ⚠️ Partial (Phase 0 stub) |

---

## Governance Rules

### General Rules
1. **Plane Isolation**: Each plane's memory is isolated but supports cross-plane data flow via defined APIs
2. **Source of Truth**: JSONL receipts are the legal source of truth; databases are read/index planes
3. **No Secrets/PII**: Memory stores must not contain secrets or PII (use secrets manager/KMS)
4. **Identical Schema Contract**: All plane databases must have identical core schema (enforced via schema pack)

### Memory-Specific Rules
1. **Working Memory**: Ephemeral in IDE plane (can be cleared), durable in cloud planes
2. **Episodic Memory**: Append-only, signed receipts, WORM semantics for evidence
3. **Vector DB Memory**: Product plane only, pgvector extension required
4. **SQL DB Memory**: ACID transactions, plane-scoped isolation
5. **File Store**: JSONL receipts are source of truth, databases mirror for indexing
6. **Semantic Q&A Cache**: **NOT used for gating decisions** (informational only)

---

## References

- **DB Plane Contract**: `docs/architecture/db_plane_contract_option_a.md`
- **Schema Pack**: `infra/db/schema_pack/canonical_schema_contract.json`
- **Four Plane Storage**: `storage-scripts/folder-business-rules.md`
- **BKG Phase 0 Stub**: `infra/db/migrations/tenant/002_bkg_phase0.sql` (to be created)
- **Semantic Q&A Cache Stub**: `infra/db/migrations/product/003_semantic_qa_cache_phase0.sql` (to be created)

---

**Document Status**: Complete (pending BKG and Semantic Q&A Cache Phase 0 stub implementation)  
**Last Updated**: 2026-01-03

