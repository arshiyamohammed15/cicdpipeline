# ZeroUI Core Database Schema (Contract-Derived)

**Status**: MVP/Pilot  
**Date**: 2026-01-03  
**Alignment**: 7 Layers × 4 Planes Architecture, Option A DB Contract

## Overview

This document describes the minimal, contract-derived core database schema for ZeroUI Option A. The schema is derived **exclusively** from existing repository contracts, receipt schemas, and policy artifacts—no invented business fields.

## Schema Design Principles

1. **Contract-Derived**: Every column must be traceable to a contract field or receipt schema.
2. **Index-Only for Receipts**: Raw receipts remain append-only JSONL on disk (`ZU_ROOT` paths). Database stores only metadata/index for search/reporting.
3. **Plane Isolation**: Each plane's database stores only data appropriate to its responsibility (per Option A contract).
4. **Multi-Tenant Safety**: Tenant DB tables include `tenant_id` for every row. Product/Shared must NOT store raw tenant payload bodies.

## Schema by Plane

### Tenant Plane (`zeroui_tenant_pg`)

**Purpose**: Tenant-scoped evidence index + integration watermarks/cursors

#### Tables

##### `app.tenant_receipt_index`

Index table for tenant receipts. Raw receipts stored as append-only JSONL in `ZU_ROOT/tenant/{tenant-id}/{region}/evidence/data/`.

**Contract Fields** (source citations):
- `receipt_id`: `DecisionReceipt.receipt_id` (TypeScript: `src/edge-agent/shared/receipt-types.ts`), `receipt.schema.json`
- `gate_id`: `DecisionReceipt.gate_id` (TypeScript), `receipt.schema.json`
- `tenant_id`: Contracts (`key_management_service`, `signal_ingestion`, etc.)
- `repo_id`: `DecisionReceipt.actor.repo_id` (TypeScript), `gsmd/schema/receipt.schema.json`
- `policy_snapshot_hash`: `DecisionReceipt.snapshot_hash` (TypeScript), `gsmd/schema/receipt.schema.json` (as `policy_snapshot_hash`, pattern: `^sha256:[0-9a-f]{64}$`)
- `policy_version_ids`: `DecisionReceipt.policy_version_ids` (TypeScript), `gsmd/schema/receipt.schema.json` (array of strings)
- `emitted_at`: `DecisionReceipt.timestamp_utc` (TypeScript, ISO 8601 UTC timestamp)
- `outcome`: `DecisionReceipt.decision.status` (TypeScript) - enum: `'pass' | 'warn' | 'soft_block' | 'hard_block'`
- `signature`: `DecisionReceipt.signature` (TypeScript), `gsmd/schema/receipt.schema.json`

**Columns**:
- `receipt_id` TEXT PRIMARY KEY
- `tenant_id` TEXT NOT NULL
- `repo_id` TEXT
- `gate_id` TEXT NOT NULL
- `receipt_type` TEXT (e.g., 'decision', 'feedback')
- `outcome` TEXT ('pass' | 'warn' | 'soft_block' | 'hard_block')
- `severity` TEXT (optional)
- `policy_snapshot_hash` TEXT (format: 'sha256:hex')
- `policy_version_ids` JSONB (array of policy version IDs)
- `emitted_at` TIMESTAMPTZ NOT NULL
- `zu_root_relpath` TEXT NOT NULL (path to JSONL file relative to ZU_ROOT)
- `byte_offset` BIGINT (optional: byte offset in JSONL file)
- `byte_len` BIGINT (optional: byte length of receipt line)
- `payload_sha256` TEXT (optional: SHA256 hash of receipt payload)
- `signature_alg` TEXT (optional: signature algorithm)
- `signature` TEXT
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(tenant_id, repo_id, gate_id, emitted_at DESC)` - Lookup by tenant/repo/gate/time
- `(policy_snapshot_hash)` - Lookup by policy snapshot
- `(outcome)` - Filter by decision outcome

##### `app.tenant_integration_cursor`

Watermarks/cursors for tenant integration ingestion (webhooks, adapters).

**Columns**:
- `cursor_id` TEXT PRIMARY KEY
- `tenant_id` TEXT NOT NULL
- `provider` TEXT NOT NULL (e.g., 'github', 'gitlab', 'jira')
- `repo_id` TEXT (optional: repo-specific cursor)
- `cursor_value` TEXT NOT NULL (provider-specific format)
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(tenant_id, provider, repo_id)` - Lookup by tenant/provider/repo

---

### Product Plane (`zeroui_product_pg`)

**Purpose**: Policy lifecycle spine + product orchestration metadata + vector embeddings index

#### Tables

