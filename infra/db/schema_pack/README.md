# ZeroUI Core Schema Pack (Identical Across 4 Planes)

This folder defines the canonical database schema contract that must be identical across planes:
- IDE Plane: SQLite (cache/mirror)
- Tenant Plane: Postgres
- Product Plane: Postgres
- Shared Plane: Postgres

"Identical" means:
- Same table names
- Same column names
- Same primary keys
- Same schema version recorded in `meta.schema_version`

Engine-specific differences (allowed):
- Data types (SQLite vs Postgres)
- Index implementations
- Extensions (e.g., pgvector is Postgres-only)

Sources of truth:
1) canonical_schema_contract.json
2) migrations/pg/*.sql and migrations/sqlite/*.sql must match the contract

