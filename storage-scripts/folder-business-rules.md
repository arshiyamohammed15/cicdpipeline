# ZeroUI — Folder Business Rules (Authoritative, Windows‑first)

**Version:** 2.0 • **Date:** 2025-11-05 (UTC)  
**Scope:** Authoritative placement rules for the **4 planes** (IDE Plane, Tenant, Product, Shared), with a **laptop‑first** layout and a **configurable local root** (`ZU_ROOT`). This v2.0 simplifies the structure with lazy creation (parent folders only), consolidation (unified telemetry pattern), and flattening (reduced nesting depth from 5 to 3 levels).

> **Principles**: JSONL receipts are the **legal truth**; policy snapshots are **signed**; privacy by default (**no code/PII** in stores); **no secrets/private keys** on disk; cloud buckets are represented locally under `ZU_ROOT` for development.

---

## 0) Audience & How to use
- **Interns & Cursor**: Follow the **decision tree** and **per‑folder rules** exactly. When unclear, use **fallback** and open an **RFC** within 24h.
- **SRE/Platform**: Enforce via CI linters, scanners, and path validators.
- **Auditors**: Use the acceptance tests and path templates to verify compliance.

---

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
- **IDE Plane** → `{ZU_ROOT}/ide/...`
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

### 4.1 IDE (`{ZU_ROOT}/ide/…`)
- `receipts/{repo-id}/{yyyy}/{mm}/` — **Append‑only signed JSONL**. No code/PII.  
  Aux: `index/`, `quarantine/`, `checkpoints/` created on-demand under the same repo path.  
- `policy/` — Signed snapshots + `current` pointer, cache, and `trust/pubkeys/` (public keys only).  
- `config/` — Non‑secret consent snapshots and configuration.  
- `queue/(pending|sent|failed)/` — Envelope refs only (created on-demand).  
- `logs/`, `db/` (SQLite mirror, raw JSON).  
- `llm/(prompts|tools|adapters|cache/token|cache/embedding|redaction|runs)/` — Sanitized; **no secrets/weights/PII** (created on-demand).  
- `fingerprint/` — Non‑secret device fingerprint.  
- `tmp/` — Temporary; also used by RFC stamping (`UNCLASSIFIED__<slug>`).  
**Lazy creation:** Scaffold creates only parent folders; subfolders (like `receipts/{repo}/index/`, `llm/prompts/`) are created on-demand when needed.

### 4.2 Tenant (`{ZU_ROOT}/tenant/…`)
- `evidence/data/` — Merged receipts, manifests, checksums (created on-demand with dt= partitions).  
- `evidence/dlq/` — Dead letter queue.  
- `evidence/watermarks/{consumer-id}/` — Per-consumer watermarks (created on-demand).  
- `ingest/(staging|dlq)/` and `ingest/staging/unclassified/` — RFC fallback.  
- `telemetry/(metrics|traces|logs)/dt=…/` — Unified observability pattern (created on-demand).  
- `adapters/(webhooks|gateway-logs)/dt=…/` — Created on-demand.  
- `reporting/marts/dt=…/` — Created on-demand.  
- `policy/(snapshots|trust/pubkeys)/` — Signed; public keys only.  
- `meta/schema/` — **Deprecated** legacy alias; created only with compatibility enabled.

### 4.3 Product (`{ZU_ROOT}/product/…`)
- `policy/registry/(releases|templates|revocations)/` — Unified policy structure.  
- `evidence/watermarks/{consumer-id}/` — Per-consumer watermarks (created on-demand).  
- `reporting/tenants/aggregates/dt=…/` — Created on-demand.  
- `adapters/gateway-logs/dt=…/` — Created on-demand.  
- `telemetry/(metrics|traces|logs)/dt=…/` — Unified observability pattern (created on-demand).  
- `policy/trust/pubkeys/` — Public keys (merged with policy structure).

### 4.4 Shared (`{ZU_ROOT}/shared/…`)
- `pki/` — All PKI files (trust-anchors, intermediate, CRL, key-rotation) in one folder (public only).  
- `telemetry/(metrics|traces|logs)/dt=…/` — Unified observability pattern (created on-demand).  
- `siem/(detections|events/dt=…/)` — Flattened SIEM structure.  
- `bi-lake/curated/zero-ui/`.  
- `governance/(controls|attestations)/`, `llm/(guardrails|routing|tools)/` — Flattened governance structure.

---

## 5) Fallbacks & RFC
- **IDE**: `{ZU_ROOT}/ide/tmp/UNCLASSIFIED__{slug}`  
- **Tenant/Product**: `.../ingest/staging/unclassified/{slug}`  
Resolve within **24h** with an RFC; move to canonical; add manifests/checksums for evidence.

---

## 6) Security & integrity, Dual storage, CI, Acceptance tests
Unchanged from v1.0; refer to sections 9–12 of v1.0 with the following additions:  
- Watermarks are **per consumer**; the scaffold supports `-Consumer` to create the leaf.  
- Deprecated alias `meta/schema` is **off by default**; scaffold enables it only with `-CompatAliases`.

---

## 7) Path templates (cheat sheet, updated)
- **IDE receipts**: `ide/receipts/{repo-id}/{yyyy}/{mm}/`  
- **Telemetry (all planes)**: `{plane}/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`  
- **Tenant Evidence**: `tenant/evidence/data/{repo-id}/dt={yyyy}-{mm}-{dd}/`  
- **Tenant Adapters**: `tenant/adapters/(webhooks/{source}|gateway-logs)/dt={yyyy}-{mm}-{dd}/`  
- **Tenant Reporting**: `tenant/reporting/marts/<table>/dt={yyyy}-{mm}-{dd}/`  
- **Product Policy**: `product/policy/registry/(releases|templates|revocations)/`  
- **Product Reporting**: `product/reporting/tenants/{tenant-id}/{env}/aggregates/dt={yyyy}-{mm}-{dd}/`  
- **Watermarks**: `*/evidence/watermarks/{consumer-id}/`  
- **Deprecated alias**: `tenant/.../meta/schema/` (opt‑in only)

**End of file (v2.0).**