##### `app.policy_bundle`

Policy bundle registry with snapshot hash references. Policy snapshots stored in `ZU_ROOT/product/{region}/policy/registry/`.

**Contract Fields**:
- `snapshot_hash`: `DecisionReceipt.snapshot_hash` (TypeScript), `gsmd/schema/receipt.schema.json` (as `policy_snapshot_hash`)
- `version_ids`: `DecisionReceipt.policy_version_ids` (TypeScript)

**Columns**:
- `bundle_id` TEXT PRIMARY KEY
- `snapshot_hash` TEXT NOT NULL UNIQUE (format: 'sha256:hex')
- `version_ids` JSONB (array of policy version IDs)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(snapshot_hash)` - Lookup by snapshot hash

##### `app.policy_release`

Policy release lifecycle tracking. Links to `policy_bundle` via `snapshot_hash`.

**Columns**:
- `release_id` TEXT PRIMARY KEY
- `snapshot_hash` TEXT NOT NULL (references `policy_bundle.snapshot_hash`)
- `status` TEXT NOT NULL (e.g., 'draft', 'published', 'revoked')
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(snapshot_hash)` - Lookup by snapshot hash

##### `app.embedding_document`

Document metadata for vector embeddings. Links to `embedding_vector` via `doc_id`.

**Columns**:
- `doc_id` TEXT PRIMARY KEY
- `tenant_id` TEXT (optional: only if product plane stores per-tenant embeddings)
- `namespace` TEXT NOT NULL (e.g., 'context_snapshot', 'policy_rule')
- `source` TEXT (source identifier, e.g., repo_id, policy_id)
- `metadata` JSONB (optional structured metadata)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(tenant_id)` WHERE `tenant_id IS NOT NULL` - Lookup by tenant
- `(namespace, source)` - Lookup by namespace/source

##### `app.embedding_vector`

Vector embeddings for Context Service similarity search. Uses pgvector extension.

**Dimension**: 1536 (from existing `db/migrations/mvp/003_product_vector_embeddings.sql`)

**Columns**:
- `vector_id` TEXT PRIMARY KEY
- `doc_id` TEXT NOT NULL REFERENCES `app.embedding_document(doc_id)` ON DELETE CASCADE
- `embedding` vector(1536) (requires pgvector extension)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- HNSW index on `embedding` using `vector_cosine_ops` (created only if pgvector extension is available)

---

### Shared Plane (`zeroui_shared_pg`)

**Purpose**: Cross-tenant shared infrastructure metadata (provider registry, eval harness, SBOM/supply chain)

#### Tables

##### `app.provider_registry`

Cross-tenant provider registry metadata, versions, allowlists. Shared infrastructure metadata only (no tenant payloads).

**Columns**:
- `provider_id` TEXT PRIMARY KEY
- `name` TEXT NOT NULL
- `version` TEXT (optional: provider version)
- `metadata` JSONB (optional: provider-specific metadata)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(name)` - Lookup by provider name

##### `app.eval_run`

Evaluation harness runs and results metadata. Shared across tenants.

