# ZeroUI LLM Strategy Directives (4 Planes) — Cursor Apply Guide

STRICT DIRECTIVES: no hallucination, no assumptions, no sycophancy, no fiction.  
Apply as **policy-driven routing** with **auditable receipts**.  
This file is a **source-of-truth directive** for implementing LLM routing, fallbacks, and governance across planes.

**Enforcement**: This directive is enforced by ADR-LLM-001 (per-plane LLM instances). Functional Modules must call Router contract only; no direct Ollama calls.

---

## 1) Plane-Specific Model Policy (MUST)

### 1.1 Tenant / ZeroUI / Shared Planes (on-prem workstation now; real clouds later)
**Major Tasks**
- Primary: `qwen2.5-coder:32b`
- Failover: `qwen2.5-coder:14b`

**Minor Tasks**
- Primary: `qwen2.5-coder:14b`
- Failover: `tinyllama:latest`

**Directive**
- "Major vs Minor" MUST be decided by deterministic policy rules (see Section 2).
- If the runtime host cannot load 32b (OOM / timeout / unavailable), automatic failover MUST occur and be recorded in receipts.

### 1.2 Laptop / IDE Plane
Your original plan:  
- Primary: `Llama 3`  
- Failover: `tinyllama:latest`

**Updated directive (REQUIRED improvement)**
IDE plane MUST use **two primaries** by task type to reduce quality drift:
- **Code tasks (primary):** `qwen2.5-coder:7b` (or `qwen2.5-coder:14b` if laptop hardware supports)
- **Text/general assistant tasks (primary):** `llama3.1:8b` (pin exact tag used)
- **Failover for both:** `tinyllama:latest`

**Reason**
- Code-specialist model for code tasks → better diffs/patches.
- General model for explanations/coaching → better natural language.
- Failover model is "degraded mode" only (see Section 3).

---

## 2) Deterministic Task Classification Policy (MUST)

**No human judgement. No "it feels major".**  
Major/minor MUST be computed from measurable signals:

### 2.1 Major Task rules (ANY true → Major)
- `changed_files_count >= MAJOR_FILES_THRESHOLD`
- `estimated_diff_loc >= MAJOR_LOC_THRESHOLD`
- `rag_context_bytes >= MAJOR_RAG_BYTES_THRESHOLD`
- `tool_calls_planned >= MAJOR_TOOLCALL_THRESHOLD`
- `high_stakes_flag == true` (release/rollback/policy/security/compliance)

### 2.2 Minor Task rules (ALL true → Minor)
- below all thresholds above
- `high_stakes_flag == false`

### 2.3 Policy-driven thresholds
Threshold values MUST live in policy/config (not hardcoded in code).  
Example policy keys:
- `router.major.files_threshold`
- `router.major.loc_threshold`
- `router.major.rag_bytes_threshold`
- `router.major.tool_calls_threshold`

---

## 3) Failover + Degraded Mode (MUST)

### 3.1 When failover happens
Failover can happen due to:
- model not installed
- model load failure / OOM
- request timeout
- response violates output contract/schema
- safety/guardrail refusal (if applicable)

### 3.2 Degraded mode rules
If routing selects `tinyllama:latest`, the system MUST:
- restrict to **non-critical outputs**:
  - brief summaries
  - basic "next steps"
  - "cannot complete" messages
- MUST NOT produce:
  - privileged actions
  - policy changes
  - code patches for high-stakes flows
- MUST emit a receipt that marks the run as degraded (Section 6).

---

## 4) Context Window Control (MUST)

Never rely on implicit defaults. Always set context explicitly per request.

### 4.1 Recommended defaults (policy-driven)
- Minor tasks: `num_ctx = 4096..8192`
- Major tasks: `num_ctx = 16384..32768`

### 4.2 Rule
- Increase `num_ctx` only when needed (measured).
- RAG must reduce prompt size (retrieve minimal evidence).

---

## 5) Determinism Controls (MUST)

### 5.1 Seed
Every LLM invocation MUST include a deterministic `seed` (policy-defined), so repeated runs are reproducible where possible.

### 5.2 Temperature
For any output used in governance or automated changes:
- temperature MUST be low and policy-defined (default: `0.0..0.2`)
- if temperature > 0, receipt MUST record it

### 5.3 Output schema enforcement
If the calling workflow expects JSON/tool schema output:
- validate output strictly
- on schema violation → retry once with constrained prompt
- then failover (and record)

---

## 6) Receipts Requirements for LLM Router (MUST)

Every LLM call MUST produce a receipt (append-only) with at least:

### 6.1 Required receipt fields
- `plane`: `ide | tenant | product | shared`
- `task_class`: `major | minor`
- `task_type`: `code | text | retrieval | planning | summarise` (policy-defined enum)
- `model.primary`: exact model tag string
- `model.used`: exact model tag string
- `model.failover_used`: boolean
- `degraded_mode`: boolean
- `router.policy_id`: e.g. `POL-LLM-ROUTER-001`
- `router.policy_snapshot_hash`
- `llm.params`: `{ num_ctx, temperature, seed }`
- `output.contract_id` (if JSON schema enforced)
- `result.status`: `ok | schema_fail | timeout | model_unavailable | error`
- `evidence.trace_id` / `receipt_id`

### 6.2 Storage rule
- IDE plane writes receipts to local append-only JSONL.
- Tenant/Product/Shared planes persist receipt index per your DB strategy.

---

## 7) Model Naming + Pinning Rules (MUST)

- Do NOT use ambiguous names like "Llama 3".
- Use pinned tags: `llama3.1:8b` (or exact alternative), `qwen2.5-coder:14b`, etc.
- If quantization variants are used, pin them explicitly in documentation/config.

---

## 8) Implementation Guidance (for Cursor / engineers)

### 8.1 Add a Model Router component (single responsibility)
Implement `ModelRouter` that takes:
- plane
- task_type
- measurable signals (files/loc/context bytes/tool calls/high-stakes)
- policy snapshot

Returns:
- model.primary
- model.failover_chain[]
- params (num_ctx, temperature, seed)
- contract enforcement rules

### 8.2 Router must be pure + testable
- No network calls inside router.
- Router outputs must be deterministic given inputs.

### 8.3 No hardcoding
- Models, thresholds, params, and routing rules must be loaded from policy/config.

---

## 9) Minimum Tests (MUST)

### 9.1 Unit tests
- Major vs minor classification boundaries
- IDE plane code vs text routing
- Failover chain ordering
- Degraded mode toggling
- Receipt fields completeness

### 9.2 Integration tests (local)
- Model installed/uninstalled simulation
- Timeout simulation → failover + receipt
- Schema violation → retry → failover + receipt

### 9.3 CI check (optional but recommended)
- Lint/validate router policy JSON schema
- Snapshot hash present in receipts

---

## 10) Readiness Statement (for Functional Modules)

Functional Modules implementation can proceed ONLY if:
- Router policy exists and is referenced by a policy snapshot
- Receipts for model selection are emitted and indexed
- IDE plane uses split routing (code vs text) as above
- Degraded mode is enforced and measurable

---

## 11) Out of Scope (explicit)
- Choosing exact threshold values (must come from your policy team / pilot measurement)
- Introducing new vector DB vendors (stay on Postgres/pgvector for MVP)
- Any module-specific business logic for FM-1..FM-15

---

