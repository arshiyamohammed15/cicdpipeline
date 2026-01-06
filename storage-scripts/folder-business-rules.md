# ZeroUI — Folder Business Rules (Authoritative, Windows‑first)

# Folder Business Rules — ZeroUI 2.0 (DB/Storage)

## 0) Scope & Goal
**Goal:** The repository contains only **code & docs**.
**Forbidden in repo:** any **storage/data artifacts** (SQLite/DB files, WAL/SHM, logs, evidence packs/ZIPs, generated CSVs, etc.).

## 1) Non-Negotiable Rules
1. **Storage lives outside the repo**:
   - Edge SQLite DB → `D:\ZeroUI\edge.db`
   - Evidence packs → `E:\ZeroUI\Evidence\...`
   - Retention logs → `E:\zeroui_logs\...`
2. Repo holds only:
   - `/db/**` SQL (DDL/perf/checks/retention/signing glue)
   - `/scripts/**` PS1 automation (orchestration/runbooks)
   - `/docs/**` Markdown + CSV sign-offs
3. **Prohibited under repo** (tracked or untracked):
   `*.db`, `*.sqlite`, `*.sqlite3`, `*.wal`, `*.shm`, `*.log`, `*.zip`,
   any `edge.db`, any folder named `evidence`, `Evidence`, or `zeroui_logs`.
4. Scripts **must write** only to the external paths above (never inside the repo tree).

**Version:** 2.0 • **Date:** 2025-11-05 (UTC)
**Scope:** Authoritative placement rules for the **4 planes** (IDE Plane (Laptop), Tenant, Product, Shared), with a **laptop‑first** layout and a **configurable local root** (`ZU_ROOT`). This v2.0 simplifies the structure with lazy creation (parent folders only), consolidation (unified telemetry pattern), and flattening (reduced nesting depth from 5 to 3 levels).

> **Note:** "IDE Plane" and "IDE Plane (Laptop)" are equivalent terms. The "(Laptop)" suffix clarifies that this plane represents laptop-local storage. Legacy references to "IDE Plane" remain valid for compatibility.

> **Principles**: JSONL receipts are the **legal truth**; policy snapshots are **signed**; privacy by default (**no code/PII** in stores); **no secrets/private keys** on disk; cloud buckets are represented locally under `ZU_ROOT` for development.

---

## 0) Audience & How to use
- **Interns & Cursor**: Follow the **decision tree** and **per‑folder rules** exactly. When unclear, use **fallback** and open an **RFC** within 24h.
- **SRE/Platform**: Enforce via CI linters, scanners, and path validators.
- **Auditors**: Use the acceptance tests and path templates to verify compliance.

---

## Constitution Rule FN-001 — Folder Naming
- All new folders created in any ZeroUI repository **MUST** use kebab-case (`[a-z0-9-]+`).
- CI, scaffolds, and peer reviews must reject or rename any folder that violates this rule before merge.

## 1) Global invariants (apply everywhere)
1. **Name casing & charset**: All folder names are **kebab‑case**: `[a-z0-9-]` only.
2. **Placeholders**: `{tenant-id}`, `{org-id}`, `{region}`, `{env∈dev|stg|prod}`, `{repo-id}`, `{source}`, `{version}`, `{family}`, `{name}`, `{snapshot-id}`, `{yyyy}`, `{mm}`, `{dd}`, `{consumer-id}`.
3. **Partitions**: Time partitions use **UTC** → `dt={yyyy}-{mm}-{dd}` (zero‑padded). Optional hot sharding: `dt=.../shard={00..ff}/`.
4. **Privacy**: **No source code / PII** in any store. Receipts/evidence use **handles/IDs** only.
5. **Secrets & keys**: Only **public** keys in `trust/pubkeys/`. **Never** store private keys/credentials on disk—use secrets manager/HSM/KMS.
6. **Receipts**: Newline‑delimited JSON (**JSONL**), each line **signed** over canonical JSON. **Append‑only**; invalid lines go to **quarantine** (laptop) or **dlq** (cloud ingest).
7. **Policy snapshots**: JSON and **signed**. Laptops cache; authoritative publishing in **Product**.
8. **Dual storage**: JSONL is **authority**. DB mirrors (SQLite/Postgres) store the **raw JSON** verbatim + minimal indexes; DB is a **read/index** plane.
9. **Region & encryption**: Cloud storage is region‑pinned; KMS encryption at rest; mTLS in transit.

---

## 2) Windows‑first local root and planes mapping

### Environment-Scoped ZU_ROOT Pattern

ZU_ROOT should be environment-scoped to support multiple environments (development, integration, staging, production):

**Configuration-Driven Approach:**
- All environment setups are defined in `storage-scripts/config/environments.json`
- Each environment can have multiple deployment types (local, onprem, cloud)
- ZU_ROOT paths are validated against configuration rules

