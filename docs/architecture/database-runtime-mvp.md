# ZeroUI Database Runtime MVP

**Status**: MVP/Pilot  
**Date**: 2026-01-03  
**Alignment**: 7 Layers × 4 Planes Architecture

## Overview

This document describes the MVP database runtime infrastructure for ZeroUI, aligned to the "7 Layers × 4 Planes" architecture. The runtime provides:

- **IDE Plane**: PostgreSQL (same as other planes)
- **Tenant/Product/Shared Planes**: PostgreSQL as primary database
- **Vector Search**: pgvector extension on Product Plane PostgreSQL
- **Event Bus**: Redis Streams

All services run on a single on-prem workstation using Docker Compose, with naming/structure ready to move to real clouds later.

## Architecture Alignment

### Storage by Plane

| Plane | Storage Type | Location | Purpose |
|-------|-------------|----------|---------|
| **IDE Plane (Laptop)** | PostgreSQL | `zeroui_ide_pg` | Append-only receipts, local policy cache, edge runtime state |
| **Tenant Plane** | PostgreSQL | `zeroui_tenant_pg` | Tenant-scoped truth: receipts/evidence ledger, integration state, context exports |
| **Product Plane** | PostgreSQL + pgvector | `zeroui_product_pg` | Product control-plane: policy bundles, orchestration state, vector embeddings |
| **Shared Plane** | PostgreSQL | `zeroui_shared_pg` | Cross-tenant shared: provider registry, eval harness, SBOM, observability |

### Why This Stack

- **PostgreSQL (Primary DB)**: Industry-standard ACID database for tenant/product/shared planes. Supports complex queries, transactions, and future scaling.
- **pgvector (Vector Search)**: Enables similarity search for Context Service embeddings. Runs on Product Plane where context snapshots are indexed.
- **Redis Streams (Event Bus)**: Lightweight, high-performance event streaming for inter-service communication. Replaces heavier message brokers in MVP.
- **PostgreSQL (IDE Plane)**: PostgreSQL database for IDE Plane, consistent with other planes. JSONL receipts remain source of truth; PostgreSQL provides indexing/caching.

## Docker Runtime

### Services

The MVP runtime consists of 5 Docker services:

1. **postgres_ide** (Port 5436)
   - Database: `zeroui_ide_pg`
   - User: `zeroui_ide_user`
   - Schema: `core` (core schema tables)

2. **postgres_tenant** (Port 5433)
   - Database: `zeroui_tenant_pg`
   - User: `zeroui_tenant_user`
   - Schema: `app` (application tables)

3. **postgres_product** (Port 5434)
   - Database: `zeroui_product_pg`
   - User: `zeroui_product_user`
   - Schema: `app` (application tables)
   - Extension: `pgvector` (enabled on init)

4. **postgres_shared** (Port 5435)
   - Database: `zeroui_shared_pg`
   - User: `zeroui_shared_user`
   - Schema: `app` (application tables)

5. **redis** (Port 6379)
   - Redis Streams for event bus
   - AOF persistence enabled

### Starting Services

From repo root (PowerShell):

```powershell
cd infra/docker
docker compose -f compose.yaml up -d
```

### Stopping Services

```powershell
cd infra/docker
docker compose -f compose.yaml down
```

To wipe volumes and re-initialize:

```powershell
cd infra/docker
docker compose -f compose.yaml down -v
docker compose -f compose.yaml up -d
```

**Warning**: `-v` removes all data volumes. Init scripts only run when data directories are empty.

## Configuration

### Environment Variables

Set these in `.env` (copy from `.env.example`):

```powershell
# IDE Plane
ZEROUI_IDE_DB_URL=postgresql://zeroui_ide_user:change_me_ide@localhost:5436/zeroui_ide_pg

# Tenant Plane
ZEROUI_TENANT_DB_URL=postgresql://zeroui_tenant_user:change_me_tenant@localhost:5433/zeroui_tenant_pg

# Product Plane
ZEROUI_PRODUCT_DB_URL=postgresql://zeroui_product_user:change_me_product@localhost:5434/zeroui_product_pg

# Shared Plane
ZEROUI_SHARED_DB_URL=postgresql://zeroui_shared_user:change_me_shared@localhost:5435/zeroui_shared_pg

# Redis
REDIS_URL=redis://localhost:6379

# Four Plane Storage Fabric
ZU_ROOT=D:\ZeroUI\development
```

