# ZeroUI Database Environment Variables (Option A)

## Canonical variables

### IDE Plane (SQLite)
- `ZEROUI_IDE_SQLITE_PATH`
  - Windows example: `C:\Users\<USER>\.zeroai\zeroui_local.db`
- `ZEROUI_IDE_SQLITE_URL`
  - Example: `sqlite:///C:/Users/<USER>/.zeroai/zeroui_local.db`

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