**Environment Examples:**

*development (local laptop):*
- **Windows PowerShell**: `$env:ZU_ROOT = "D:\\ZeroUI\\development"`

*integration/staging/production (on-prem):*
- **Windows**: `$env:ZU_ROOT = "\\\\onprem-server\\ZeroUI\\{environment}"`
- **Linux**: `$env:ZU_ROOT = "/mnt/storage/zero-ui/{environment}"`

*integration/staging/production (cloud):*
- **AWS S3**: `$env:ZU_ROOT = "s3://zero-ui-{environment}/{environment}"`
- **Azure**: `$env:ZU_ROOT = "az://zero-ui-{environment}/{environment}"`
- **GCS**: `$env:ZU_ROOT = "gs://zero-ui-{environment}/{environment}"`

**Configuration Management:**
Use `storage-scripts/tools/config_manager.ps1` to:
- List available environments: `-Action list`
- Validate configuration: `-Action validate -Env <env> -DeploymentType <type>`
- Generate ZU_ROOT: `-Action generate -Env <env> -DeploymentType <type> -ZuRoot <base>`
- Show environment config: `-Action show -Env <env>`

*(macOS/Linux may mirror with the same structure, but Windows is the reference environment.)*

### Plane Structure

All four planes live under `ZU_ROOT`:
- **IDE Plane (Laptop)** → `{ZU_ROOT}/ide/...`
- **Tenant** → `{ZU_ROOT}/tenant/...`
- **Product** → `{ZU_ROOT}/product/...`
- **Shared** → `{ZU_ROOT}/shared/...`

> Note: Cloud bucket mappings may vary per environment; local scaffold is simplified to `{ZU_ROOT}/{plane}/…`. See `storage-scripts/config/environments.json` for environment-specific configurations.

---

## 3) Decision tree (run in order)
**Q1. Secret or private key?** → **STOP** (secrets manager/HSM/KMS).
**Q2. Executable code/tests/fixtures?** → Keep in **source repo**.
**Q3. Signed fact by Agent/user feedback?** → **Receipt**:
- IDE: `ide/receipts/{repo-id}/{yyyy}/{mm}/`
- Tenant/Product mirrors: `evidence/data/{repo-id}/dt={date}/[shard=…/]`
**Q4. Derived from receipts (tables/aggregates/BI)?** → **Analytics**:
- Tenant: `reporting/marts/<table>/dt={date}/`
- Product: `reporting/tenants/{tenant-id}/{env}/aggregates/dt={date}/`
- Shared BI: `bi-lake/curated/zero-ui/{tenant-id}/{env}/dt={date}/`
**Q5. Observability telemetry (OTel)?** → **Telemetry**:
- All planes: `{plane}/telemetry/(metrics|traces|logs)/dt={date}/`
**Q6. Policy snapshot/template/public key?** → **Policy/Trust**.
**Q7. Adapter/webhook event or gateway diagnostic?** → **Adapters** (`adapters/webhooks/{source}/dt=…/`, `adapters/gateway-logs/dt=…/`).
**Q8. LLM prompt/tool/adapter/guardrail/cache?** → **LLM** trees (no secrets/weights/PII).
**Q9. Governance/consent/retention/legal‑hold/catalog/lineage?** → **Governance/Audit/Catalog**.
**Q10. Still ambiguous?** → Use **fallback** and open an **RFC** (§5).

---

## 4) Per‑plane, per‑folder rules (aligned with scaffold)

### 4.1 IDE Plane (Laptop) (`{ZU_ROOT}/ide/…`)
- `receipts/{repo-id}/{yyyy}/{mm}/` — **Append‑only signed JSONL**. No code/PII.
  Aux: `index/`, `quarantine/`, `checkpoints/` created on-demand under the same repo path.
- `policy/` — Signed snapshots + `current` pointer, cache, and `trust/pubkeys/` (public keys only).
- `config/` — Non‑secret consent snapshots and configuration.
- `queue/(pending|sent|failed)/` — Envelope refs only (created on-demand).
- `logs/`, `db/` (SQLite mirror, raw JSON).
- `llm/(prompts|tools|adapters|cache/token|cache/embedding|redaction|runs)/` — Sanitized; **no secrets/weights/PII** (created on-demand).
- `fingerprint/` — Non‑secret device fingerprint.
- `tmp/` — Temporary; also used by RFC stamping (`UNCLASSIFIED__<slug>`).
- `evaluation/(dry-runs|results|cache)/` — **Optional** evaluation harness storage (created on-demand).
  - **Allowed**: Evaluation harness inputs/outputs, fixtures, run results, test artifacts. **No code/PII**; use handles/IDs only. Format: JSONL or structured JSON.
  - **Never**: Source code, raw PII, secrets, unredacted evaluation data.
  - **Writers**: Evaluation harness services, testing services, policy evaluation services.
  - **Readers**: Evaluation harness services, reporting services, audit services.