### Connection String Format

PostgreSQL URLs follow this pattern:
```
postgresql://{user}:{password}@{host}:{port}/{database}
```

For Docker runtime:
- Host: `localhost` (from host machine) or service name (from within Docker network)
- Ports: 5436 (ide), 5433 (tenant), 5434 (product), 5435 (shared)
- Database names: `zeroui_ide_pg`, `zeroui_tenant_pg`, `zeroui_product_pg`, `zeroui_shared_pg`

## Schema Bootstrap

Minimal schema placeholders are in `db/migrations/mvp/`:

1. **001_tenant_receipts_index.sql**: Receipts index table (metadata only; raw receipts remain JSONL on disk)
2. **002_product_policy_registry.sql**: Policy bundle registry with snapshot hash references
3. **003_product_vector_embeddings.sql**: Vector embeddings table for Context Service (uses pgvector)

### Applying Migrations

From repo root (PowerShell):

```powershell
# Tenant Plane
docker exec -i zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg < db/migrations/mvp/001_tenant_receipts_index.sql

# Product Plane
docker exec -i zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg < db/migrations/mvp/002_product_policy_registry.sql
docker exec -i zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg < db/migrations/mvp/003_product_vector_embeddings.sql
```

**Note**: These are minimal placeholders. Detailed app schemas will be added as modules are implemented.

## Validation

### Smoke Test

Run the smoke test script to validate connectivity:

```powershell
.\scripts\db\smoke-test.ps1
```

This checks:
- Tenant Postgres connectivity
- Product Postgres connectivity + pgvector extension
- Shared Postgres connectivity
- Redis connectivity

### Manual Verification

**List databases:**
```powershell
docker exec zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg -c "\l"
docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "\l"
docker exec zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg -c "\l"
```

**Check pgvector extension:**
```powershell
docker exec zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
```

**Check Redis:**
```powershell
docker exec zeroui-redis redis-cli PING
```

**Test Redis Streams:**
```powershell
docker exec zeroui-redis redis-cli XADD zeroui:events * event_type test data "{\"test\": true}"
docker exec zeroui-redis redis-cli XREAD STREAMS zeroui:events 0
```

## Four Plane Storage Fabric Integration

The database runtime complements the Four Plane storage fabric (`ZU_ROOT` paths):

- **IDE Plane**: JSONL receipts in `ZU_ROOT/ide/receipts/` are source of truth. PostgreSQL (`ZEROUI_IDE_DB_URL`) provides local indexing/caching only.
- **Tenant Plane**: PostgreSQL stores receipt/evidence metadata and indexes. Raw receipts remain in `ZU_ROOT/tenant/{tenant-id}/{region}/evidence/data/` (JSONL).
- **Product Plane**: PostgreSQL stores policy bundle metadata and vector embeddings. Policy snapshots remain in `ZU_ROOT/product/{region}/policy/registry/`.
- **Shared Plane**: PostgreSQL stores shared metadata. Artifacts (SBOM, eval results) remain in `ZU_ROOT/shared/{org-id}/{region}/`.

**Principle**: Database is a **read/index plane**. JSONL files in `ZU_ROOT` are the **source of truth**.

## Going Live (Future)

When moving from MVP to production:

1. **Schemas don't change**: Table definitions remain the same.
2. **Connection strings change**: Point to cloud-hosted databases.
3. **Service separation**: Each plane's database can move to its cloud home:
   - Tenant DB → Tenant cloud/on-prem
   - Product DB → ZeroUI product cloud
   - Shared DB → Shared cloud
4. **Redis**: Can be replaced with managed Redis (AWS ElastiCache, Azure Cache, etc.) or other message brokers.

## References

- **DB Plane Contract**: `docs/architecture/db_plane_contract_option_a.md`
- **DB Environment Variables**: `docs/architecture/db_env_vars.md`
- **Four Plane Storage**: `storage-scripts/folder-business-rules.md`
- **Architecture Alignment**: `docs/architecture/four_plane_vs_7x4_alignment.md`

