# ZeroUI — Folder Business Rules (Authoritative, Windows‑first)

**Version:** 1.1 • **Date:** 2025-10-18 (UTC)  
**Scope:** Authoritative placement rules for the **4 planes** (Laptop, Tenant, Product, Shared), with a **laptop‑first** layout and a **configurable local root** (`ZU_ROOT`). This v1.1 aligns the spec with the Windows‑first scaffold and closes gaps (per‑consumer watermarks, dt= partitions for Observability/Adapters/Reporting, laptop month partition, legacy alias gating).

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
Set a single env var:
- **Windows PowerShell**: `$env:ZU_ROOT = "D:\\ZeroUI"`  
*(macOS/Linux may mirror with the same structure, but Windows is the reference environment.)*

All four planes live under `ZU_ROOT`:
- **IDE (laptop plane)** → `{ZU_ROOT}/ide/...`
- **Tenant** → `{ZU_ROOT}/tenant/...`
- **Product** → `{ZU_ROOT}/product/...`
- **Shared** → `{ZU_ROOT}/shared/...`

> Note: Cloud bucket mappings may vary per environment; local scaffold is simplified to `{ZU_ROOT}/{plane}/…`.

---

## 3) Decision tree (run in order)
**Q1. Secret or private key?** → **STOP** (secrets manager/HSM/KMS).  
**Q2. Executable code/tests/fixtures?** → Keep in **source repo**.  
**Q3. Signed fact by Agent/user feedback?** → **Receipt**:  
- IDE: `ide/agent/receipts/{repo-id}/{yyyy}/{mm}/`  
- Tenant/Product mirrors: `evidence/(decision|feedback)/{repo-id}/dt={date}/[shard=…/]`
**Q4. Derived from receipts (tables/aggregates/BI)?** → **Analytics**:  
- Tenant: `reporting/marts/<table>/dt={date}/`  
- Product: `reporting/tenants/{tenant-id}/{env}/aggregates/dt={date}/`  
- Shared BI: `bi-lake/curated/zero-ui/{tenant-id}/{env}/dt={date}/`
**Q5. Observability telemetry (OTel)?** → **Observability**:  
- Tenant: `observability/(metrics|traces|logs)/dt={date}/`  
- Product: `service-metrics/(metrics|traces|logs)/dt={date}/`  
- Shared: `observability/otel/(metrics|traces|logs)/dt={date}/`
**Q6. Policy snapshot/template/public key?** → **Policy/Trust**.  
**Q7. Adapter/webhook event or gateway diagnostic?** → **Adapters** (`adapters/webhooks/{source}/dt=…/`, `adapters/gateway-logs/dt=…/`).  
**Q8. LLM prompt/tool/adapter/guardrail/cache?** → **LLM** trees (no secrets/weights/PII).  
**Q9. Governance/consent/retention/legal‑hold/catalog/lineage?** → **Governance/Audit/Catalog**.  
**Q10. Still ambiguous?** → Use **fallback** and open an **RFC** (§8).

---

## 4) Per‑plane, per‑folder rules (aligned with scaffold)

### 4.1 IDE (`{ZU_ROOT}/ide/…`)
- `agent/receipts/{repo-id}/{yyyy}/{mm}/` — **Append‑only signed JSONL**. No code/PII.  
  Aux: `index/`, `quarantine/`, `checkpoints/` under the same repo path.  
- `agent/policy/cache/` — Signed snapshots + `current` pointer.  
- `agent/trust/pubkeys/` — **Public** keys only.  
- `agent/config/consent/` — Non‑secret consent snapshots.  
- `agent/queue/evidence/(pending|sent|failed)/` — Envelope refs only.  
- `agent/logs/metrics/`, `agent/db/` (SQLite mirror, raw JSON).  
- `agent/llm/(prompts|tools|adapters|cache/token|cache/embedding|redaction|runs)/` — Sanitized; **no secrets/weights/PII**.  
- `agent/actor/fingerprint/` — Non‑secret device fingerprint.  
- `agent/tmp/` — Temporary; also used by RFC stamping (`UNCLASSIFIED__<slug>`).  
**Removed:** prior `extension/*` paths (presentation caches) are **not scaffolded** to avoid drift; teams may create them locally if needed.

### 4.2 Tenant (`{ZU_ROOT}/tenant/…`)
- `evidence/(receipts|manifests|checksums|dlq|watermarks)/`  
- `ingest/(staging|dlq)/` and `ingest/staging/unclassified/` — RFC fallback.  
- `observability/(metrics|traces|logs)/dt=…/`.  
- `adapters/(webhooks|gateway-logs)/dt=…/`.  
- `reporting/marts/dt=…/`.  
- `policy/(snapshots|trust/pubkeys)/` — Signed; public keys only.  
- `meta/schema/` — **Deprecated** legacy alias; created only with compatibility enabled.

### 4.3 Product (`{ZU_ROOT}/product/…`)
- `policy-registry/(releases|templates|revocations)/`.  
- `evidence/watermarks/`.  
- `reporting/tenants/aggregates/dt=…/`.  
- `adapters/gateway-logs/dt=…/`.  
- `service-metrics/(metrics|traces|logs)/dt=…/`.  
- `trust/pubkeys/`.

### 4.4 Shared (`{ZU_ROOT}/shared/…`)
- `pki/(trust-anchors|intermediate|crl|key-rotation)/` (public only).  
- `observability/otel/(metrics|traces|logs)/dt=…/`.  
- `siem/(detections/zero-ui|events/dt=…/)`.  
- `bi-lake/curated/zero-ui/`.  
- `governance/(controls/zero-ui|attestations)/`, `llm/(guardrails|routing|tools)/`.

---

## 5) Fallbacks & RFC
- **IDE**: `{ZU_ROOT}/ide/agent/tmp/UNCLASSIFIED__{slug}`  
- **Tenant/Product**: `.../ingest/staging/unclassified/{slug}`  
Resolve within **24h** with an RFC; move to canonical; add manifests/checksums for evidence.

---

## 6) Security & integrity, Dual storage, CI, Acceptance tests
Unchanged from v1.0; refer to sections 9–12 of v1.0 with the following additions:  
- Watermarks are **per consumer**; the scaffold supports `-Consumer` to create the leaf.  
- Deprecated alias `meta/schema` is **off by default**; scaffold enables it only with `-CompatAliases`.

---

## 7) Path templates (cheat sheet, updated)
- **IDE receipts**: `ide/agent/receipts/{repo-id}/{yyyy}/{mm}/`  
- **Tenant Observability**: `observability/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`  
- **Tenant Adapters**: `adapters/(webhooks/{source}|gateway-logs)/dt={yyyy}-{mm}-{dd}/`  
- **Tenant Reporting**: `reporting/marts/<table>/dt={yyyy}-{mm}-{dd}/`  
- **Product Service Metrics**: `service-metrics/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`  
- **Watermarks**: `*/watermarks/{consumer-id}/`  
- **Deprecated alias**: `tenant/.../meta/schema/` (opt‑in only)

**End of file (v1.1).**