**Lazy creation:** Scaffold creates only parent folders; subfolders (like `receipts/{repo}/index/`, `llm/prompts/`) are created on-demand when needed.

### 4.2 Tenant (`{ZU_ROOT}/tenant/…`)
- `evidence/data/` — Merged receipts, manifests, checksums (created on-demand with dt= partitions). **WORM semantics** (Write-Once-Read-Many).
- `evidence/dlq/` — Dead letter queue.
- `evidence/watermarks/{consumer-id}/` — Per-consumer watermarks (created on-demand).
- `ingest/(staging|dlq)/` and `ingest/staging/unclassified/` — RFC fallback.
- `telemetry/(metrics|traces|logs)/dt=…/` — Unified observability pattern (created on-demand).
- `adapters/(webhooks|gateway-logs)/dt=…/` — Created on-demand.
- `reporting/marts/dt=…/` — Created on-demand.
- `policy/(snapshots|trust/pubkeys)/` — Signed; public keys only.
- `context/(identity|sso|scim|compliance)/` — Tenant context stores (created on-demand).
  - **Allowed**: Exported/redacted context snapshots, indexes, metadata. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, private keys, unredacted user data.
  - **Writers**: Tenant context services, SSO/SCIM adapters, compliance hooks, data governance services.
  - **Readers**: Policy evaluation services, access control services, audit/compliance services.
  - **Note**: DB/vector/graph systems may exist for tenant context, but any file/object exports (snapshots, indexes, dumps) must land in `tenant/context/`. In-memory or ephemeral DB caches are exempt; persistent exports require this path.
- `meta/schema/` — **Deprecated** legacy alias; created only with compatibility enabled.

### 4.3 Product (`{ZU_ROOT}/product/…`)
- `policy/registry/(releases|templates|revocations)/` — Unified policy structure.
- `evidence/watermarks/{consumer-id}/` — Per-consumer watermarks (created on-demand).
- `reporting/tenants/aggregates/dt=…/` — Created on-demand.
- `adapters/gateway-logs/dt=…/` — Created on-demand.
- `telemetry/(metrics|traces|logs)/dt=…/` — Unified observability pattern (created on-demand).
- `policy/trust/pubkeys/` — Public keys (merged with policy structure).
- `features/(store|metadata)/dt=…/` — Feature store and metadata (created on-demand).
  - **Allowed**: Feature store artifacts, feature metadata, feature lineage. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, unredacted feature data.
  - **Writers**: Feature store services, ML pipeline services, data engineering services.
  - **Readers**: ML services, analytics services, reporting services.

### 4.4 Shared (`{ZU_ROOT}/shared/…`)
- `pki/` — All PKI files (trust-anchors, intermediate, CRL, key-rotation) in one folder (public only).
- `telemetry/(metrics|traces|logs)/dt=…/` — Unified observability pattern (created on-demand).
- `siem/(detections|events/dt=…/)` — Flattened SIEM structure.
- `bi-lake/curated/zero-ui/`.
- `governance/(controls|attestations|sbom|supply-chain)/` — Flattened governance structure.
  - **Note**: `governance/sbom/` and `governance/supply-chain/` complement `security/sbom/` and `security/supply-chain/`. Use governance/ for policy/attestation artifacts; use security/ for raw SBOM/provenance files.
  - **Allowed** (sbom|supply-chain): SBOM policy artifacts, supply chain attestations, governance metadata. **Signed artifacts only**.
  - **Never** (sbom|supply-chain): Unsigned SBOMs, unverified attestations, secrets, private keys.
- `llm/(guardrails|routing|tools|ollama|tinyllama)/` — Flattened governance structure (created on-demand).
- `provider-registry/` — Provider metadata, versions, allowlists (created on-demand).
  - **Allowed**: Provider metadata (LLM providers, model versions, capabilities), allowlists/blocklists, version manifests, provider configuration snapshots. JSONL or structured JSON format.
  - **Never**: Provider API keys, secrets, weights, model binaries, PII.
  - **Writers**: Provider registry services, configuration management services, deployment services.
  - **Readers**: LLM gateway services, routing services, policy evaluation services, deployment services.
- `registry/(artifacts|models|providers)/` — Registry for artifacts, models, and providers (created on-demand).
  - **Allowed**: Artifact metadata, model metadata, provider metadata, version manifests, registry indexes. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, model binaries, unredacted registry data.
  - **Writers**: Registry services, artifact management services, model registry services.
  - **Readers**: Deployment services, policy evaluation services, audit services.
