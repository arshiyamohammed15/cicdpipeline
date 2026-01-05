# ZeroUI DB Plane Contract — Option A (MVP/Pilot)

## Purpose
This document locks the database deployment contract for the ZeroUI MVP/Pilot:
- IDE Plane (Laptop): local SQLite
- Tenant Plane: Postgres (tenant database)
- Product Plane: Postgres (product database)
- Shared Plane: Postgres (shared database)

This is a **logical plane boundary contract**. In pilot, Tenant/Product/Shared databases may run on the same on-prem workstation Postgres cluster, but they remain separate databases.

## Plane → Database Mapping

| Plane | Runtime Location (Pilot) | Database Engine | Database Name | Canonical Env Var |
|---|---|---|---|---|
| IDE Plane (Laptop) | Developer laptop | SQLite | zeroui_local.db (file) | ZEROUI_IDE_SQLITE_URL |
| Tenant Plane | On-prem workstation (pilot) | Postgres | zeroui_tenant_pg | ZEROUI_TENANT_DB_URL |
| Product Plane | On-prem workstation (pilot) | Postgres | zeroui_product_pg | ZEROUI_PRODUCT_DB_URL |
| Shared Plane | On-prem workstation (pilot) | Postgres | zeroui_shared_pg | ZEROUI_SHARED_DB_URL |

## Data Ownership Rules (What lives where)

### IDE Plane (SQLite)
Stores only **edge runtime state** required for local, offline-first operation:
- local receipt cache/buffer (last-N)
- local policy cache (current snapshot + verification metadata)
- local outbox/queue for sending events upward
- lightweight status state for IDE surfaces

Must NOT store:
- long-term tenant history
- cross-repo/cross-tenant aggregates
- global control-plane state

### Tenant Plane (Postgres: zeroui_tenant_pg)
Stores **tenant-scoped truth**:
- durable receipts/evidence ledger for the tenant
- tenant history used for deterministic decisions
- tenant integration state (provider cursors, watermarks, webhook ingestion metadata)
- tenant context exports/snapshots/indexes (redacted; no secrets; policy governed)

Must NOT store:
- cross-tenant global registries
- shared provider registry data

### Product Plane (Postgres: zeroui_product_pg)
Stores **product control-plane state** (per tenant but product-owned):
- policy bundle/snapshot/release spine (policy lifecycle)
- orchestration state and governance workflow state
- product-side aggregates and reporting per tenant

Must NOT store:
- shared global registries intended for all tenants
- raw tenant secret payloads

### Shared Plane (Postgres: zeroui_shared_pg)
Stores **cross-tenant shared infrastructure metadata**:
- provider registry metadata, allowlists, adapter versions
- evaluation harness fixtures/runs/results metadata
- SBOM / provenance / supply chain verification metadata
- global observability metadata (no tenant payload bodies)

Must NOT store:
- tenant receipts/evidence payloads
- tenant context snapshots (unless fully anonymised and explicitly allowed by policy)

## Hard Boundary Rules (Non-negotiable)
1) IDE/Edge components MUST NOT connect directly to Product/Shared Postgres databases.
2) Tenant services MUST NOT write into Product/Shared Postgres databases via direct DB access.
3) Shared database MUST NOT store tenant payload bodies; only shared metadata/artifacts.
4) A module stores its data only in the plane DB that matches its plane responsibility.

If a new feature's storage plane is unclear, STOP and explicitly classify the plane before creating tables.

## Pilot Workstation Topology
- One Postgres cluster runs on an on-prem workstation.
- The cluster hosts three separate databases:
  - zeroui_tenant_pg
  - zeroui_product_pg
  - zeroui_shared_pg
- Logical plane separation is preserved by:
  - separate DB names
  - separate credentials (recommended)
  - separate migrations per DB (recommended)

## Going Live (Move to Real Clouds)
When moving from pilot workstation to real clouds:
- **Schemas and table designs do not change**
- Only the connection strings change:
  - ZEROUI_TENANT_DB_URL points to tenant cloud/on-prem DB
  - ZEROUI_PRODUCT_DB_URL points to ZeroUI product cloud DB
  - ZEROUI_SHARED_DB_URL points to shared cloud DB

