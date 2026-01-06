# ZeroUI Four Plane Folder Structure v1.0 — Canonical Specification

**ID**: ARCH.STORAGE.4PLANE.SPEC.V1  
**Date**: 2026-01-03  
**Status**: Canonical Specification  
**Source of Truth**: This document defines the complete folder structure for ZeroUI 4-Plane Storage Architecture

---

## Overview

This specification defines the complete folder structure for the ZeroUI 4-Plane Storage Architecture. All paths are relative to `ZU_ROOT` and follow the naming conventions defined in `storage-scripts/folder-business-rules.md`.

**Key Principles:**
- Kebab-case naming: `[a-z0-9-]+` only
- Time partitions: `dt={yyyy}-{mm}-{dd}` (UTC)
- Lazy creation: Parent folders created by scaffold; subfolders created on-demand
- No secrets/PII: Only handles/IDs in storage
- JSONL authority: Receipts are append-only signed JSONL

---

## IDE Plane (`{ZU_ROOT}/ide/`)

### Core Paths
- `receipts/{repo-id}/{yyyy}/{mm}/` — Append-only signed JSONL receipts
- `policy/` — Signed snapshots + current pointer, cache
- `policy/trust/pubkeys/` — Public keys only
- `config/` — Non-secret consent snapshots and configuration
- `queue/` — Envelope refs only (pending/, sent/, failed/ created on-demand)
- `logs/` — Log files
- `db/` — SQLite mirror, raw JSON
- `llm/(prompts|tools|adapters|cache/token|cache/embedding|redaction|runs)/` — LLM artifacts (created on-demand)
- `fingerprint/` — Non-secret device fingerprint
- `tmp/` — Temporary; RFC stamping (`UNCLASSIFIED__{slug}`)

### Optional Paths
- `evaluation/(dry-runs|results|cache)/` — Evaluation harness storage (optional, created on-demand)
  - **Allowed**: Evaluation harness inputs/outputs, fixtures, run results, test artifacts. **No code/PII**; use handles/IDs only.
  - **Never**: Source code, raw PII, secrets, unredacted evaluation data.

---

## Tenant Plane (`{ZU_ROOT}/tenant/`)

### Core Paths
- `evidence/data/` — Merged receipts, manifests, checksums (dt= partitions created on-demand)
- `evidence/dlq/` — Dead letter queue
- `evidence/watermarks/{consumer-id}/` — Per-consumer watermarks (created on-demand)
- `ingest/(staging|dlq)/` — RFC fallback (staging/unclassified/ created on-demand)
- `telemetry/(metrics|traces|logs)/dt=.../` — Unified observability pattern (created on-demand)
- `adapters/(webhooks/{source}|gateway-logs)/dt=.../` — Adapters (created on-demand)
- `reporting/marts/<table>/dt=.../` — Analytics marts (created on-demand)
- `policy/snapshots/` — Signed snapshots
- `policy/trust/pubkeys/` — Public keys only

### Context Stores
- `context/(identity|sso|scim|compliance)/` — Tenant context stores (created on-demand)
  - **Allowed**: Exported/redacted context snapshots, indexes, metadata. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, private keys, unredacted user data.
  - **Writers**: Tenant context services, SSO/SCIM adapters, compliance hooks, data governance services.
  - **Readers**: Policy evaluation services, access control services, audit/compliance services.

### Deprecated (Opt-in)
- `meta/schema/` — Deprecated legacy alias (created only with -CompatAliases)

---

## Product Plane (`{ZU_ROOT}/product/`)

### Core Paths
- `policy/registry/(releases|templates|revocations)/` — Unified policy structure
- `evidence/watermarks/{consumer-id}/` — Per-consumer watermarks (created on-demand)
- `reporting/tenants/{tenant-id}/{env}/aggregates/dt=.../` — Tenant aggregates (created on-demand)
- `adapters/gateway-logs/dt=.../` — Gateway diagnostics (created on-demand)
- `telemetry/(metrics|traces|logs)/dt=.../` — Unified observability pattern (created on-demand)
- `policy/trust/pubkeys/` — Public keys (merged with policy structure)

### Feature Stores
- `features/(store|metadata)/dt=.../` — Feature store and metadata (created on-demand)
  - **Allowed**: Feature store artifacts, feature metadata, feature lineage. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, unredacted feature data.
  - **Writers**: Feature store services, ML pipeline services, data engineering services.
  - **Readers**: ML services, analytics services, reporting services.

---

## Shared Plane (`{ZU_ROOT}/shared/`)

### Core Paths
- `pki/` — All PKI files (trust-anchors, intermediate, CRL, key-rotation) in one folder (public only)
- `telemetry/(metrics|traces|logs)/dt=.../` — Unified observability pattern (created on-demand)
- `siem/(detections|events/dt=.../)` — Flattened SIEM structure (events/dt=.../ created on-demand)
- `bi-lake/curated/zero-ui/` — BI lake curated data
- `governance/(controls|attestations)/` — Flattened governance structure
- `llm/(guardrails|routing|tools|ollama|tinyllama)/` — Flattened governance structure (created on-demand)
- `provider-registry/` — Provider metadata, versions, allowlists (created on-demand)
  - **Allowed**: Provider metadata (LLM providers, model versions, capabilities), allowlists/blocklists, version manifests, provider configuration snapshots. JSONL or structured JSON format.
  - **Never**: Provider API keys, secrets, weights, model binaries, PII.

