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
- IDE Plane: Postgres only (`ZEROUI_IDE_DB_URL`)
- Tenant Plane: Postgres only (`ZEROUI_TENANT_DB_URL`)
- Product Plane: Postgres only (`ZEROUI_PRODUCT_DB_URL`)
- Shared Plane: Postgres only (`ZEROUI_SHARED_DB_URL`)

Rules:
1) Do not create tables in the wrong plane database.
2) Do not mix tenant/product/shared tables in a single database.
3) Use only the canonical env vars above.
4) If a prompt asks to store data and the plane is unclear: STOP and ask (max 3 questions). Do not guess.

## Mandatory Directive: LLM Strategy (4 Planes)

All future implementation prompts and code changes MUST follow:
- docs/architecture/llm_strategy_directives.md

Rules:
1) Treat this file as a source-of-truth directive for LLM routing, fallbacks, determinism, and receipts.
2) If any prompt instruction conflicts with the directive, STOP and ask max 3 questions. Do not guess.
3) Do not introduce model naming ambiguity ("Llama 3" is not allowed in configs; pin exact tags).
4) Enforce policy-driven routing (no hardcoded thresholds/messages) and auditable receipts for model selection.

## Mandatory Directive: Per-Plane LLM Instances

- ADR-LLM-001-per-plane-llm-instances.md is ACCEPTED and MUST be followed.
- Each plane runs its own LLM runtime + model set.
- Functional Modules must call plane-local LLM Router contract; direct Ollama calls are forbidden.
- CI enforces 'no direct Ollama in FM code' via `scripts/ci/forbid_direct_ollama_in_fm.ps1`.
- On conflict: STOP and ask max 3 questions.

## Mandatory Directive: LLM Topology Configuration

- LLM endpoints MUST be resolved via `LLM_TOPOLOGY_*` environment variables; no hardcoded Ollama URLs in code.
- Topology mode is environment-driven: `LOCAL_SINGLE_PLANE` (local dev) or `PER_PLANE` (on-prem/staging).
- Local mode may forward tenant/product/shared requests to IDE LLM endpoint for resource efficiency.
- Configuration via `scripts/setup/configure_llm_topology.ps1`; validation via `-Mode verify`.
- On conflict: STOP and ask max 3 questions.

**Enforcement Rules:**
- LLM endpoints MUST be resolved via `LLM_TOPOLOGY_*` env vars; no hardcoded Ollama URLs.
- Local mode may forward tenant/product/shared to IDE LLM endpoint.
- On conflict: STOP and ask max 3 questions.