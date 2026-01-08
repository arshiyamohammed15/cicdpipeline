# ZeroUI Database Environment Variables (Option A)

**Date**: 2026-01-03  
**Status**: Current Implementation  
**Alignment**: DB Plane Contract Option A

## Canonical variables

### IDE Plane (SQLite)
- `ZEROUI_IDE_SQLITE_PATH` (file path)
  - Windows example: `C:\Users\<USER>\.zeroai\zeroui_local.db`
  - Used by: PowerShell scripts for file-based operations
- `ZEROUI_IDE_SQLITE_URL` (connection string)
  - Example: `sqlite:///C:/Users/<USER>/.zeroai/zeroui_local.db`
  - Used by: Application code for database connections

### Tenant Plane (Postgres)
- `ZEROUI_TENANT_DB_URL`
  - Example: `postgresql://zeroui_tenant_user:password@localhost:5432/zeroui_tenant_pg`

### Product Plane (Postgres)
- `ZEROUI_PRODUCT_DB_URL`
  - Example: `postgresql://zeroui_product_user:password@localhost:5432/zeroui_product_pg`

### Shared Plane (Postgres)
- `ZEROUI_SHARED_DB_URL`
  - Example: `postgresql://zeroui_shared_user:password@localhost:5432/zeroui_shared_pg`

## Pilot note
In MVP/Pilot, Tenant/Product/Shared Postgres URLs may point to the same host and port, but MUST use different database names:
- `zeroui_tenant_pg`
- `zeroui_product_pg`
- `zeroui_shared_pg`

**Implementation Status**: These environment variables are used by:
- Database connection scripts: `scripts/db/apply_schema_pack.ps1`
- Database verification scripts: `scripts/db/verify_schema_equivalence.ps1`
- Cloud services: All services use these variables via `database/connection.py` patterns
- CI verification: `scripts/ci/verify_database_env_vars.ps1`

**Reference**: See `docs/architecture/db_plane_contract_option_a.md` for complete plane-to-database mapping.