**Columns**:
- `run_id` TEXT PRIMARY KEY
- `suite` TEXT NOT NULL (evaluation suite identifier)
- `status` TEXT NOT NULL (e.g., 'running', 'completed', 'failed')
- `started_at` TIMESTAMPTZ
- `ended_at` TIMESTAMPTZ
- `metadata` JSONB (optional: run-specific metadata)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(suite, status)` - Lookup by suite/status
- `(started_at)` WHERE `started_at IS NOT NULL` - Lookup by start time

##### `app.supply_chain_artifact`

SBOM, provenance, attestation metadata. Artifacts stored in `ZU_ROOT/shared/{org-id}/{region}/security/(sbom|supply-chain)/`.

**Columns**:
- `artifact_id` TEXT PRIMARY KEY
- `artifact_type` TEXT NOT NULL (generic: 'sbom', 'provenance', 'attestation' - values only if evidenced in repo docs)
- `ref` TEXT (pointer to storage path or external reference)
- `sha256` TEXT (optional: SHA256 hash of artifact)
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()

**Indexes**:
- `(artifact_type)` - Lookup by artifact type
- `(sha256)` WHERE `sha256 IS NOT NULL` - Lookup by hash

---

## What is NOT Stored in Database

**Intentionally excluded** (stored in `ZU_ROOT` paths only):

1. **Raw Receipt Bodies**: Receipts remain append-only JSONL in `ZU_ROOT/tenant/{tenant-id}/{region}/evidence/data/`. Database stores only metadata/index.
2. **Policy Snapshot Content**: Policy snapshots stored in `ZU_ROOT/product/{region}/policy/registry/`. Database stores only hash references.
3. **Tenant Payload Bodies**: Product/Shared databases must NOT store raw tenant receipt/evidence payloads.
4. **SBOM/Provenance Artifacts**: Artifacts stored in `ZU_ROOT/shared/{org-id}/{region}/security/(sbom|supply-chain)/`. Database stores only metadata/pointers.

**Principle**: Database is a **read/index plane**. JSONL files in `ZU_ROOT` are the **source of truth**.

## Applying Migrations

### Prerequisites

1. Docker containers running (from `infra/docker/compose.yaml`):
   - `zeroui-postgres-tenant` (port 5433)
   - `zeroui-postgres-product` (port 5434)
   - `zeroui-postgres-shared` (port 5435)

2. Environment variables set (from `.env`):
   - `ZEROUI_TENANT_DB_URL`
   - `ZEROUI_PRODUCT_DB_URL`
   - `ZEROUI_SHARED_DB_URL`

### Apply All Migrations

From repo root (PowerShell):

```powershell
.\scripts\db\apply_migrations.ps1
```

This applies:
- `infra/db/migrations/tenant/001_core.sql` → Tenant DB
- `infra/db/migrations/product/001_core.sql` → Product DB
- `infra/db/migrations/product/002_embeddings.sql` → Product DB
- `infra/db/migrations/shared/001_core.sql` → Shared DB

### Apply Individual Migrations

**Tenant Plane**:
```powershell
Get-Content infra\db\migrations\tenant\001_core.sql | docker exec -i zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg
```

**Product Plane (Core)**:
```powershell
Get-Content infra\db\migrations\product\001_core.sql | docker exec -i zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg
```

**Product Plane (Embeddings)**:
```powershell
Get-Content infra\db\migrations\product\002_embeddings.sql | docker exec -i zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg
```

**Shared Plane**:
```powershell
Get-Content infra\db\migrations\shared\001_core.sql | docker exec -i zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg
```

## Schema Smoke Test

Run the smoke test to verify tables exist and basic SELECT queries work:

```powershell
.\scripts\db\schema_smoke.ps1
```

This validates:
- All core tables exist in each database
- Basic SELECT queries succeed
- pgvector extension is enabled (Product Plane)

## Contract Field Citations

### Receipt Fields

| Database Column | Contract Source | File Path |
|----------------|----------------|-----------|
| `receipt_id` | `DecisionReceipt.receipt_id` | `src/edge-agent/shared/receipt-types.ts` |
| `gate_id` | `DecisionReceipt.gate_id` | `src/edge-agent/shared/receipt-types.ts` |
| `tenant_id` | Contracts (multiple) | `contracts/key_management_service`, `contracts/signal_ingestion`, etc. |
| `repo_id` | `DecisionReceipt.actor.repo_id` | `src/edge-agent/shared/receipt-types.ts` |
| `policy_snapshot_hash` | `DecisionReceipt.snapshot_hash`, `gsmd/schema/receipt.schema.json` (as `policy_snapshot_hash`) | `src/edge-agent/shared/receipt-types.ts`, `gsmd/schema/receipt.schema.json` |
| `policy_version_ids` | `DecisionReceipt.policy_version_ids` | `src/edge-agent/shared/receipt-types.ts` |
| `emitted_at` | `DecisionReceipt.timestamp_utc` | `src/edge-agent/shared/receipt-types.ts` |
| `outcome` | `DecisionReceipt.decision.status` | `src/edge-agent/shared/receipt-types.ts` |
| `signature` | `DecisionReceipt.signature` | `src/edge-agent/shared/receipt-types.ts` |

### Policy Fields

| Database Column | Contract Source | File Path |
|----------------|----------------|-----------|
| `snapshot_hash` | `DecisionReceipt.snapshot_hash` | `src/edge-agent/shared/receipt-types.ts` |
| `version_ids` | `DecisionReceipt.policy_version_ids` | `src/edge-agent/shared/receipt-types.ts` |

### Embedding Fields

| Database Column | Contract Source | File Path |
|----------------|----------------|-----------|
| `embedding` (dimension 1536) | Existing migration | `db/migrations/mvp/003_product_vector_embeddings.sql` |

## References

- **DB Plane Contract**: `docs/architecture/db_plane_contract_option_a.md`
- **DB Environment Variables**: `docs/architecture/db_env_vars.md`
- **Database Runtime MVP**: `docs/architecture/database-runtime-mvp.md`
- **Four Plane Storage**: `storage-scripts/folder-business-rules.md`
- **Receipt Schema Cross-Reference**: `docs/architecture/receipt-schema-cross-reference.md`