- `notifications/(queues|events)/dt=…/` — Notification queues and events (created on-demand).
  - **Allowed**: Notification queue metadata, event metadata, delivery receipts. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, unredacted notification content.
  - **Writers**: Notification services, event bus services, alerting services.
  - **Readers**: Notification services, audit services, monitoring services.
- `eval/(harness|results|cache)/` — Shared evaluation harness storage (created on-demand).
  - **Allowed**: Evaluation harness inputs/outputs, fixtures, run results, test artifacts. **No code/PII**; use handles/IDs only. Format: JSONL or structured JSON.
  - **Never**: Source code, raw PII, secrets, unredacted evaluation data.
  - **Writers**: Evaluation harness services, testing services, policy evaluation services.
  - **Readers**: Evaluation harness services, reporting services, audit services.
  - **Access control**: Required; evaluation results may contain sensitive metadata.
- `security/sbom/` — SBOM (Software Bill of Materials) outputs, attestations, provenance (created on-demand).
  - **Allowed**: SBOM outputs (SPDX, CycloneDX), attestations, provenance metadata, signed artifacts. **Signed artifacts only**.
  - **Never**: Unsigned SBOMs, unverified attestations, secrets, private keys.
  - **Writers**: SBOM generation services, build services, supply chain verification services.
  - **Readers**: Security services, compliance services, audit services, deployment services.
  - **Retention**: Per compliance requirements; signed artifacts must be retained per policy.
- `security/supply-chain/` — SLSA/provenance/verification artifacts (created on-demand).
  - **Allowed**: SLSA provenance, supply chain verification artifacts, attestation evidence, signed verification results. **Signed artifacts only**.
  - **Never**: Unsigned provenance, unverified attestations, secrets, private keys.
  - **Writers**: Supply chain verification services, build services, deployment services.
  - **Readers**: Security services, compliance services, audit services, deployment services.
  - **Retention**: Per compliance requirements; signed artifacts must be retained per policy.

---

## 5) Fallbacks & RFC
- **IDE Plane (Laptop)**: `{ZU_ROOT}/ide/tmp/UNCLASSIFIED__{slug}`
- **Tenant/Product**: `.../ingest/staging/unclassified/{slug}`
Resolve within **24h** with an RFC; move to canonical; add manifests/checksums for evidence.

---

## 6) Security & integrity, Dual storage, CI, Acceptance tests
Unchanged from v1.0; refer to sections 9–12 of v1.0 with the following additions:
- Watermarks are **per consumer**; the scaffold supports `-Consumer` to create the leaf.
- Deprecated alias `meta/schema` is **off by default**; scaffold enables it only with `-CompatAliases`.

---

## 7) Path templates (cheat sheet, updated)
- **IDE Plane (Laptop) receipts**: `ide/receipts/{repo-id}/{yyyy}/{mm}/`
- **Telemetry (all planes)**: `{plane}/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`
- **Tenant Evidence**: `tenant/evidence/data/{repo-id}/dt={yyyy}-{mm}-{dd}/`
- **Tenant Adapters**: `tenant/adapters/(webhooks/{source}|gateway-logs)/dt={yyyy}-{mm}-{dd}/`
- **Tenant Reporting**: `tenant/reporting/marts/<table>/dt={yyyy}-{mm}-{dd}/`
- **Tenant Context**: `tenant/context/(identity|sso|scim|compliance)/`
- **Product Policy**: `product/policy/registry/(releases|templates|revocations)/`
- **Product Features**: `product/features/(store|metadata)/dt={yyyy}-{mm}-{dd}/`
- **Product Reporting**: `product/reporting/tenants/{tenant-id}/{env}/aggregates/dt={yyyy}-{mm}-{dd}/`
- **Shared Provider Registry**: `shared/provider-registry/`
- **Shared Registry**: `shared/registry/(artifacts|models|providers)/`
- **Shared Notifications**: `shared/notifications/(queues|events)/dt={yyyy}-{mm}-{dd}/`
- **Shared Governance SBOM/Supply Chain**: `shared/governance/(sbom|supply-chain)/`
- **Shared Evaluation Harness**: `shared/eval/(harness|results|cache)/`
- **Shared SBOM**: `shared/security/sbom/`
- **Shared Supply Chain**: `shared/security/supply-chain/`
- **IDE Evaluation** (optional): `ide/evaluation/(dry-runs|results|cache)/`
- **Watermarks**: `*/evidence/watermarks/{consumer-id}/`
- **Deprecated alias**: `tenant/.../meta/schema/` (opt‑in only)

**End of file (v2.0).**

---

## 8) Audit Ledger Clarification

**Audit ledger** may be under `shared/governance/` or `shared/siem/` depending on use case:
- **Governance**: Policy-driven audit artifacts, attestations, compliance records
- **SIEM**: Security event logs, detections, incident artifacts

**Canonical spec**: See `docs/architecture/four_plane_folder_structure_v1.md` for complete path reference.
