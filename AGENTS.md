# AGENTS.md

## Four Plane Placement Rules (ZeroUI)

**Before creating any folder/file**, decide whether it is:
1) **Runtime Storage Artifact** (belongs under ZU_ROOT Four-Plane paths) OR
2) **Repo Source Artifact** (belongs inside this repo)

### Runtime Storage Artifact
- Source of truth: `storage-scripts/folder-business-rules.md`
- Choose the exact canonical path family under the correct plane (IDE/Laptop, Tenant, Product, Shared).
- If no canonical path exists: **STOP and ask** (max 3 questions). Do not guess.

### Repo Source Artifact
- Do not create new top-level plane roots inside the repo unless explicitly modifying `storage-scripts/**`.
- If the right repo folder is ambiguous: **STOP and ask** (max 3 questions). Do not guess.

### Non-negotiable
- No invented folders.
- No assumptions.
- If uncertain: STOP.

## DB Plane Routing (Option A)

ZeroUI uses a strict plane → database contract:
- IDE Plane: SQLite only (`ZEROUI_IDE_SQLITE_URL`)
- Tenant Plane: Postgres only (`ZEROUI_TENANT_DB_URL`)
- Product Plane: Postgres only (`ZEROUI_PRODUCT_DB_URL`)
- Shared Plane: Postgres only (`ZEROUI_SHARED_DB_URL`)

Rules:
1) Do not create tables in the wrong plane database.
2) Do not mix tenant/product/shared tables in a single database.
3) Use only the canonical env vars above.
4) If a prompt asks to store data and the plane is unclear: STOP and ask (max 3 questions). Do not guess.
