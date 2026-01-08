# Functional Modules Setup Status

**Date**: 2026-01-03  
**Status**: Prerequisites Not Met

## Execution Attempt Summary

### Attempted Steps
1. ✅ Schema pack script exists: `scripts/db/apply_schema_pack.ps1`
2. ✅ Phase 0 stubs script exists: `scripts/db/apply_phase0_stubs.ps1`
3. ✅ Memory model documentation exists: `docs/architecture/memory_model.md`
4. ✅ BKG Phase 0 stub documentation exists: `docs/architecture/bkg_phase0_stub.md`

### Prerequisites Check Results

| Prerequisite | Status | Details |
|--------------|--------|---------|
| **Docker** | ❌ NOT AVAILABLE | Docker command not found in PATH |
| **Docker Containers** | ❌ NOT RUNNING | Cannot check container status (Docker unavailable) |
| **SQLite CLI** | ❌ NOT AVAILABLE | `sqlite3` command not found in PATH |
| **Environment Variables** | ❌ NOT SET | `ZEROUI_IDE_SQLITE_PATH`, `ZEROUI_TENANT_DB_URL`, `ZEROUI_PRODUCT_DB_URL`, `ZEROUI_SHARED_DB_URL` not set |

---

## Required Setup Steps

### Step 1: Install Prerequisites

#### Docker Desktop (Windows)
1. Install Docker Desktop for Windows: https://www.docker.com/products/docker-desktop
2. Ensure Docker is running and accessible from PowerShell
3. Verify: `docker --version`

