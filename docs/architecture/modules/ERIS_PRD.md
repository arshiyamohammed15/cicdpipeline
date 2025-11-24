# Evidence & Receipt Indexing Service (ERIS) – Final PRD

## 1. Module Overview

**Name:** Evidence & Receipt Indexing Service (ERIS)  
**Type:** Platform Module (PM-7)  
**Primary Planes:**  
- CCP-3 Evidence & Audit Plane  
- CCP-1 Identity & Trust Plane  
- CCP-2 Policy & Configuration Plane  
- CCP-4 Observability & Reliability Plane  

**One-line definition:**  
A service that **ingests, validates, indexes, and serves receipts and evidence** produced across the ZeroUI system, backed by an immutable, append-only audit log with cryptographic integrity guarantees and multi-tenant isolation.

Receipts are the **source of truth** for “who/what did what, where, when, under which policy, with what result”.

---

## 2. Problem Statement

ZeroUI is receipts-first: every privileged or risk-bearing decision (gates, nudges, AI actions, releases, overrides) must emit a **receipt**.  

Without ERIS, receipts are:

- Emitted in various places (Edge Agent, gateways, backend services) as **append-only JSONL** and logs.
- Not **centrally indexed**, so:
  - You cannot reliably answer questions like **“Show all high-risk overrides for Tenant X last 7 days”** or **“Which AI actions used Policy Y?”**.
  - Incident/RCA, compliance review, or ROI calculations require ad-hoc log digging.

ERIS solves this by providing a **central, logically single index** over all receipts and ensuring immutability, integrity, and governed access.

---

## 3. Goals & Non-Goals

### 3.1 Goals

1. **Single logical evidence index** for all receipts (decisions, nudges, AI calls, overrides, policy changes, system events).
2. **Immutable, append-only guarantees** for stored receipts (no update/delete; only logical tombstones or retention expiry).
3. **Fast, structured queries** across receipts:
   - By tenant, actor, repo, policy, time window, decision outcome, severity, module, plane, environment, etc.
4. **Cryptographic integrity** of stored receipts:
   - Hash chaining within well-defined chains and signature verification against KMS/Trust Stores, with KID-based key resolution.
5. **Multi-tenant isolation**:
   - Strict separation and access control at tenant boundary.
6. **Evidence substrate** for:
   - MMM Engine, Detection Engine, Trust-as-Capability, Tenant Admin Portal, Product Ops Portal, ROI Dashboards.
7. **Enterprise-grade observability & operations**:
   - Health, metrics, alerts, retention/archival, and integrity checks.
8. **Metadata-only evidence**:
   - Receipts contain only governed metadata, never raw secrets, PII, or source code.

### 3.2 Non-Goals

1. **Not** a general purpose log analytics platform.
2. **Not** a replacement for observability logs or traces; those live in CCP-4. ERIS focuses on **receipts/evidence**, not all logs.
3. **Not** the raw storage of Edge Agent local JSONL—those remain the **source of truth at the Edge**; ERIS indexes **shipped** receipts.

---

## 4. Scope

### 4.1 In-Scope

- Receipt ingestion from:
  - Edge Agents (via backend ingestion endpoints).
  - Backend services (Detection Engine, LLM Gateway, MMM, etc.).
- Validation & normalisation of incoming receipts (including metadata-only constraints).
- Persistence into an **append-only evidence store** (e.g., table or log).
- Indexes and query APIs for:
  - Compliance / security / tenant admins.
  - Internal engines (MMM, Trust, Detection, ROI).
- Basic aggregation APIs (counts, grouped by dimensions) for downstream modules.
- Retention, archival, and legal hold flags based on Data Governance & BCDR policies.
- Integrity verification (hash-chains + signatures).
- Meta-audit of access to receipts.

### 4.2 Out-of-Scope

- Advanced BI visualisations (these live in dashboards / portals).
- Real-time stream processing for ML feature pipelines (can read from ERIS as a data source later).
- Direct external-tenant self-service UI (served via Tenant Admin / ROI modules).

---

## 5. Personas & Primary Use Cases

### 5.1 Personas

1. **Developer / Engineer (End-User)**  
   - Needs: see “why” a gate blocked/warned, show last decisions for their repo/branch/PR.
2. **Tenant Admin / Engineering Manager**  
   - Needs: view compliance with policies, override patterns, risk posture, tenant-level receipts.
3. **Security / Compliance Officer**  
   - Needs: tamper-proof audit trail, quickly fetch evidence for audits / incidents.
4. **ZeroUI Product Ops / SRE**  
   - Needs: troubleshoot module behaviour, verify receipts flow, correlate incidents.
5. **System Modules (MMM, Detection, Trust, ROI)**  
   - Need programmatic access to historical evidence for analysis and recommendations.

### 5.2 Core Use Cases (Illustrative)

- UC-1: “Show all release decisions for repo _R_ in last 24 hours with severity ≥ WARNING.”
- UC-2: “List all overrides of policy **POL-PR-SIZE-500LOC** by tenant _T_ in last 30 days.”
- UC-3: “For incident _I_, retrieve full receipt chain: detection → MMM decision → AI call receipts → overrides.”
- UC-4: “Compute baseline: number of hard blocks vs passes per week, per tenant.”
- UC-5: “Verify no audit trail gaps: monotonic receipt IDs and hash-chain continuity within each chain.”

---

## 6. Functional Requirements

### FR-1: Receipt Ingestion

- ERIS **must accept** receipts via:
  - Internal HTTP/HTTPS API endpoints (from backend services).
  - Courier batch ingestion endpoint (see FR-10).
  - **Note:** Async message bus ingestion is **out of scope** for initial implementation. Future versions may support async message bus ingestion with the following requirements:
    - Message bus technology: TBD (e.g., Kafka, RabbitMQ, AWS SQS).
    - Message format: JSON-encoded receipt (same as HTTP API).
    - Delivery guarantees: At-least-once delivery (idempotency handled by `receipt_id`).
    - Error handling: Failed messages written to DLQ (see FR-2 for DLQ specification).
- Each receipt is a **single, self-contained JSON document** conforming to the canonical receipt schema defined in `docs/architecture/receipt-schema-cross-reference.md`. Required fields include:

  - `receipt_id` (unique per receipt, UUID format).
  - `gate_id` (gate identifier, e.g., 'edge-agent', 'detection-engine-core').
  - `policy_version_ids` (array of policy version IDs).
  - `snapshot_hash` (SHA256 hash of policy snapshot, format: `sha256:hex`).
  - `timestamp_utc` (ISO 8601 UTC timestamp).
  - `timestamp_monotonic_ms` (hardware monotonic timestamp in milliseconds).
  - `evaluation_point` (enum: `pre-commit`, `pre-merge`, `pre-deploy`, `post-deploy`).
  - `inputs` (metadata-only JSON object; see FR-2).
  - `decision` (nested object containing):
    - `decision.status` (enum: `pass`, `warn`, `soft_block`, `hard_block`).
    - `decision.rationale` (human-readable explanation string).
    - `decision.badges` (array of badge strings).
  - `result` (metadata-only JSON object with operation results).
  - `actor` (nested object containing):
    - `actor.repo_id` (repository identifier, required).
    - `actor.machine_fingerprint` (optional machine fingerprint).
    - `actor.type` (optional: `human`, `ai_agent`, `service`).
  - `evidence_handles` (optional array of evidence references).
  - `degraded` (boolean flag indicating degraded mode operation).
  - `signature` (cryptographic signature, required).
  - `schema_version` (schema version identifier, e.g., semantic versioning string).

