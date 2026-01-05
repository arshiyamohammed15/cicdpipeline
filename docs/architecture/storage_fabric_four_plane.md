# Four Plane Storage Fabric

**ID**: ARCH.STORAGE.FABRIC.MT-04  
**Date**: 2026-01-03  
**Status**: Architecture Note

## Definition

The **Four Plane Storage Fabric** is a deterministic path contract system that provides structured storage across the four deployment planes of ZeroUI 2.0: **IDE Plane (Laptop)**, **Tenant**, **Product**, and **Shared**. The fabric defines canonical paths, naming conventions, and operational rules that enable consistent data organization without duplicating business logic.

### Core Principle

Storage fabric = **deterministic path contracts** across IDE/Tenant/Product/Shared planes. The fabric provides structure and governance rules; services implement business logic.

**Implementation Source of Truth**: `storage-scripts/` folder contains the authoritative rules, scaffold scripts, and path templates. See `storage-scripts/folder-business-rules.md` for complete specifications.

---

## Architecture Layer Mapping

The storage fabric supports the 7×4 architecture layers without duplicating responsibilities:

### Layer 2: Writes (Evidence & Receipts)

**Storage Responsibility**: Provide append-only, immutable storage for evidence and receipts.

- **IDE Plane**: `ide/receipts/{repo-id}/{yyyy}/{mm}/` — Signed JSONL receipts from edge agent
- **Tenant Plane**: `tenant/{tenant-id}/{region}/evidence/data/{repo-id}/dt={yyyy}-{mm}-{dd}/` — WORM (Write-Once-Read-Many) evidence mirror
- **Shared Plane**: `shared/{org-id}/{region}/governance/(controls|attestations)/` — Audit ledger and attestations

**Services Write To**: Layer 2 services (edge agent, evidence ingestion, audit services) write evidence and receipts to these paths. Storage fabric enforces append-only semantics and partitioning.

### Layer 3: Contracts (Policy & Configuration)

**Storage Responsibility**: Provide signed policy snapshots, configuration templates, and contract definitions.

- **IDE Plane**: `ide/policy/` — Cached policy snapshots and public keys
- **Product Plane**: `product/{region}/policy/registry/(releases|templates|revocations)/` — Authoritative policy registry
- **Shared Plane**: `shared/{org-id}/{region}/pki/` — PKI artifacts and trust anchors

**Services Define Contracts**: Layer 3 services (policy registry, configuration management) publish signed contracts to these paths. Storage fabric enforces signing requirements and versioning.

### Layer 7: Consumption (Reporting & Aggregates)

**Storage Responsibility**: Provide partitioned data marts and aggregates for analytics and reporting.

- **Tenant Plane**: `tenant/{tenant-id}/{region}/reporting/marts/<table>/dt={yyyy}-{mm}-{dd}/` — Tenant-specific data marts
- **Product Plane**: `product/{region}/reporting/tenants/{tenant-id}/{env}/aggregates/dt={yyyy}-{mm}-{dd}/` — Cross-tenant aggregates
- **Shared Plane**: `shared/{org-id}/{region}/bi-lake/curated/zero-ui/` — BI data lake

**Services Consume From**: Layer 7 services (reporting, analytics, BI tools) read aggregated data from these paths. Storage fabric provides partitioning and organization; services implement query logic.

---

## Operational Rules

### Time Partitioning (`dt=`)

All time-partitioned data uses UTC date partitions: `dt={yyyy}-{mm}-{dd}` (zero-padded).

- **Purpose**: Enable efficient querying, retention, and archival
- **Format**: `dt=2026-01-03/` (not `dt=2026/01/03/`)
- **Optional Sharding**: High-volume paths may use `dt=.../shard={00..ff}/` for hot sharding

**Example**: `tenant/{tenant-id}/{region}/telemetry/metrics/dt=2026-01-03/`

### JSONL Truth

**JSONL (newline-delimited JSON) is the source of truth** for evidence and receipts.

- **Format**: Each line is a complete, signed JSON object
- **Signing**: Each line is signed over canonical JSON (deterministic serialization)
- **Append-Only**: Once written, lines cannot be modified or deleted
- **Invalid Lines**: Go to `quarantine/` (laptop) or `dlq/` (cloud ingest)

**Example**: `ide/receipts/{repo-id}/2026/01/receipts.jsonl`

### DB Mirror

**Dual storage pattern**: JSONL is authority; DB mirrors provide indexing.

- **JSONL**: Source of truth, append-only, signed
- **DB Mirror**: SQLite (laptop) or Postgres (cloud) stores raw JSON verbatim + minimal indexes
- **Purpose**: DB provides fast queries and indexing; JSONL provides audit trail and legal truth
- **Sync**: Services maintain DB mirror by reading JSONL and updating DB

**Example**: `ide/db/` (SQLite) mirrors `ide/receipts/` (JSONL)

### Watermarks

**Per-consumer watermarks** track processing progress for streaming consumers.

- **Path**: `{plane}/evidence/watermarks/{consumer-id}/`
- **Purpose**: Enable idempotent processing and resume from last processed position
- **Format**: JSON file with timestamp, offset, or sequence number

**Example**: `tenant/{tenant-id}/{region}/evidence/watermarks/evidence-indexer/watermark.json`

### Dead Letter Queue (DLQ)

**DLQ paths** store unprocessable or invalid data.

- **IDE Plane**: `ide/receipts/{repo-id}/quarantine/` — Invalid receipts
- **Tenant Plane**: `tenant/{tenant-id}/{region}/evidence/dlq/` — Failed evidence ingestion
- **Tenant Plane**: `tenant/{tenant-id}/{region}/ingest/dlq/` — Failed adapter ingestion

**Purpose**: Enable manual review, retry, and debugging of failed processing.

---

## Cross-Cutting Planes

The storage fabric supports four cross-cutting architectural concerns:

1. **Evidence & Audit**: Append-only evidence storage, audit trails, WORM semantics
2. **Data & Memory**: Data organization, partitioning, analytics storage
3. **Security & Supply Chain**: Security artifacts, trust stores, SBOM, supply chain attestation
4. **Observability**: Unified telemetry pattern (`{plane}/telemetry/(metrics|traces|logs)/dt=.../`)

Each concern spans multiple deployment planes, and the storage fabric provides consistent path patterns across all planes.

---

## Integration with Services

**Storage fabric does NOT**:
- ❌ Implement business logic (that's in services)
- ❌ Duplicate service responsibilities (storage is infrastructure)
- ❌ Hardcode paths (use `ZU_ROOT` environment variable)

**Storage fabric DOES**:
- ✅ Provide path structure and naming conventions
- ✅ Support environment scoping (dev/staging/prod via `ZU_ROOT`)
- ✅ Enforce data governance rules (no code/PII, no secrets, JSONL receipts)
- ✅ Support lazy creation of subfolders (parent folders in scaffold, subfolders on-demand)
- ✅ Provide partitioning patterns (`dt=`, `YYYY/MM`)

**Services** read/write to storage using canonical paths with placeholders (`{tenant-id}`, `{region}`, `{org-id}`). The storage fabric ensures consistency and governance; services implement domain logic.

---

## References

- **Implementation**: `storage-scripts/folder-business-rules.md` — Authoritative folder rules and path templates
- **Scaffold Scripts**: `storage-scripts/tools/create-folder-structure-*.ps1` — Environment-specific folder creation
- **Alignment Report**: `docs/architecture/four_plane_vs_7x4_alignment.md` — Detailed mapping to 7×4 architecture

