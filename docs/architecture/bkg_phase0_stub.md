# Background Knowledge Graph (BKG) - Phase 0 Stub

**Status**: Planned (not fully implemented yet)  
**Date**: 2026-01-03  
**Purpose**: Schema placeholder and contracts to enable Functional Modules to write receipts/events without ambiguity

## Overview

BKG (Background Knowledge Graph) connects entities (tenant, repo, actor, receipt, policy, gate, signal, event) to form a knowledge graph. This Phase 0 stub provides:
- Schema placeholders in all plane databases
- JSON Schema contract for BKG edges
- Storage locations and ownership rules
- Clear boundaries for what goes to Tenant/Product/Shared

**Full graph logic** (traversal, querying, inference) is **not yet implemented**. This stub enables FMs to reference BKG edges in receipts/events without ambiguity.

---

## Schema Placeholders

### Postgres (Tenant/Product/Shared Planes)

**Table**: `core.bkg_edge` (in core schema for identical schema contract)

**Columns**:
- `edge_id` TEXT PRIMARY KEY
- `source_entity_type` TEXT NOT NULL (enum: tenant, repo, actor, receipt, policy, gate, signal, event)
- `source_entity_id` TEXT NOT NULL
- `target_entity_type` TEXT NOT NULL (enum: tenant, repo, actor, receipt, policy, gate, signal, event)
- `target_entity_id` TEXT NOT NULL
- `edge_type` TEXT NOT NULL (enum: owns, contains, triggers, references, depends_on, belongs_to, causes, precedes)
- `metadata` JSONB NULL (optional edge-specific metadata)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now()

**Indexes**:
- `(source_entity_type, source_entity_id)`
- `(target_entity_type, target_entity_id)`
- `(edge_type)`
- `(source_entity_type, source_entity_id, target_entity_type, target_entity_id)`

**Evidence**: `infra/db/migrations/tenant/002_bkg_phase0.sql`, `infra/db/migrations/product/003_bkg_phase0.sql`, `infra/db/migrations/shared/002_bkg_phase0.sql`

### SQLite (IDE Plane)

**Table**: `core__bkg_edge` (using `__` prefix for schema emulation)

**Columns**: Same as Postgres, but `metadata` is TEXT (JSON stored as TEXT in SQLite) and `created_at` is TEXT (datetime('now'))

**Evidence**: `infra/db/migrations/sqlite/002_bkg_phase0.sql`

---

## Contracts

### JSON Schema

**File**: `contracts/bkg/schemas/bkg_edge.schema.json`

**Required Fields**:
- `edge_id` (string)
- `source_entity_type` (string, enum)
- `source_entity_id` (string)
- `target_entity_type` (string, enum)
- `target_entity_id` (string)
- `edge_type` (string, enum)

**Optional Fields**:
- `metadata` (object)
- `created_at` (string, date-time)

**Evidence**: `contracts/bkg/schemas/bkg_edge.schema.json`

---

## Storage Locations

### IDE Plane
- **Database**: SQLite (`ZEROUI_IDE_SQLITE_URL`)
- **Table**: `core__bkg_edge`
- **Access**: Edge Agent
- **Governance**: Local-only, ephemeral (can be cleared on restart)

### Tenant Plane
- **Database**: Postgres (`zeroui_tenant_pg`)
- **Table**: `core.bkg_edge`
- **Access**: Tenant services
- **Governance**: Tenant-scoped, ACID transactions, durable

### Product Plane
- **Database**: Postgres (`zeroui_product_pg`)
- **Table**: `core.bkg_edge`
- **Access**: Product services
- **Governance**: Product-scoped, ACID transactions, durable

### Shared Plane
- **Database**: Postgres (`zeroui_shared_pg`)
- **Table**: `core.bkg_edge`
- **Access**: Shared services
- **Governance**: Shared-scoped, ACID transactions, durable

---

## Ownership Rules (What Goes Where)

### Tenant Plane BKG Edges

**Store edges where**:
- Source or target entity is tenant-scoped (tenant, repo, actor within a tenant)
- Edge relates to tenant-specific receipts/events
- Edge connects tenant entities to tenant receipts

**Examples**:
- `tenant` → `owns` → `repo`
- `repo` → `contains` → `receipt`
- `actor` → `triggers` → `receipt`
- `receipt` → `references` → `policy` (if policy is tenant-specific)

**Do NOT store**:
- Cross-tenant edges (use Shared plane)
- Product-level policy edges (use Product plane)

### Product Plane BKG Edges

**Store edges where**:
- Source or target entity is product-scoped (product-level policies, product aggregates)
- Edge relates to policy lifecycle (policy → policy, policy → release)
- Edge connects product entities to product-level receipts

**Examples**:
- `policy` → `depends_on` → `policy`
- `policy` → `triggers` → `release`
- `receipt` → `references` → `policy` (if policy is product-level)

**Do NOT store**:
- Tenant-specific edges (use Tenant plane)
- Cross-tenant shared edges (use Shared plane)

### Shared Plane BKG Edges

**Store edges where**:
- Source or target entity is shared-scoped (provider registry, eval runs, SBOM artifacts)
- Edge relates to cross-tenant relationships
- Edge connects shared entities to shared artifacts

**Examples**:
- `provider` → `supports` → `tenant` (cross-tenant relationship)
- `eval_run` → `references` → `policy` (shared evaluation)
- `sbom` → `references` → `artifact` (supply chain)

**Do NOT store**:
- Tenant-specific edges (use Tenant plane)
- Product-level policy edges (use Product plane)

---

## Entity Types

**Allowed Entity Types** (per contract):
- `tenant`: Tenant entity
- `repo`: Repository entity
- `actor`: Actor entity (user, service, etc.)
- `receipt`: Receipt entity
- `policy`: Policy entity
- `gate`: Gate entity (decision gate)
- `signal`: Signal entity (ingestion signal)
- `event`: Event entity (system event)

---

## Edge Types

**Allowed Edge Types** (per contract):
- `owns`: Source entity owns target entity
- `contains`: Source entity contains target entity
- `triggers`: Source entity triggers target entity
- `references`: Source entity references target entity
- `depends_on`: Source entity depends on target entity
- `belongs_to`: Source entity belongs to target entity
- `causes`: Source entity causes target entity
- `precedes`: Source entity precedes target entity (temporal)

---

## Implementation Status

### Phase 0 (Current)
- ✅ Schema placeholders created in all plane databases
- ✅ JSON Schema contract created
- ✅ Ownership rules documented
- ✅ Storage locations defined

### Phase 1 (Future)
- ⏳ Graph traversal logic
- ⏳ Graph querying API
- ⏳ Graph inference engine
- ⏳ Graph visualization

---

## References

- **Memory Model**: `docs/architecture/memory_model.md`
- **BKG Edge Schema**: `contracts/bkg/schemas/bkg_edge.schema.json`
- **Migrations**: 
  - `infra/db/migrations/tenant/002_bkg_phase0.sql`
  - `infra/db/migrations/product/003_bkg_phase0.sql`
  - `infra/db/migrations/shared/002_bkg_phase0.sql`
  - `infra/db/migrations/sqlite/002_bkg_phase0.sql`

---

**Document Status**: Phase 0 Stub Complete  
**Last Updated**: 2026-01-03