- Additional fields for ERIS indexing and integrity:
  - `tenant_id` (derived from receipt metadata or IAM context; required for multi-tenant isolation).
  - `plane` (e.g., `laptop`, `tenant_cloud`, `product_cloud`, `shared_services`).
  - `environment` (e.g., `dev`, `staging`, `prod`).
  - `module_id` (module identifier, if distinct from `gate_id`).
  - `resource_type` and `resource_id` (e.g., repo, branch, PR, deployment; extracted from `inputs` or `result`).
  - `severity` (optional, module-specific extension; not in base canonical schema).
  - `risk_score` (optional, module-specific extension; not in base canonical schema).
  - Cryptographic integrity fields:
    - `hash` (hash of this record's canonical representation).
    - `prev_hash` (hash of previous record in the chain).
    - `chain_id` (logical chain/stream identifier; see FR-4 for formula).
    - `signature_algo` (signature algorithm identifier, if signed).
    - `kid` (Key ID for resolving verification key in KMS/Trust Stores).
  - Receipt linking fields (optional, for multi-step flows):
    - `parent_receipt_id` (optional, links to parent receipt in flow).
    - `related_receipt_ids` (optional array, links to related receipts).

- **Note:** ERIS accepts receipts in the canonical schema format. Fields like `severity` and `risk_score` are module-specific extensions and may not be present in all receipts.
- **Tenant ID Derivation Algorithm:**
  - ERIS derives `tenant_id` using the following algorithm (in order of precedence):
    1. **Primary:** Extract from receipt metadata:
       - If receipt contains explicit `tenant_id` field in metadata/annotations, use it.
       - If `actor.repo_id` is present, resolve tenant via repository-to-tenant mapping (from IAM or configuration).
    2. **Fallback:** Extract from IAM context:
       - If receipt is ingested via authenticated API, extract `tenant_id` from IAM token claims (`tenant_id` claim in JWT).
    3. **Error:** If `tenant_id` cannot be determined:
       - Reject receipt with validation error: "tenant_id cannot be determined from receipt metadata or IAM context".
       - Log rejection for audit and troubleshooting.
  - Tenant ID derivation is deterministic: same receipt with same context always produces same `tenant_id`.

- Incoming receipts are **never mutated** after acceptance.

### FR-2: Validation, Normalisation & Metadata-Only Enforcement

- ERIS **must validate** incoming receipts against a central, versioned JSON Schema retrieved from **Contracts & Schema Registry (M34)**.
- **Schema Lookup Integration:**
  - ERIS queries Contracts & Schema Registry to retrieve schema by `schema_version`.
  - API contract: `GET /registry/v1/schemas/{schema_name}/versions/{schema_version}` (or equivalent).
  - If schema is not found in Contracts & Schema Registry, ERIS must reject the receipt with structured error.
  - ERIS caches schemas for performance but must refresh on schema updates (TTL-based or event-driven).
- **Validation includes:**
  - Required fields and value types per canonical schema.
  - Enum domains (e.g., `decision.status`, `evaluation_point`, `plane`, `environment`, `actor.type`).
  - **Metadata-only payload rule**:
    - `inputs` and `result` fields MUST contain only metadata fields that are explicitly allowed by Data Governance & Privacy (M22) and Contracts & Schema Registry (M34).
    - Raw source code, secrets, access tokens, stack traces with PII, or user content are forbidden.
    - Where a reference is needed, only hashed or tokenised identifiers may be stored.
    - ERIS may delegate validation to Data Governance & Privacy module's classification service for payload content validation.
- **Invalid receipts:**
  - Are **rejected** with structured error response (see Section 9.9 for error response schema).
  - Error response includes: validation failure reason, field path, expected vs actual value.
- **Dead Letter Queue (DLQ):**
  - Invalid receipts that fail validation are written to a DLQ for investigation and troubleshooting.
  - DLQ storage:
    - Location: Append-only log file or dedicated DLQ table/queue.
    - Format: JSONL format (one invalid receipt per line) with rejection reason and timestamp.
  - DLQ retention policy:
    - Default retention: 30 days (configurable per tenant).
    - DLQ entries are subject to same retention policies as normal receipts (Data Governance).
  - DLQ monitoring:
    - DLQ size and growth rate are monitored via metrics.
    - Alerts triggered when DLQ size exceeds threshold or growth rate is abnormal.
  - DLQ replay:
    - DLQ entries can be queried and replayed (after fixing validation issues) via admin API.
    - Replay preserves original `receipt_id` and timestamp for audit trail.
- ERIS **must normalise**:
  - Timestamps to canonical format (`timestamp_utc` as ISO 8601, `timestamp_monotonic_ms` as integer).
  - Enum values (`decision.status`, `evaluation_point`, `actor.type`, `plane`, `environment`).
  - Policy IDs and module IDs to canonical strings.
- **Schema version support:**
  - Each receipt carries `schema_version` (format: semantic versioning string, e.g., `"1.0.0"`).
  - ERIS maintains backward-compatible parsing where feasible:
    - Schema version `1.x.y` receipts are accepted if ERIS supports version `1.z.w` where `z >= x`.
    - Breaking changes (major version bump) require explicit migration handling.
  - **Unknown schema versions:**
    - If `schema_version` is not supported and backward compatibility cannot be determined, ERIS must reject the receipt.
    - ERIS logs unknown schema versions for monitoring and schema registry updates.
- **Schema evolution handling:**
  - ERIS must support schema migration for backward compatibility:
    - Missing optional fields in older schema versions are handled gracefully.
    - New required fields in newer schema versions cause rejection of older receipts without those fields.
  - Migration strategy is defined per schema version in Contracts & Schema Registry.

### FR-3: Append-Only Evidence Store

- Receipts are persisted in an **append-only store**:
  - No in-place UPDATE or DELETE; only insertion and logical masking/retention markers.
- ERIS must:
  - Enforce write-once semantics for `receipt_id`.
  - Support idempotent ingestion (receiving same `receipt_id` twice does not create duplicates).
- Storage must support:
  - Partitioning by `dt` (e.g., event date) to enable efficient retention and queries.
  - Per-consumer watermarks (e.g., last processed `receipt_id`/timestamp) for downstream consumers reading from ERIS.

### FR-4: Cryptographic Integrity & Signature Verification

- For each logical **chain** of receipts, ERIS must maintain a **hash chain**:
  - Each receipt’s `prev_hash` equals the `hash` of the previous receipt in that chain.
- **Chain scope (`chain_id`):**
  - `chain_id` identifies a logical stream, defined by the formula:
    - `{tenant_id}:{plane}:{environment}:{emitter_service}`
    - Where:
      - `tenant_id`: Tenant identifier (required).
      - `plane`: Plane identifier (e.g., `laptop`, `tenant_cloud`, `product_cloud`, `shared_services`).
      - `environment`: Environment identifier (e.g., `dev`, `staging`, `prod`).
      - `emitter_service`: Service/module that emitted the receipt (e.g., `detection-engine`, `mmm-engine`, `edge-agent`).
    - Example: `tenant-123:product_cloud:prod:detection-engine`
  - Ordering is guaranteed **within a chain**, but **not across chains**.
  - Chain ID generation rules:
    - All components must be non-empty strings.
    - Components are normalized (lowercase, no special characters except hyphens/underscores).
    - Chain ID is deterministic: same inputs produce same chain_id.
- ERIS must:
  - Persist chain heads as integrity anchors.
  - Provide internal tools/APIs to verify chain continuity over a range of receipts (per `chain_id`).
- **Signature verification (integration with KMS/Trust Stores):**
  - If a receipt includes `signature` and `kid`:
    - ERIS must resolve the key via Key & Trust Management (KMS & Trust Stores).
    - Verify the signature against the canonical serialisation of the receipt.
    - Reject receipts signed by revoked/unknown KIDs according to KMS policy, or mark them as untrusted according to a configurable policy.
  - ERIS must record signature verification outcome as part of stored metadata.
- Integrity APIs (see Section 9) must be able to:
  - Verify the integrity of a single receipt (hash + optional signature).
  - Verify the integrity of a range of receipts within a chain (hash-chain continuity).

### FR-5: Indexing & Query APIs

- ERIS must maintain indexes for common query dimensions, including at least:
  - `tenant_id`
  - `plane`
  - `environment`
  - `actor.repo_id`, `actor.type` (note: actor fields are nested in canonical schema)
  - `gate_id`, `module_id`
  - `policy_version_ids`
  - `decision.status` (note: decision.status is nested in canonical schema)
  - `severity` (module-specific extension, if present)
  - `resource_type`, `resource_id`
  - `timestamp_utc` / `dt` (note: timestamp_utc is the canonical field name)
  - `chain_id` (for hash chain queries)
  - `parent_receipt_id`, `related_receipt_ids` (for receipt linking queries)
- Provide internal APIs:
  - `GET /v1/evidence/receipts/{receipt_id}`
  - `POST /v1/evidence/search`
    - Filterable by: time range, tenant, plane, environment, actor, module/gate, policy, decision, severity, resource, etc.
    - Cursor-based pagination for large result sets.
  - `POST /v1/evidence/aggregate`
    - Example aggregations:
      - Counts grouped by `decision.status` and day (note: aggregates on nested `decision.status` field).
      - Counts of overrides per `policy_version_id`.
      - Distributions of severities by module.

### FR-6: Multi-Tenant Isolation & Access Control

- Every receipt is tagged with `tenant_id`.
- **IAM Integration:**
  - ERIS integrates with **IAM (M21)** for authentication and authorization:
    - **Token verification:**
      - API contract: `POST /iam/v1/verify` (or equivalent).
      - ERIS validates JWT tokens on all API requests.
      - Token must include: `sub` (subject), `tenant_id`, `roles`, `permissions`.
    - **Access decision evaluation:**
      - API contract: `POST /iam/v1/decision` (or equivalent).
      - ERIS queries IAM for access decisions on query operations.
      - IAM evaluates RBAC/ABAC policies and returns allow/deny decision.
    - **Role requirements:**
      - Tenant-scoped queries: Require IAM role with `evidence:read` permission for the tenant.
      - System-wide, multi-tenant queries: Require IAM role `product_ops` or `admin` with `evidence:read:all` permission.
      - Export operations: Require IAM role with `evidence:export` permission.
      - Ingestion operations: Require IAM role with `evidence:write` permission (typically service-to-service).
- Query APIs:
  - MUST enforce that callers only see receipts for tenants they are authorised for under IAM.
  - System-wide, multi-tenant queries (for ZeroUI Product Ops) require elevated, audited permissions (IAM role `product_ops` or `admin`).
  - Access patterns (who queried what) must be controlled and traceable (via meta-receipts per FR-9).

### FR-7: Retention, Archival & Legal Hold

- Retention policy is driven by **Data Governance & Privacy (M22)** + **BCDR** modules:
  - Per-tenant retention durations.
  - Legal hold flags per tenant or per incident.
- **Data Governance Integration:**
  - ERIS queries Data Governance & Privacy module for retention policies:
    - API contract: `GET /privacy/v1/retention/policies?tenant_id={tenant_id}` (or equivalent).
    - Retention policy includes: retention duration, archival rules, deletion rules.
  - ERIS must handle retention policy changes:
    - When retention policy is updated for a tenant, ERIS re-evaluates existing receipts.
    - Receipts that should be archived/expired are marked accordingly.
    - Re-evaluation is triggered by:
      - Periodic background job (e.g., daily).
      - Event notification from Data Governance module (preferred).
  - **Legal hold management:**
    - ERIS receives legal hold flags from Data Governance & Privacy module:
      - API contract: `GET /privacy/v1/legal-holds?tenant_id={tenant_id}` (or equivalent).
      - Event-driven: ERIS subscribes to legal hold events (set/clear).
    - Legal hold flags can be set per tenant or per incident (identified by receipt metadata).
    - When legal hold is active:
      - Receipts cannot be archived or deleted even if retention period expires.
      - Export operations must include legal hold metadata.
      - Legal hold status is included in receipt metadata.
- ERIS must:
  - Mark receipts as "archived" or "expired" according to retention policy.
  - Support export of evidence segments for long-term archival (e.g., to WORM storage; see FR-11).
  - Preserve append-only properties while receipts are under required retention or legal hold.
  - Log retention policy lookups and legal hold status changes for audit.

### FR-8: Integrations with Other Modules

- ERIS must support:
  - Writes from Detection Engine, MMM Engine, LLM Gateway, Integration Adapters, and other platform modules.
  - Reads from Trust-as-a-Capability, ROI, Tenant Admin, Product Ops, RCA flows, etc.
- **Receipt linking for multi-step flows:**
  - ERIS supports linking receipts into **logical chains** representing multi-step flows:
    - e.g., detection receipt → MMM decision → AI call receipts → override receipts → deployment receipt.
  - Receipt linking fields (optional in receipt schema):
    - `parent_receipt_id`: Links to the parent receipt in the flow (e.g., detection receipt is parent of MMM decision).
    - `related_receipt_ids`: Array of related receipt IDs (e.g., multiple AI call receipts related to one MMM decision).
  - **Note:** Receipt linking (logical chains) is distinct from hash chains (`chain_id`):
    - Hash chains (`chain_id`) ensure cryptographic integrity within a logical stream.
    - Receipt linking (`parent_receipt_id`, `related_receipt_ids`) represents business flow relationships.
  - ERIS maintains indexes on `parent_receipt_id` and `related_receipt_ids` for efficient chain traversal queries.

### FR-9: Meta-Audit of Access

- Every **read or export operation** on receipts MUST emit a **meta-receipt** (access audit event), stored in ERIS like any other receipt, containing at least:
  - `access_event_id` (unique identifier for the access event).
  - `requester_actor_id` and `actor_type` (extracted from IAM token/context).
  - `requester_role` / permission context (IAM role and permissions used).
  - `tenant_id`(s) accessed (array of tenant IDs queried).
  - `plane` and `environment` context (if applicable).
  - `timestamp` (when the access occurred).
  - High-level description of query scope (e.g., filters used or export scope, not full query details to avoid PII leakage).
  - `decision` / outcome (enum: `success`, `denied`, `partial`).
  - `receipt_count` (number of receipts accessed, if applicable).
- These meta-receipts must be queryable and subject to the same retention and integrity rules as normal receipts.
- Meta-receipts are stored via the same ingestion path as normal receipts (or via a privileged internal path that still lands in ERIS).

### FR-10: Courier Batch Ingestion

- ERIS **must support** courier batch ingestion from CCCS (PM-2) and other modules that use courier pattern for offline-first receipt delivery.
- **Courier batch ingestion API:**
  - `POST /v1/evidence/receipts/courier-batch`
  - Body: Courier batch JSON containing:
    - `batch_id` (unique batch identifier).
    - `tenant_id` (tenant identifier).
    - `emitter_service` (service that emitted the batch).
    - `sequence_numbers` (array of sequence numbers for receipts in batch, for deduplication).
    - `merkle_root` (Merkle root hash of the batch for tamper-evidence).
    - `receipts` (array of receipt JSON documents).
    - `timestamp` (batch creation timestamp).
  - Behaviour:
    - Validates batch structure and Merkle root.
    - Ensures idempotent batch ingestion (same `batch_id` processed only once).
    - Deduplicates receipts within batch using `receipt_id` and `sequence_numbers`.
    - Persists batch metadata for Merkle proof generation.
    - Returns 200 with `batch_id` and ingestion status, or 4xx with validation error details.
- **Merkle proof generation:**
  - `GET /v1/evidence/courier-batches/{batch_id}/merkle-proof`
  - Returns Merkle proof for the batch, enabling tamper-evidence verification.
  - Proof includes: Merkle root, leaf hashes, path to root.
- **Batch metadata storage:**
  - ERIS persists courier batch metadata:
    - `batch_id`, `tenant_id`, `emitter_service`, `merkle_root`, `sequence_numbers`, `receipt_count`, `timestamp`.
  - Batch metadata is queryable for audit and troubleshooting.

### FR-11: Export API

- ERIS **must provide** export APIs for BCDR archival and compliance evidence export.
- **Export API:**
  - `POST /v1/evidence/export`
  - Request:
    - `tenant_id` (required unless caller is privileged multi-tenant role).
    - Export scope:
      - Time range (`from`, `to`).
      - Filters (same as search API: plane, environment, gate_id, module_id, policy_version_ids, decision, severity, actor, resource, etc.).
      - `chain_id` (optional, export specific chain).
    - Export format (enum: `jsonl`, `csv`, `parquet`; default: `jsonl`).
    - Export options:
      - `include_metadata` (boolean, include ERIS metadata like chain_id, hash, etc.).
      - `include_signatures` (boolean, include receipt signatures).
      - `compression` (enum: `none`, `gzip`, `zip`; default: `gzip`).
  - Response:
    - `export_id` (unique export job identifier).
    - `status` (enum: `pending`, `processing`, `completed`, `failed`).
    - `download_url` (when completed, temporary signed URL for download).
    - `export_metadata`:
      - `receipt_count` (number of receipts exported).
      - `export_format`, `compression`, `file_size`, `checksum` (SHA256).
      - `export_timestamp`, `expires_at` (download URL expiration).
  - Behaviour:
    - Export operations are asynchronous for large datasets.
    - Export respects Data Governance constraints (legal hold, retention, access control).
    - Export generates meta-receipt per FR-9.
    - Export files are stored temporarily (TTL-based cleanup) or streamed directly.
- **Export status API:**
  - `GET /v1/evidence/export/{export_id}`
  - Returns export job status and download URL when completed.

### FR-12: Receipt Chain Traversal

- ERIS **must support** querying receipt chains (logical flows) using receipt linking fields.
- **Chain traversal API:**
  - `GET /v1/evidence/receipts/{receipt_id}/chain`
    - Returns all receipts in the chain starting from the specified receipt:
      - Follows `parent_receipt_id` links upward (ancestors).
      - Follows `related_receipt_ids` links (siblings).
      - Optionally follows child receipts (where this receipt is `parent_receipt_id`).
    - Query parameters:
      - `direction` (enum: `up` (ancestors), `down` (descendants), `both`, `siblings`; default: `both`).
      - `max_depth` (integer, limit traversal depth; default: 10).
      - `include_metadata` (boolean, include ERIS metadata).
  - `POST /v1/evidence/receipts/chain-query`
    - Query receipts by chain relationships:
      - `root_receipt_id` (find all receipts in chain starting from root).
      - `flow_id` (if receipts are tagged with flow identifiers).
      - Filters (same as search API).
    - Returns all receipts in the chain matching filters.
- **Chain integrity:**
  - ERIS validates receipt chain integrity:
    - `parent_receipt_id` must reference an existing receipt.
    - Circular references are detected and logged as warnings.
    - Orphaned receipts (parent_receipt_id pointing to non-existent receipt) are flagged.

---

## 7. Non-Functional Requirements

### NFR-1: Reliability & Durability

- ERIS must provide high availability for its internal consumers (reads and writes).
- Writes must be durable:
  - Once a receipt is acknowledged, it must survive node failures and routine maintenance.
- Data is replicated according to BCDR policies.

### NFR-2: Integrity & Immutability

- Append-only model enforced by:
  - Application layer.
  - Data layer (no update/delete paths).
- Cryptographic integrity:
  - Hash chains and optional signatures must be verifiable through integrity APIs.
  - Periodic background integrity checks should be possible (implementation detail / operational runbook).

### NFR-3: Security & Privacy

- All APIs over TLS.
- Fine-grained RBAC tied to IAM.
- No secrets, PII or raw source content in receipts:
  - Enforced by schema + validation + Data Governance policies.
- Export functions must respect Data Governance constraints.
- **Rate Limiting:**
  - ERIS implements rate limiting per tenant and per endpoint to prevent abuse and ensure fair resource usage.
  - Rate limits (configurable, defaults below):
    - Ingestion endpoints (`POST /v1/evidence/receipts`, `/bulk`, `/courier-batch`):
      - Default: 1000 requests per second per tenant.
      - Burst: 2000 requests for 10 seconds.
    - Query endpoints (`POST /v1/evidence/search`, `/aggregate`):
      - Default: 100 requests per second per tenant.
      - Burst: 200 requests for 10 seconds.
    - Export endpoints (`POST /v1/evidence/export`):
      - Default: 10 concurrent exports per tenant.
      - Rate: 5 export requests per minute per tenant.
    - Integrity endpoints (`GET /v1/evidence/receipts/{receipt_id}/verify`, `POST /verify_range`):
      - Default: 500 requests per second per tenant.
  - Rate limit enforcement:
    - Exceeding rate limit returns HTTP 429 (Too Many Requests).
    - Response includes `Retry-After` header with seconds to wait.
    - Rate limit status included in response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
  - Rate limits are monitored and can be adjusted per tenant based on usage patterns.

### NFR-4: Performance & SLOs

- ERIS must define **documented SLOs** for:
  - Ingestion latency.
  - Query latency (search/aggregate).
  - Availability.
- SLOs:
  - Must be agreed between Architecture, Product, and Operations.
  - Must be continuously monitored via the Observability & Reliability Plane.
- This PRD **does not fix numeric thresholds**; those are set via configuration/SLO docs and may vary per deployment tier (e.g., internal vs tenant-facing).

### NFR-5: Observability

- ERIS emits:
  - Structured logs for ingestion, validation failures, query performance, and integrity checks.
  - Metrics:
    - Ingestion rate.
    - Validation error counts.
    - Query latency distributions.
    - Integrity-check results.
  - Traces:
    - Integrated with the platform’s OpenTelemetry setup.
- Observability data must be sufficient to:
  - Detect ingestion backlogs early.
  - Identify slow queries.
  - Investigate integrity failures.

### NFR-6: Resilience

- ERIS must be resilient to:
  - Store node failures.
  - Service restarts.
- Required behaviours:
  - No duplicate receipts under normal failover scenarios (idempotent ingestion).
  - No loss of acknowledged receipts.
  - Hash chains remain consistent after recovery.

---

## 8. Data Model (Conceptual)

### 8.1 Receipt Record (Core)

Key fields (conceptual; concrete schema defined in Contracts & Schema Registry and canonical schema in `docs/architecture/receipt-schema-cross-reference.md`):

**Canonical Receipt Fields (from receipt schema):**
- Identification:
  - `receipt_id` (PK, UUID)
  - `gate_id` (gate identifier)
  - `schema_version` (semantic versioning string)
- Policy:
  - `policy_version_ids` (array of strings)
  - `snapshot_hash` (SHA256 hash, format: `sha256:hex`)
- Time:
  - `timestamp_utc` (ISO 8601 UTC timestamp)
  - `timestamp_monotonic_ms` (integer, hardware monotonic timestamp)
- Evaluation:
  - `evaluation_point` (enum: `pre-commit`, `pre-merge`, `pre-deploy`, `post-deploy`)
- Decision:
  - `decision.status` (enum: `pass`, `warn`, `soft_block`, `hard_block`)
  - `decision.rationale` (string)
  - `decision.badges` (array of strings)
- Actor:
  - `actor.repo_id` (string, required)
  - `actor.machine_fingerprint` (string, optional)
  - `actor.type` (enum: `human`, `ai_agent`, `service`, optional)
- Data:
  - `inputs` (JSON object, metadata-only)
  - `result` (JSON object, metadata-only)
  - `evidence_handles` (array of evidence references, optional)
- Operational:
  - `degraded` (boolean)
  - `signature` (string, cryptographic signature)

**ERIS-Specific Indexing Fields:**
- Multi-tenant:
  - `tenant_id` (derived from receipt metadata or IAM context)
- Context:
  - `plane` (`laptop`, `tenant_cloud`, `product_cloud`, `shared_services`, etc.)
  - `environment` (`dev`, `staging`, `prod`, etc.)
- Module / Gate:
  - `module_id` (if distinct from `gate_id`)
- Resource:
  - `resource_type` (`repo`, `branch`, `pr`, `deployment`, etc.; extracted from `inputs` or `result`)
  - `resource_id` (extracted from `inputs` or `result`)
- Module-specific extensions (optional):
  - `severity` (not in base canonical schema)
  - `risk_score` (numeric, not in base canonical schema)
- Cryptographic integrity:
  - `hash` (hash of canonical serialisation of the receipt)
  - `prev_hash` (hash of previous record in the same `chain_id`)
  - `chain_id` (logical stream ID; formula: `{tenant_id}:{plane}:{environment}:{emitter_service}`)
  - `signature_algo` (signature algorithm identifier, if signed)
  - `kid` (Key ID to resolve verification key)
  - `signature_verification_status` (e.g., `verified`, `failed`, `not_present`, `kid_revoked`)
- Receipt linking (optional):
  - `parent_receipt_id` (links to parent receipt in flow)
  - `related_receipt_ids` (array, links to related receipts)
- Source:
  - `source_plane` / `emitter_service` (if needed distinct from `plane`)
  - `ingest_source` (which ERIS ingestion endpoint / pipeline)
- Time partitioning:
  - `dt` (partition key derived from `timestamp_utc` date component, e.g., `YYYY-MM-DD`)
- Retention:
  - `retention_state` (`active`, `archived`, `expired`)
  - `legal_hold` (boolean)

### 8.2 Index Structures

Logical indexes (implementation-specific tuning left to design, but functionally required):

- Primary index:
  - `(tenant_id, receipt_id)`
  - or `(tenant_id, timestamp_utc, receipt_id)` depending on chosen store.
- Secondary indexes:
  - `(tenant_id, dt, plane, environment)`
  - `(tenant_id, gate_id, dt)`
  - `(tenant_id, module_id, dt)`
  - `(tenant_id, policy_version_ids[], dt)` (implementation may need special handling for arrays).
  - `(tenant_id, actor.repo_id, dt)` (note: actor is nested object)
  - `(tenant_id, resource_type, resource_id, dt)`
  - `(tenant_id, decision.status, severity, dt)` (note: decision.status is nested)
  - `(tenant_id, chain_id, timestamp_utc)` (for chain queries)
  - `(parent_receipt_id)` (for receipt chain traversal)
  - `(related_receipt_ids[])` (for receipt chain traversal; array index)

Downstream consumers may maintain watermarks (last processed `receipt_id`/`timestamp_utc`) per `tenant_id`/`chain_id`.

### 8.3 Courier Batch Metadata

- `batch_id` (PK)
- `tenant_id`
- `emitter_service`
- `merkle_root` (Merkle root hash)
- `sequence_numbers` (array)
- `receipt_count` (integer)
- `timestamp` (batch creation timestamp)
- `status` (enum: `pending`, `processing`, `completed`, `failed`)

---

## 9. Interfaces & APIs (High Level)

### 9.1 Ingestion API (HTTP)

`POST /v1/evidence/receipts`

- Body: single receipt JSON.
- Behaviour:
  - Validate against schema (including metadata-only payload constraint).
  - Verify signature if present:
    - Resolve `kid` via KMS/Trust Stores.
    - Verify signature according to `signature_algo`.
    - Apply KMS policy for revoked/unknown keys.
  - Ensure idempotency by `receipt_id`.
  - Persist to append-only store with hash-chain updates.
  - Return 200 with `receipt_id` and verification status, or 4xx with validation error details.

Optional bulk variant:

`POST /v1/evidence/receipts/bulk`

- Body: array of receipts.
- Semantics: defined in design (all-or-nothing vs per-item), but must preserve idempotency and integrity guarantees.

### 9.2 Query API

`POST /v1/evidence/search`

- Request:
  - `tenant_id` (required unless caller is privileged multi-tenant role).
  - Optional filters:
    - `plane`, `environment`
    - Time range (`from`, `to`; based on `timestamp_utc`)
    - `gate_id`, `module_id`
    - `policy_version_ids`
    - `decision.status` (enum: `pass`, `warn`, `soft_block`, `hard_block`; note: filters on nested `decision.status` field)
    - `severity` (module-specific extension, if present)
    - `actor.repo_id` (note: filters on nested `actor.repo_id` field)
    - `actor.type` (enum: `human`, `ai_agent`, `service`; note: filters on nested `actor.type` field)
    - `resource_type`, `resource_id`
    - `chain_id` (filter by hash chain)
    - `parent_receipt_id` (filter by receipt linking)
  - Pagination:
    - `cursor`, `limit`.
- Response:
  - Page of receipts (in canonical schema format) + next cursor.

`POST /v1/evidence/aggregate`

- Common aggregations:
  - Counts grouped by `decision.status` and day (note: aggregates on nested `decision.status` field).
  - Counts of overrides per `policy_version_id`.
  - Counts per `module_id` / `gate_id` per time bucket.
  - Distributions of `decision.status` by `gate_id`, `module_id`, `tenant_id`.
  - Aggregations by `actor.type`, `plane`, `environment`.

### 9.3 Integrity API

`GET /v1/evidence/receipts/{receipt_id}/verify`

- Verifies:
  - Hash integrity of this receipt.
  - Signature verification (if applicable).
- Returns:
  - `hash_valid`, `signature_valid`, `signature_verification_status`.

`POST /v1/evidence/verify_range`

- Input:
  - `tenant_id`, `chain_id`, `from_timestamp`, `to_timestamp` (or `from_receipt_id`/`to_receipt_id`).
- Behaviour:
  - Verify hash-chain continuity for the receipts in that range.
- Returns:
  - Summary of any gaps or mismatches.

### 9.4 Courier Batch Ingestion API

`POST /v1/evidence/receipts/courier-batch`

- Body: Courier batch JSON (see FR-10 for structure).
- Behaviour:
  - Validates batch structure and Merkle root.
  - Ensures idempotent batch ingestion.
  - Deduplicates receipts within batch.
  - Persists batch metadata.
  - Returns 200 with `batch_id` and ingestion status, or 4xx with validation error details.

`GET /v1/evidence/courier-batches/{batch_id}/merkle-proof`

- Returns Merkle proof for the batch.
- Response includes: Merkle root, leaf hashes, path to root.

### 9.5 Export API

`POST /v1/evidence/export`

- Request: Export parameters (see FR-11 for details).
- Response: `export_id`, `status`, `download_url` (when completed), `export_metadata`.
- Behaviour:
  - Asynchronous export for large datasets.
  - Respects Data Governance constraints.
  - Generates meta-receipt per FR-9.

`GET /v1/evidence/export/{export_id}`

- Returns export job status and download URL when completed.

### 9.6 Receipt Chain Traversal API

`GET /v1/evidence/receipts/{receipt_id}/chain`

- Returns all receipts in the chain starting from the specified receipt.
- Query parameters: `direction` (up/down/both/siblings), `max_depth`, `include_metadata`.
- Response: Array of receipts in chain.

`POST /v1/evidence/receipts/chain-query`

- Query receipts by chain relationships.
- Request: `root_receipt_id` or `flow_id`, plus optional filters.
- Response: All receipts in chain matching filters.

### 9.7 Access Meta-Audit Hooks

- All query/aggregate/integrity/export/chain endpoints must:
  - Emit a **meta-receipt** per FR-9 that captures who accessed what and when.
  - Use an internal, well-defined meta-event schema stored via the same ingestion path (or via a privileged internal path that still lands in ERIS).

### 9.8 Standard Module Endpoints

`GET /v1/evidence/health`

- Returns service health status with dependency checks.
- Response:
  - `status` (enum: `healthy`, `degraded`, `unhealthy`).
  - `version` (service version).
  - `timestamp` (current server time, ISO 8601).
  - `dependencies` (object with status of each dependency):
    - `storage` (enum: `healthy`, `degraded`, `unhealthy`).
    - `iam` (enum: `healthy`, `degraded`, `unhealthy`).
    - `data_governance` (enum: `healthy`, `degraded`, `unhealthy`).
    - `contracts_schema_registry` (enum: `healthy`, `degraded`, `unhealthy`).
    - `kms` (enum: `healthy`, `degraded`, `unhealthy`).
- HTTP status codes:
  - 200: Service is healthy.
  - 503: Service is degraded or unhealthy.

`GET /v1/evidence/metrics`

- Returns Prometheus-format metrics for observability.
- Response: Prometheus text format metrics including:
  - Ingestion metrics: `eris_receipts_ingested_total`, `eris_receipts_ingestion_duration_seconds`, `eris_receipts_validation_errors_total`.
  - Query metrics: `eris_queries_total`, `eris_query_duration_seconds`, `eris_query_results_count`.
  - Storage metrics: `eris_receipts_stored_total`, `eris_storage_size_bytes`, `eris_index_size_bytes`.
  - Integrity metrics: `eris_integrity_checks_total`, `eris_integrity_failures_total`.
  - Error metrics: `eris_errors_total` (by error code).
  - Rate limiting metrics: `eris_rate_limit_exceeded_total`.
- HTTP status: 200 (always returns metrics, even if service is degraded).

`GET /v1/evidence/config`

- Returns module configuration and capabilities.
- Response:
  - `module_id`: "PM-7"
  - `module_name`: "Evidence & Receipt Indexing Service (ERIS)"
  - `version`: Service version.
  - `capabilities`: Array of supported capabilities:
    - `receipt_ingestion`, `receipt_query`, `receipt_aggregation`, `courier_batch_ingestion`, `export`, `chain_traversal`, `integrity_verification`.
  - `supported_schema_versions`: Array of supported receipt schema versions.
  - `rate_limits`: Current rate limit configuration per endpoint.
  - `storage_config`: Storage configuration (partitioning, retention, etc.).
- HTTP status: 200.

### 9.9 Error Response Schema

All error responses follow a consistent schema:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "field_path",
      "expected": "expected_value_or_type",
      "actual": "actual_value",
      "reason": "Detailed reason for error"
    },
    "retryable": false,
    "request_id": "unique_request_identifier",
    "timestamp": "2025-01-XXT00:00:00Z"
  }
}
```

**Error Codes:**
- `VALIDATION_ERROR`: Receipt validation failed (field validation, schema mismatch, etc.).
- `SCHEMA_NOT_FOUND`: Receipt schema version not found in Contracts & Schema Registry.
- `SIGNATURE_VERIFICATION_FAILED`: Signature verification failed (invalid signature, revoked key, etc.).
- `TENANT_ID_MISSING`: Tenant ID cannot be determined from receipt or IAM context.
- `DUPLICATE_RECEIPT`: Receipt with same `receipt_id` already exists (idempotency check).
- `CHAIN_INTEGRITY_FAILED`: Hash chain integrity check failed.
- `UNAUTHORIZED`: Authentication failed (missing or invalid token).
- `FORBIDDEN`: Authorization failed (insufficient permissions).
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded (HTTP 429).
- `RESOURCE_NOT_FOUND`: Requested resource (receipt, batch, export) not found.
- `INTERNAL_ERROR`: Internal server error (unexpected failure).
- `DEPENDENCY_UNAVAILABLE`: Required dependency (IAM, Data Governance, KMS, etc.) is unavailable.

**HTTP Status Code Mapping:**
- 400 Bad Request: `VALIDATION_ERROR`, `SCHEMA_NOT_FOUND`, `TENANT_ID_MISSING`, `CHAIN_INTEGRITY_FAILED`.
- 401 Unauthorized: `UNAUTHORIZED`.
- 403 Forbidden: `FORBIDDEN`.
- 404 Not Found: `RESOURCE_NOT_FOUND`.
- 409 Conflict: `DUPLICATE_RECEIPT`.
- 429 Too Many Requests: `RATE_LIMIT_EXCEEDED`.
- 500 Internal Server Error: `INTERNAL_ERROR`.
- 503 Service Unavailable: `DEPENDENCY_UNAVAILABLE`.

**Error Response Headers:**
- `X-Request-ID`: Unique request identifier for correlation.
- `Retry-After`: For rate limit errors, seconds to wait before retry.

---

## 10. Interactions with Other Modules

### 10.1 Receipt Producers (Writers)

- **CCCS (PM-2)**:
  - Receipt Generation Service (RGES) sends receipts to ERIS via courier batches (see FR-10).
  - CCCS uses ERIS courier batch ingestion API for offline-first receipt delivery.
- **Detection Engine Core**:
  - Emits decision receipts (gates, scores, outcomes) to ERIS.
- **Signal Ingestion & Normalization**:
  - Provides upstream events; its derived decisions are recorded as receipts in ERIS via Detection/MMM.
- **MMM Engine**:
  - Emits receipts for Mirror/Mentor/Multiplier interventions.
- **LLM Gateway & Safety Enforcement**:
  - Emits receipts for every AI call, including policy IDs used, safety filters applied, models, and KIDs.

### 10.2 Receipt Consumers (Readers)

- **Trust as a Capability**:
  - Queries ERIS for historical receipts to compute trust posture per actor/tenant.
- **Tenant Admin / Product Operations / ROI Dashboards**:
  - Read receipts and aggregations from ERIS to:
    - Show policy compliance.
    - Show override patterns.
    - Show ROI metrics based on decisions and outcomes.

### 10.3 Integration Modules

- **IAM (M21)**:
  - ERIS queries IAM for token verification (`POST /iam/v1/verify`) and access decisions (`POST /iam/v1/decision`).
  - IAM role requirements: `evidence:read`, `evidence:read:all`, `evidence:export`, `evidence:write`.
  - See FR-6 for detailed integration.
  - **Note:** API paths should be verified against actual IAM module implementation during integration.

- **Data Governance & Privacy (M22)**:
  - ERIS queries Data Governance for retention policies (`GET /privacy/v1/retention/policies?tenant_id={tenant_id}` or equivalent).
  - ERIS queries Data Governance for legal hold status (`GET /privacy/v1/legal-holds?tenant_id={tenant_id}` or equivalent).
  - ERIS may delegate payload content validation to Data Governance classification service (`POST /privacy/v1/classification`).
  - See FR-7 for detailed integration.
  - **Note:** Exact API paths should be verified against actual Data Governance module implementation during integration.

- **Contracts & Schema Registry (M34)**:
  - ERIS queries Contracts & Schema Registry for receipt schemas by `schema_version` (`GET /registry/v1/schemas/{schema_id}/versions/{schema_version}` or equivalent).
  - ERIS uses Contracts & Schema Registry validation service for receipt validation (`POST /registry/v1/validate`).
  - See FR-2 for detailed integration.
  - **Note:** Schema lookup API path (schema_id vs schema_name) should be verified against actual Contracts & Schema Registry implementation during integration.

- **KMS & Trust Stores (M33)**:
  - ERIS queries KMS for key metadata by `kid` (`GET /kms/v1/keys/{key_id}` or equivalent key retrieval endpoint).
  - ERIS uses KMS signature verification service (`POST /kms/v1/verify`).
  - See FR-4 for detailed integration.
  - **Note:** Key retrieval API path should be verified against actual KMS module implementation during integration. KMS may use different endpoint structure for key retrieval vs key generation.

- **BCDR / Archival processes**:
  - Use ERIS export APIs (FR-11) and dt-partitioning to archive or restore evidence.
  - BCDR queries ERIS for evidence segments based on retention policies.

---

## 11. Test Strategy & Implementation Details

### 11.1 Unit Tests

- **UT-1: Schema Validation**
  - Valid receipt → accepted, stored.
  - Missing required fields → 4xx, no write.
  - Payload with raw code/secret → rejected by metadata-only rule.

- **UT-2: Idempotent Ingestion**
  - Same `receipt_id` twice → second call returns success with no duplicate.

- **UT-3: Append-Only Enforcement**
  - Direct update through repository layer → rejected.

- **UT-4: Hash Chain Creation**
  - Insert sequence of receipts for same `chain_id` → `prev_hash` correctly set; chain verification passes.

- **UT-5: Signature Verification**
  - Valid signature with known, non-revoked `kid` → verification status `verified`.
  - Invalid signature → verification status `failed`.
  - Revoked `kid` → handled according to KMS policy (reject or mark untrusted).

- **UT-6: Access Control Guards**
  - Query without tenant context → rejected unless caller is privileged.
  - Tenant-scoped query → only tenant data returned.

- **UT-7: Courier Batch Ingestion**
  - Valid courier batch → accepted, receipts ingested, batch metadata stored.
  - Duplicate `batch_id` → idempotent handling, no duplicate receipts.
  - Invalid Merkle root → rejected with validation error.
  - Receipt deduplication within batch → duplicate `receipt_id` within batch handled correctly.
  - Sequence number validation → sequence numbers validated for consistency.

- **UT-8: Export API**
  - Export request → export job created, status `pending`.
  - Export format validation → invalid format rejected.
  - Data Governance constraint enforcement → receipts under legal hold included in export with metadata.
  - Export file generation → file created with correct format, checksum, and metadata.
  - Export download URL → temporary signed URL generated with expiration.

- **UT-9: Receipt Chain Traversal**
  - Chain traversal with valid `parent_receipt_id` → all ancestors/descendants returned.
  - Circular reference detection → circular references detected and logged as warnings.
  - Orphaned receipt handling → orphaned receipts (invalid `parent_receipt_id`) flagged.
  - Max depth limit → traversal stops at max_depth, returns partial chain with indicator.
  - Chain integrity → all receipts in chain are valid and accessible.

### 11.2 Component / Integration Tests

- **IT-1: End-to-End Ingest→Query**
  - Simulate Detection Engine emitting N receipts.
  - Query via search API; assert correct results.

- **IT-2: Validation + DLQ**
  - Send invalid receipts (bad fields, disallowed payload content).
  - Expect 4xx; verify DLQ / logs capture rejection reason.

- **IT-3: Multi-Tenant Isolation**
  - Tenant A/B receipts; Tenant A token must not see Tenant B data.
  - Product Ops role can see both; meta-receipts show cross-tenant access.

- **IT-4: Integrity Verification**
  - Corrupt a record in test env; run verify APIs; expect failure reports.

- **IT-5: Meta-Audit of Access**
  - Invoke search/aggregate APIs.
  - Confirm that corresponding meta-receipts are written, with correct requester, scope, and timestamp.

- **IT-6: Courier Batch End-to-End**
  - Simulate CCCS sending courier batch with N receipts.
  - Verify batch ingested, receipts stored, batch metadata persisted.
  - Query Merkle proof for batch → proof returned with correct structure.
  - Replay same batch_id → idempotent handling, no duplicates.

- **IT-7: Export End-to-End**
  - Request export with filters → export job created.
  - Poll export status → status transitions: `pending` → `processing` → `completed`.
  - Download export file → file contains correct receipts in specified format.
  - Verify export metadata → receipt count, checksum, format match actual file.
  - Verify meta-receipt → export operation generates meta-receipt per FR-9.

- **IT-8: Chain Traversal End-to-End**
  - Create multi-step flow: detection receipt → MMM decision → AI call receipts → override receipt.
  - Link receipts using `parent_receipt_id` and `related_receipt_ids`.
  - Query chain from root → all receipts in flow returned.
  - Query chain from middle receipt → ancestors and descendants returned.
  - Verify chain integrity → all links valid, no circular references.

### 11.3 Performance & Load Tests

- **PT-1: Sustained Ingestion**
  - Continuous receipts at expected load.
  - No unbounded backlog; SLOs met.

- **PT-2: Query Under Load**
  - Mixed search/aggregate workload over realistic data volume.
  - SLOs for query latency met and observed via metrics.

### 11.4 Security Tests

- **ST-1: AuthN/AuthZ**
  - Unauthenticated requests → 401.
  - Authenticated but unauthorised → 403.

- **ST-2: Malformed Payloads**
  - Oversized fields, unexpected types → validation rejection, no crash.

- **ST-3: Data Leakage**
  - Attempt to inject PII/secrets into payload → caught by validation; no storage.

### 11.5 Resilience Tests

- **RT-1: Store Node Failure**
  - Simulate storage failures during ingestion.
  - Confirm no duplicate receipts and no lost acknowledged receipts.

- **RT-2: Restart & Recovery**
  - Restart ERIS.
  - Confirm chain continuity and no loss.

---

## 12. Acceptance Criteria (Definition of Ready / Done)

ERIS can be marked **Definition of Done** when:

1. **All functional requirements FR-1 … FR-12** are implemented and covered by automated tests.
2. **Receipt schema alignment**:
   - ERIS accepts receipts in canonical schema format from `docs/architecture/receipt-schema-cross-reference.md`.
   - Field mappings validated against TypeScript interfaces and GSMD module schemas.
3. **Append-only and integrity guarantees** are enforced:
   - No update/delete paths.
   - Hash-chain and signature verification APIs running and tested.
   - Chain ID formula fixed and documented: `{tenant_id}:{plane}:{environment}:{emitter_service}`.
4. **Metadata-only payload constraint** is enforced through schema and runtime validation:
   - Integration with Contracts & Schema Registry for schema validation.
   - Integration with Data Governance for payload content validation.
5. **Multi-tenant isolation & meta-audit**:
   - Tenant-scoped queries correctly enforced via IAM integration.
   - IAM token verification and access decision evaluation integrated.
   - Meta-receipts for all access operations recorded and queryable.
6. **Integration APIs implemented**:
   - Data Governance integration (retention policy lookup, legal hold management).
   - Contracts & Schema Registry integration (schema lookup, validation service).
   - IAM integration (token verification, access decisions).
   - KMS integration (key resolution, signature verification).
7. **Courier batch ingestion**:
   - Courier batch ingestion API implemented and tested.
   - Merkle proof generation API implemented.
8. **Export API**:
   - Export API implemented with support for multiple formats (JSONL, CSV, Parquet).
   - Export respects Data Governance constraints (legal hold, retention, access control).
9. **Receipt linking**:
   - Receipt linking fields (`parent_receipt_id`, `related_receipt_ids`) supported.
   - Chain traversal APIs implemented and tested.
10. **SLOs defined and monitored**:
    - Documented SLOs exist for ingestion, queries, and availability.
    - Metrics and alerts wired to Observability & Reliability Plane.
11. **Resilience and BCDR hooks present**:
    - Storage partitioning by `dt`.
    - Export/archival flows usable from Ops runbooks.
12. **Security posture verified**:
    - AuthN/AuthZ tested with IAM integration.
    - No secrets/PII/code in receipts under enforced validation.