#### SQLite CLI
1. Download SQLite CLI: https://www.sqlite.org/download.html
2. Extract `sqlite3.exe` to a directory in PATH (e.g., `C:\Program Files\SQLite\`)
3. Verify: `sqlite3 --version`

### Step 2: Start Docker Containers

```powershell
# Navigate to docker compose directory
cd infra/docker

# Start Postgres and Redis containers
docker compose -f compose.yaml up -d

# Verify containers are running
docker ps --filter "name=zeroui-postgres" --filter "name=zeroui-redis"
```

**Expected Containers**:
- `zeroui-postgres-tenant` (port 5433)
- `zeroui-postgres-product` (port 5434)
- `zeroui-postgres-shared` (port 5435)
- `zeroui-redis` (port 6379)

### Step 3: Set Environment Variables

Create a `.env` file in the repo root (copy from `.env.example`):

```powershell
# Copy example env file
Copy-Item .env.example .env

# Edit .env and set actual values:
# - ZEROUI_IDE_SQLITE_PATH=C:\Users\<USER>\.zeroai\zeroui_local.db
# - ZEROUI_TENANT_DB_URL=postgresql://zeroui_tenant_user:change_me_tenant@localhost:5433/zeroui_tenant_pg
# - ZEROUI_PRODUCT_DB_URL=postgresql://zeroui_product_user:change_me_product@localhost:5434/zeroui_product_pg
# - ZEROUI_SHARED_DB_URL=postgresql://zeroui_shared_user:change_me_shared@localhost:5435/zeroui_shared_pg
```

**Or set in PowerShell session**:
```powershell
$env:ZEROUI_IDE_SQLITE_PATH = "C:\Users\$env:USERNAME\.zeroai\zeroui_local.db"
$env:ZEROUI_TENANT_DB_URL = "postgresql://zeroui_tenant_user:change_me_tenant@localhost:5433/zeroui_tenant_pg"
$env:ZEROUI_PRODUCT_DB_URL = "postgresql://zeroui_product_user:change_me_product@localhost:5434/zeroui_product_pg"
$env:ZEROUI_SHARED_DB_URL = "postgresql://zeroui_shared_user:change_me_shared@localhost:5435/zeroui_shared_pg"
```

### Step 4: Apply Schema Pack

```powershell
# From repo root
.\scripts\db\apply_schema_pack.ps1
```

**Expected Output**:
- ✅ TENANT Postgres: Schema pack applied
- ✅ PRODUCT Postgres: Schema pack applied
- ✅ SHARED Postgres: Schema pack applied
- ✅ IDE SQLite: Schema pack applied

**What It Does**:
- Creates `meta.schema_version` table in all databases
- Creates `core` schema (Postgres) or `core__` prefixed tables (SQLite)
- Creates core tables: `tenant`, `repo`, `actor`, `receipt_index`, `bkg_edge`
- Records schema version "001" in `meta.schema_version`

### Step 5: Apply Phase 0 Stubs

```powershell
# From repo root
.\scripts\db\apply_phase0_stubs.ps1
```

**Expected Output**:
- ✅ TENANT Postgres: Phase 0 stub applied (BKG edges)
- ✅ PRODUCT Postgres: Phase 0 stub applied (BKG edges + Semantic Q&A Cache)
- ✅ SHARED Postgres: Phase 0 stub applied (BKG edges)
- ✅ IDE SQLite: Phase 0 stub applied (BKG edges)

**What It Does**:
- Applies BKG edge schema migrations (if not already in schema pack)
- Applies Semantic Q&A Cache schema migration (Product Plane only)

**Note**: BKG edges are already included in the schema pack migrations, so this step may be idempotent.

### Step 6: Verify Schema Application

```powershell
# Verify schema equivalence
.\scripts\db\verify_schema_equivalence.ps1
```

**Expected Output**:
- ✅ Postgres schema equivalence: OK
- ✅ SQLite contract check: OK
- ✅ meta.schema_version: OK
- ✅ ALL SCHEMA IDENTITY CHECKS PASSED

---

## Reference Documentation

### Memory Model
- **File**: `docs/architecture/memory_model.md`
- **Purpose**: Maps all 6 memory types to concrete stores with governance rules
- **Key Sections**:
  - Working Memory (AgentState in Graph Runtime)
  - Episodic Memory (Receipts + BKG edges)
  - Vector DB Memory (pgvector/embeddings)
  - SQL DB Memory (structured metadata + BKG tables)
  - File Store (raw artifacts, archives)
  - Semantic Q&A Cache

### BKG Phase 0 Stub
- **File**: `docs/architecture/bkg_phase0_stub.md`
- **Purpose**: Documents BKG Phase 0 stub (schema placeholders, contracts, ownership rules)
- **Key Sections**:
  - Schema Placeholders (Postgres and SQLite)
  - Contracts (JSON Schema)
  - Storage Locations (all planes)
  - Ownership Rules (what goes to Tenant/Product/Shared)
  - Entity Types and Edge Types

---

## Troubleshooting

### Docker Not Found
- **Error**: `docker : The term 'docker' is not recognized`
- **Fix**: Install Docker Desktop and ensure it's in PATH, or restart PowerShell after installation

### Container Not Found
- **Error**: `Container 'zeroui-postgres-tenant' not found`
- **Fix**: Start Docker containers: `cd infra/docker && docker compose -f compose.yaml up -d`

### SQLite Not Found
- **Error**: `sqlite3 not found in PATH`
- **Fix**: Install SQLite CLI and add to PATH, or use full path to `sqlite3.exe`

### Environment Variables Not Set
- **Error**: `Missing env var for TENANT DB URL`
- **Fix**: Set environment variables (see Step 3 above)

### Connection Refused
- **Error**: `psql: connection refused` or `could not connect to server`
- **Fix**: Ensure Docker containers are running: `docker ps`

---

## Next Steps After Setup

Once all prerequisites are met and schemas are applied:

1. **Verify Database Schemas**:
   ```powershell
   # Check Postgres schemas
   docker exec -it zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg -c "\dt core.*"
   docker exec -it zeroui-postgres-product psql -U zeroui_product_user -d zeroui_product_pg -c "\dt core.*"
   docker exec -it zeroui-postgres-shared psql -U zeroui_shared_user -d zeroui_shared_pg -c "\dt core.*"
   
   # Check SQLite schema
   sqlite3 $env:ZEROUI_IDE_SQLITE_PATH ".tables"
   ```

2. **Verify Schema Version**:
   ```powershell
   # Postgres
   docker exec -it zeroui-postgres-tenant psql -U zeroui_tenant_user -d zeroui_tenant_pg -c "SELECT * FROM meta.schema_version;"
   
   # SQLite
   sqlite3 $env:ZEROUI_IDE_SQLITE_PATH "SELECT * FROM meta__schema_version;"
   ```

3. **Begin Functional Modules Implementation**:
   - Reference `docs/architecture/memory_model.md` for memory type mappings
   - Reference `docs/architecture/bkg_phase0_stub.md` for BKG edge usage
   - Follow Four Plane placement rules: `storage-scripts/folder-business-rules.md`
   - Follow DB plane routing: `docs/architecture/db_plane_contract_option_a.md`

---

**Status**: Setup incomplete - prerequisites not met  
**Last Updated**: 2026-01-03  
**Note**: This document reflects the current setup status. For actual implementation status, see module-specific documentation.

