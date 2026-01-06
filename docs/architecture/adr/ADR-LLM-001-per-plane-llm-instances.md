# ADR-LLM-001 — Per-Plane LLM Runtime Instances and Model Sets

- **Date:** 2026-01-03
- **Status:** Accepted
- **Deciders:** ZeroUI 2.0 Architecture Working Group
- **Technical Area:** LLM routing, plane isolation, service contracts

## Context

ZeroUI 2.0 uses a 4-plane architecture (IDE, Tenant, Product, Shared) with strict data boundary isolation. LLM services are required across all planes for routing, fallbacks, and governance. The architecture must support:
- Plane-specific model sets and policies
- Resilience when planes are isolated or down
- Auditable receipts per plane
- Policy-driven routing without hardcoded dependencies

## Decision

**Each plane runs its own LLM runtime (Ollama) + model set, and all plane services must call a plane-local LLM Router contract (not Ollama directly).**

### Plane-Specific Instances

- **IDE Plane**: Local Ollama instance + local models
- **Tenant Plane**: Tenant-local Ollama instance + models (on-prem now, tenant cloud later)
- **Product/ZeroUI Plane**: Product-local Ollama instance + models (on-prem now, ZeroUI cloud later)
- **Shared Plane**: Shared-local Ollama instance + models (on-prem now, shared cloud later)

### Contract Rule

- All modules/services must call the plane-local LLM Router contract.
- No direct calls to Ollama from Functional Modules.
- Router contract API must be identical across planes.

## Reasons

- **Data boundary isolation**: Each plane maintains its own model set and routing policies without cross-plane dependencies.
- **Resilience**: If one plane's LLM runtime is down, other planes continue operating independently.
- **Plane-specific policy routing + receipts**: Each plane can enforce its own routing rules and generate receipts with plane context.

## Consequences

### Positive

- Clear isolation boundaries between planes.
- Independent scaling and availability per plane.
- Plane-specific model selection policies.
- Auditable receipts per plane with `model.used` and `degraded_mode` fields.

### Negative / Risks

- Router API contract must be identical across planes (enforced via contract tests).
- Model availability differs by plane but contract remains stable.
- Per-plane receipts MUST record `model.used` + `degraded_mode` for governance.

### Risk Mitigations

- Define Router contract as OpenAPI/JSON Schema and validate across planes.
- Implement contract tests that verify API compatibility.
- Enforce receipt schema validation in CI.

## Out of Scope

- Choosing exact model quantization / GPU sizing (per-plane operational decision).
- Model registry implementation details (covered by other ADRs).
- Specific routing algorithms (covered by `llm_strategy_directives.md`).

## Validation

The decision is considered implemented when:

- Each plane has its own Ollama instance configuration.
- All Functional Modules call Router contract only (no direct Ollama calls).
- Router contract API is identical across planes (verified by contract tests).
- Receipts include `model.used` and `degraded_mode` fields per plane.

## References

- `docs/architecture/llm_strategy_directives.md` — Model selection policies and routing rules
- `docs/architecture/four_plane_folder_structure_v1.md` — Plane structure and storage paths

---

*This ADR enforces per-plane LLM isolation and Router contract usage. Revisit if plane boundaries or LLM runtime architecture materially change.*