### Registry Paths
- `registry/(artifacts|models|providers)/` — Registry for artifacts, models, and providers (created on-demand)
  - **Allowed**: Artifact metadata, model metadata, provider metadata, version manifests, registry indexes. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, model binaries, unredacted registry data.
  - **Writers**: Registry services, artifact management services, model registry services.
  - **Readers**: Deployment services, policy evaluation services, audit services.

### Governance Extensions
- `governance/(sbom|supply-chain)/` — SBOM and supply chain governance (created on-demand)
  - **Note**: These paths complement `shared/security/sbom/` and `shared/security/supply-chain/`. Use governance/ for policy/attestation artifacts; use security/ for raw SBOM/provenance files.
  - **Allowed**: SBOM policy artifacts, supply chain attestations, governance metadata. **Signed artifacts only**.
  - **Never**: Unsigned SBOMs, unverified attestations, secrets, private keys.

### Notifications
- `notifications/(queues|events)/dt=.../` — Notification queues and events (created on-demand)
  - **Allowed**: Notification queue metadata, event metadata, delivery receipts. **No code/PII**; use handles/IDs only. JSONL or structured JSON format.
  - **Never**: Source code, raw PII, secrets, unredacted notification content.
  - **Writers**: Notification services, event bus services, alerting services.
  - **Readers**: Notification services, audit services, monitoring services.

### Security
- `security/sbom/` — SBOM (Software Bill of Materials) outputs, attestations, provenance (created on-demand)
  - **Allowed**: SBOM outputs (SPDX, CycloneDX), attestations, provenance metadata, signed artifacts. **Signed artifacts only**.
  - **Never**: Unsigned SBOMs, unverified attestations, secrets, private keys.

- `security/supply-chain/` — SLSA/provenance/verification artifacts (created on-demand)
  - **Allowed**: SLSA provenance, supply chain verification artifacts, attestation evidence, signed verification results. **Signed artifacts only**.
  - **Never**: Unsigned provenance, unverified attestations, secrets, private keys.

### Evaluation
- `eval/(harness|results|cache)/` — Shared evaluation harness storage (created on-demand)
  - **Allowed**: Evaluation harness inputs/outputs, fixtures, run results, test artifacts. **No code/PII**; use handles/IDs only. Format: JSONL or structured JSON.
  - **Never**: Source code, raw PII, secrets, unredacted evaluation data.

---

## Path Templates (Quick Reference)

### IDE Plane
- Receipts: `ide/receipts/{repo-id}/{yyyy}/{mm}/`
- Evaluation: `ide/evaluation/(dry-runs|results|cache)/` (optional)

### Tenant Plane
- Evidence: `tenant/evidence/data/{repo-id}/dt={yyyy}-{mm}-{dd}/`
- Context: `tenant/context/(identity|sso|scim|compliance)/`
- Telemetry: `tenant/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`
- Adapters: `tenant/adapters/(webhooks/{source}|gateway-logs)/dt={yyyy}-{mm}-{dd}/`
- Reporting: `tenant/reporting/marts/<table>/dt={yyyy}-{mm}-{dd}/`

### Product Plane
- Policy: `product/policy/registry/(releases|templates|revocations)/`
- Features: `product/features/(store|metadata)/dt={yyyy}-{mm}-{dd}/`
- Reporting: `product/reporting/tenants/{tenant-id}/{env}/aggregates/dt={yyyy}-{mm}-{dd}/`
- Telemetry: `product/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`

### Shared Plane
- Registry: `shared/registry/(artifacts|models|providers)/`
- Notifications: `shared/notifications/(queues|events)/dt={yyyy}-{mm}-{dd}/`
- Governance: `shared/governance/(controls|attestations|sbom|supply-chain)/`
- Security: `shared/security/(sbom|supply-chain)/`
- Telemetry: `shared/telemetry/(metrics|traces|logs)/dt={yyyy}-{mm}-{dd}/`
- SIEM: `shared/siem/(detections|events/dt={yyyy}-{mm}-{dd}/)`
- Evaluation: `shared/eval/(harness|results|cache)/`

---

## Notes

### Audit Ledger
Audit ledger may be under `shared/governance/` or `shared/siem/` depending on use case:
- **Governance**: Policy-driven audit artifacts, attestations, compliance records
- **SIEM**: Security event logs, detections, incident artifacts

### SBOM/Supply Chain Dual Paths
- `shared/security/sbom/` and `shared/security/supply-chain/`: Raw SBOM files, provenance artifacts, signed verification results
- `shared/governance/sbom/` and `shared/governance/supply-chain/`: Policy artifacts, governance metadata, attestation records

### Lazy Creation
All paths marked "created on-demand" are not created by the scaffold script. Only parent folders are created. Services create subfolders when needed.

---

## Version History

- **v1.0** (2026-01-03): Initial canonical specification with all paths from folder-business-rules.md v2.0 plus new paths:
  - `shared/registry/(artifacts|models|providers)/`
  - `tenant/context/(identity|sso|scim|compliance)/` (sub-paths)
  - `shared/governance/(sbom|supply-chain)/`
  - `shared/notifications/(queues|events)/dt=.../`
  - `product/features/(store|metadata)/dt=.../`
  - `ide/evaluation/(dry-runs|results|cache)/` (optional)

---

**End of Specification**

