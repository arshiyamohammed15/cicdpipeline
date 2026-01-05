# Enforcing Identical Database Schemas Across 4 Planes

## Goal
All plane databases must be "identical" at the logical schema contract level:
- same table names
- same column names
- same primary keys
- same schema version recorded in meta.schema_version

Engine differences are allowed (SQLite vs Postgres types, indexes, extensions).

## Mechanism
1) One canonical contract: `infra/db/schema_pack/canonical_schema_contract.json`
2) Two engine migrations:
   - Postgres: `infra/db/schema_pack/migrations/pg/001_core.sql`
   - SQLite: `infra/db/schema_pack/migrations/sqlite/001_core.sql`
3) Automated enforcement:
   - Postgres: pg_dump --schema-only for tenant/product/shared must match exactly after normalization
   - SQLite: sqlite3 .schema must contain all required tables/columns from contract

## Commands (PowerShell)
Apply schema pack:
- pwsh scripts/db/apply_schema_pack.ps1

Verify schema identity:
- pwsh scripts/db/verify_schema_equivalence.ps1

