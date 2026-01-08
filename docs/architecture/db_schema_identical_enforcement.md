# Enforcing Identical Database Schemas Across 4 Planes

**Date**: 2026-01-03  
**Status**: Current Implementation  
**Alignment**: DB Plane Contract Option A

## Goal
All plane databases must be "identical" at the logical schema contract level:
- same table names
- same column names
- same primary keys
- same schema version recorded in `meta.schema_version` (Postgres) or `meta__schema_version` (SQLite)

Engine differences are allowed (SQLite vs Postgres types, indexes, extensions).

## Mechanism
1) One canonical contract: `infra/db/schema_pack/canonical_schema_contract.json`
2) Two engine migrations:
   - Postgres: `infra/db/schema_pack/migrations/pg/001_core.sql`
   - SQLite: `infra/db/schema_pack/migrations/sqlite/001_core.sql`
3) Automated enforcement:
   - Postgres: `pg_dump --schema-only` for tenant/product/shared must match exactly after normalization
   - SQLite: `sqlite3 .schema` must contain all required tables/columns from contract

## Commands (PowerShell)
Apply schema pack:
```powershell
pwsh scripts/db/apply_schema_pack.ps1
```

Verify schema identity:
```powershell
pwsh scripts/db/verify_schema_equivalence.ps1
```

## Implementation Status
- ✅ Schema pack script exists: `scripts/db/apply_schema_pack.ps1`
- ✅ Schema verification script exists: `scripts/db/verify_schema_equivalence.ps1`
- ✅ Canonical contract exists: `infra/db/schema_pack/canonical_schema_contract.json`
- ✅ Postgres migrations exist: `infra/db/schema_pack/migrations/pg/`
- ✅ SQLite migrations exist: `infra/db/schema_pack/migrations/sqlite/`

**Reference**: See `docs/architecture/db_plane_contract_option_a.md` for plane-to-database mapping rules.

