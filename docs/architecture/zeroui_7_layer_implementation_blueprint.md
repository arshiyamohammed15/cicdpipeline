# ZeroUI 7-Layer Agentic Architecture  
**Implementation Blueprint with Cross-Cutting Planes**

> This document is the implementation-ready blueprint for ZeroUI’s 7-Layer Agentic Architecture with three cross-cutting planes.  
> It is normative for the current design: it describes what we intend to build and how the pieces fit together.

---

## 1. Purpose & Scope

ZeroUI is a laptop-first, Zero-UI product delivered through:

- A VS Code extension (status pill, diagnostics, quick-fix, decision card)
- An Edge Agent on the developer’s laptop
- Backend services in the tenant’s cloud and the product’s cloud

The system’s goals are to:

- Detect and prevent SDLC risks early (release failures, merge conflicts, legacy safety issues, etc.).
- Use AI agents in a governed, cost-controlled, auditable way.
- Treat humans and AI agents as first-class actors with parity governance.
- Keep core decisions deterministic or tightly constrained, with LLMs acting as assistants, not uncontrolled authorities.

This blueprint covers:

- The **3 cross-cutting planes**.
- The **7 functional layers**.
- The **core contracts (ZAP – ZeroUI Agent Protocol)**.
- Example end-to-end flows and phased implementation guidance.

---

## 2. Core Design Principles

1. **Laptop-first, Privacy-first**
   - The Edge Agent runs locally and prefers local processing.
   - Only redacted, minimal context leaves the device.
   - Secrets and full repository contents never leave the laptop by default.

2. **Zero-UI for Developers**
   - Primary surfaces are VS Code and CI status checks.
   - No separate web app for day-to-day developer interaction.

3. **Policy-as-Code and GSMD**
   - Behaviour is driven by Gold Standard Model Definitions (GSMD) and policies stored in version control.
   - Policies are compiled into signed bundles and distributed to runtimes (Edge, CI, backend).

4. **Receipts-First Evidence**
   - Every privileged action produces an append-only JSONL receipt with actor, time, context, policy snapshot, decision, and evidence references.

5. **Graph-Based Agent Orchestration**
   - Agent workflows are implemented as stateful graphs (nodes + edges + shared state) for clarity, control, replay and testing.

6. **Cascaded LLM Usage**
   - For AI reasoning, we use cascades: base model → large model → human escalation, under explicit routing rules and guardrails.

7. **Governed RAG**
   - Retrieval-augmented context always comes from source-of-truth systems (git, CI, docs, incidents, observability), with classification, access control and redaction.

---

## 3. Cross-Cutting Planes

### 3.1 Control & FinOps Plane

**Scope:** identity, policy, routing, budgets, audit, observability.  
**Applies to:** Layers 2–6.

#### 3.1.1 Functional Responsibilities

- Attach `actor_id`, `actor_type` (human / AI / hybrid), `device_id`, `tenant_id`, and `time_base` to every event and decision.
- Manage GSMD and policy bundles (compile → sign → distribute).
- Configure and enforce cascaded LLM profiles and routing policies.
- Enforce cost and latency budgets per tenant/module/surface.
- Collect receipts and derive metrics.

#### 3.1.2 Core Services

1. **Identity & Tenant Service**

   - Issues and validates:
     - `tenant_id`
     - `actor_id` (human / AI / hybrid)
     - `device_id` (edge machines)
   - Integrates with external identity providers when available.

2. **Policy & GSMD Service**

   - Stores GSMD modules in a git-backed repository.
   - Compiles policies into immutable PolicyBundles, e.g.:
     ```json
     {
       "bundle_id": "pol-M01-risk-gate-v3",
       "snapshot_hash": "sha256-...",
       "module_id": "M01",
       "version": "3.0.0",
       "rules": { },
       "llm_routing_policies": { },
       "guardrail_configs": { }
     }
     ```
   - Publishes bundles to Edge Agents and backend workers using signed manifests.

3. **Routing & Cascade Manager**

   - Stores cascaded LLM profiles per capability:
     ```json
     {
       "capability_id": "risk_explanation_v1",
       "base_model": "slm-local-8b",
       "large_model": "llm-cloud-70b",
       "deferral_policy_id": "def-risk-exp-01",
       "abstention_policy_id": "abst-risk-exp-01"
     }
     ```
   - Applies deferral/abstention policies when the LLM Router (Layer 1) is invoked.

4. **Budget & Rate-Limit Service**

   - Tracks budgets per `(tenant_id, module_id, surface)`:
     - maximum tokens per period,
     - maximum cost per period,
     - maximum QPS or concurrency.
   - Can reject, downgrade or delay calls when budgets are exhausted.

5. **Receipts & Metrics Service**

   - Stores append-only JSONL receipts, for example:
     ```json
     {
       "receipt_id": "rcpt-2025-12-05T10-23-01Z-1234",
       "trace_id": "trace-abc",
       "timestamp": "2025-12-05T10:23:01.234Z",
       "tenant_id": "t-acme",
       "actor_id": "dev-123",
       "actor_type": "human",
       "agent_id": "edge-m01",
       "event_type": "pr_risk_evaluated",
       "policy_snapshot_hash": "sha256-...",
       "context_hash": "ctx-...",
       "decision": "soft_block",
       "llm_calls": [
         {
           "model_id": "slm-local-8b",
           "role": "base",
           "tokens_in": 540,
           "tokens_out": 210,
           "cost_estimate": 0.0021
         }
       ],
       "evidence_refs": ["git://...", "ci://..."]
     }
     ```
   - Exposes metrics and reporting views derived from receipts only.

---

### 3.2 Safety, Guardrails & Data Governance Plane

**Scope:** privacy, redaction, safety, policy adherence.  
**Applies to:** Layers 3–5 primarily (but influences all).

#### 3.2.1 Functional Responsibilities

- Perform redaction and data minimisation on-device before data leaves the laptop.
- Classify artefacts and enforce sensitivity-based access rules.
- Apply input/output guardrails for prompts, tool calls and LLM responses.
- Provide trust/hallucination scoring and trigger escalation when needed.

#### 3.2.2 Core Services

1. **Edge Redaction Filter**

   - Runs inside the Edge Agent.
   - For any off-device call, converts raw signals into:
     ```json
     {
       "safe_context_bundle": {
         "code_snippets": [ ],
         "metadata": { },
         "tests": [ ],
         "logs": [ ]
       },
       "context_hash": "ctx-...",
       "classifications": {
         "contains_secrets": false,
         "pii_risk": "low"
       }
     }
     ```
   - Never sends full repositories or secret values off-device.

2. **Data Classification & Access Control**

   - Assigns labels such as `public`, `internal`, `confidential` to artefacts.
   - Enforces which tools and agents can access which labels.

3. **Guardrail Engine**

   - Deterministic and/or model-based checks on:
     - Prompts and tool arguments.
     - LLM responses.
   - Enforces allowed output types, structure and prohibited content categories.
   - Integrates into Verifier nodes in graphs.

4. **Verifier / Judge Models**

   - For critical flows (release, security, compliance), run a verification step:
     - trust score,
     - hallucination risk,
     - policy compliance indicators.
   - If below threshold, downgrade decisions or escalate to humans.

---

### 3.3 Behaviour & Evaluation Plane

**Scope:** behavioural intelligence, evaluation, simulation, learning.  
**Applies to:** Layers 4–7.

#### 3.3.1 Core Components

1. **Behavioural Knowledge Graph (BKG)**

   - A graph linking:
     - Actors (human / AI)
     - Artefacts (files, services, tests, dashboards)
     - Events (PRs, builds, deploys, incidents)
     - Outcomes (rollbacks, SLA breaches, successful releases)
   - Built incrementally from receipts and integrations.

2. **Evaluation Harness**

   - Scenario suites per module:
     ```json
     {
       "scenario_id": "M01.SCN.001",
       "description": "Large risky PR with failing tests",
       "inputs": { },
       "expected_decision": "hard_block",
       "expected_receipt_fields": { }
     }
     ```
   - Executes on:
     - policy changes,
     - graph changes,
     - routing/model changes.

3. **Shadow / Replay Runner**

   - Replays historical PRs and incidents through new graphs and policies in shadow mode.
   - Produces labelled receipts (`mode: "shadow"`) for comparison with production behaviour.

4. **Cascade Tuning Logic**

   - Uses feedback, receipts and evaluation results to tune:
     - deferral thresholds (base→large),
     - abstention thresholds (model→human),
     - routing policies per module.

---

## 4. The Seven Layers

### 4.1 Layer 1 – Foundation Models & Multi-Model LLM Infrastructure

**Role:** unified, governed entry point for all embedding and LLM calls.

#### 4.1.1 Responsibilities

- Register all available models (local and remote).
- Implement cascaded LLM patterns (base → large → human).
- Enforce routing and budget policies from the Control Plane.
- Return telemetry for receipts and FinOps.

#### 4.1.2 Components

1. **Model Registry**

   - Maintains metadata for each model:
     ```json
     {
       "model_id": "llm-cloud-70b",
       "provider": "tenant-cloud",
       "family": "general_reasoning",
       "context_length": 128000
     }
     ```

2. **LLM Router**

   - Input:
     ```json
     {
       "tenant_id": "t-acme",
       "capability_id": "pr_risk_explanation_v1",
       "requested_quality": "high",
       "budget_id": "budget-M01",
       "policy_snapshot_hash": "sha256-...",
       "routing_policy_id": "route-M01-01",
       "safe_context_bundle": { },
       "prompt": "Explain why this PR is risky.",
       "meta": {
         "loc_changed": 1200,
         "files_changed": 32
       }
     }
     ```
   - Output:
     ```json
     {
       "chosen_model_id": "llm-cloud-70b",
       "raw_response": "...",
       "tokens_in": 800,
       "tokens_out": 250,
       "cost_estimate": 0.008,
       "cascade_trace": [
         { "step": "base_model", "result": "deferral" },
         { "step": "large_model", "result": "accepted" }
       ]
     }
     ```

3. **Provider Adapters**

   - Implement the actual calls to local models and remote APIs.
   - Always invoked through the LLM Router; never directly from graphs.

---

### 4.2 Layer 2 – Agent Runtime & Infrastructure

**Role:** execute graphs and tools on Edge and backend, reliably and reproducibly.

#### 4.2.1 Components

1. **Edge Agent Runtime**

   - Long-running process (service) on the developer’s laptop.
   - Responsibilities:
     - Subscribe to IDE events (PR previews, save, commands).
     - Run configured graphs locally where possible.
     - Call backend only when necessary.
     - Maintain local receipts, policy cache and semantic cache.

2. **Backend Worker Runtime**

   - Stateless workers in tenant or product cloud.
   - Consume events from a queue or webhook feeder.
   - Execute graphs that require heavier compute or shared resources.

3. **Event Bus**

   - Logical abstraction that carries `AgentEvent` objects.
   - Implementation can be in-process queue, message broker or HTTP dispatcher.

4. **Persistence**

   - Local:
     - `~/.zeroai/receipts.log`
     - `~/.zeroai/semantic_cache.db`
   - Backend:
     - append-only receipts store,
     - indices and context stores (Layer 5).

---

### 4.3 Layer 3 – Protocols & Contracts (ZAP – ZeroUI Agent Protocol)

**Role:** canonical schemas for all messages and decisions in the system.

#### 4.3.1 Key Schemas

1. **AgentEvent**

   ```json
   {
     "event_id": "evt-2025-12-05T10-23-01Z-1",
     "trace_id": "trace-abc",
     "tenant_id": "t-acme",
     "actor_id": "dev-123",
     "actor_type": "human",
     "agent_id": "edge-m01",
     "surface": "vscode",
     "event_type": "git.pr.opened",
     "time_base": "2025-12-05T10:23:01.234Z",
     "payload": {
       "repo": "acme/checkout",
       "pr_number": 42,
       "branch": "feature/risky-change"
     }
   }
   ```

2. **AgentState** (conceptual representation)

   ```json
   {
     "trace_id": "trace-abc",
     "tenant_id": "t-acme",
     "policy_snapshot_hash": "sha256-...",
     "context_hash": null,
     "event": { },
     "intermediate_results": { },
     "decisions": [ ]
   }
   ```

3. **AgentDecision**

   ```json
   {
     "decision_id": "dec-...",
     "trace_id": "trace-abc",
     "module_id": "M01",
     "outcome": "soft_block",
     "severity": "high",
     "summary": "PR too large and touches risky services",
     "explanations": [
       "loc_threshold_exceeded",
       "critical_service_changed"
     ]
   }
   ```

4. **ToolInvocation**

   ```json
   {
     "tool_id": "git.diff_summary",
     "args": {
       "repo": "acme/checkout",
       "pr_number": 42
     },
     "invocation_id": "tool-...",
     "trace_id": "trace-abc"
   }
   ```

5. **Receipt**

   - Defined by the Control Plane and used uniformly by Edge and backend.

ZAP schemas are kept stable and versioned; breaking changes require explicit migrations.

---

### 4.4 Layer 4 – Orchestration (Graph Runtime & Cascades)

**Role:** implement all agent logic as stateful graphs with explicit nodes and edges.

#### 4.4.1 Concepts

- **Graph** – named workflow for a module, e.g. `M01_PR_Risk_Graph_v1`.
- **Node** – deterministic function that:
  - reads `AgentState`,
  - performs work (retrieval, tool call, LLM call, rule evaluation),
  - returns a delta to state plus optional decision.
- **Edge** – control-flow rule that links nodes conditionally.

#### 4.4.2 Standard Node Types

- `CollectorNode` – gather metrics, diff summaries, test results, incident links.
- `RouterNode` – select cascade profile; decide base vs large model, and whether to call at all.
- `BaseModelNode` / `LargeModelNode` – invoke Layer 1 with appropriate profile.
- `VerifierNode` – apply guardrails and trust checks.
- `GateNode` – compute the final gate decision: pass / warn / soft_block / hard_block.
- `CoachNode` – generate actionable guidance for the VS Code UI / CI checks.
- `RemediatorNode` – suggest or apply automated fixes (where safe).
- `HumanEscalationNode` – request human input and record that the model abstained.

#### 4.4.3 Execution Behaviour

- Each node is idempotent for a given state.
- After significant nodes, the runtime:
  - updates `AgentState`,
  - emits a receipt with node outcome.
- Graph engine supports:
  - conditional edges,
  - limited loops with safeguards,
  - checkpoints to allow resume and replay.

---

### 4.5 Layer 5 – Context, Governed RAG & Tools

**Role:** provide governed, high-quality context and tools to graphs and LLMs.

#### 4.5.1 Context Service (Governed RAG)

- Request:
  ```json
  {
    "request_id": "ctx-req-...",
    "tenant_id": "t-acme",
    "scope": {
      "repo": "acme/checkout",
      "branch": "feature/risky-change",
      "files": ["src/payments/*.py"]
    },
    "question": "What changed in this PR that affects rollback safety?",
    "max_items": 20
  }
  ```

- Response:
  ```json
  {
    "context_hash": "ctx-...",
    "safe_context_bundle": {
      "code_snippets": [ ],
      "test_snippets": [ ],
      "deploy_history": [ ],
      "incident_summaries": [ ]
    }
  }
  ```

- Implementation uses adapters for:
  - git provider,
  - CI pipelines,
  - observability stack,
  - docs and incident systems,
  - local file system where appropriate.
- All retrieved data is classified and redacted via the Safety Plane before being exposed.

#### 4.5.2 Semantic Q&A Cache

- Purpose: avoid recomputing explanations for similar questions under the same context and policy snapshot.
- Key:
  ```text
  key = hash(normalised_question, context_hash, policy_snapshot_hash, tenant_id)
  ```
- Value:
  ```json
  {
    "answer_text": "...",
    "original_receipt_id": "rcpt-...",
    "created_at": "2025-12-05T10:23:01Z"
  }
  ```
- Used only for explanations and coaching; gates always recompute decisions or rely on deterministic logic.

#### 4.5.3 Tool Adapters

- Tools include (examples):
  - `git.diff_summary`
  - `tests.status_for_pr`
  - `deploy.info_for_version`
  - `incident.lookup_by_service`
  - `metrics.summary_for_window`
- Each tool:
  - has a stable `tool_id` and version,
  - is a pure function from input → JSON output,
  - is invoked via the graph runtime and logged in receipts.

---

### 4.6 Layer 6 – Applications (Pain-Point Modules)

**Role:** each SDLC pain-point is a self-contained agentic application.

#### 4.6.1 Module Definition Template

For each module (e.g., `M01 – Release Failures & Rollbacks`), define:

- `module_id` and human-readable name.
- Triggers (events):
  - `git.pr.opened`, `git.pr.updated`,
  - `ci.pipeline.failed`,
  - `deploy.slo_breach`, etc.
- Graphs (Layer 4):
  - for example, `M01_PR_Risk_Graph_v1`, `M01_PostRelease_RCA_Graph_v1`.
- Policies and GSMD snapshot:
  - gates, thresholds, cascade profiles, guardrails.
- Surfaces:
  - VS Code:
    - status pill,
    - diagnostics and Quick Fix,
    - decision card.
  - CI:
    - check status,
    - evidence links.
- Metrics:
  - detection and intervention latency,
  - false-positive rate,
  - cost per event,
  - developer interaction patterns.

#### 4.6.2 Example Module – M01 PR Risk Gate

- Trigger: `git.pr.opened`.
- Graph outline:
  1. `CollectorNode` – collect diff, file types, coverage, service ownership, incident history.
  2. `RouterNode` – choose cascade profile using static heuristics and routing policy.
  3. `BaseModelNode` – quick assessment; may defer.
  4. `LargeModelNode` – detailed reasoning with governed context.
  5. `VerifierNode` – guardrails and trust checks.
  6. `GateNode` – final pass/warn/soft_block/hard_block.
  7. `CoachNode` – produce useful explanations and remediation guidance.
- Outputs:
  - VS Code status pill + diagnostics,
  - CI check with structured rationale,
  - receipts with evidence IDs.

---

### 4.7 Layer 7 – Governance, Observability & Platform Portal

**Role:** provide human owners with visibility and control; host the platform-level “pane of glass”.

#### 4.7.1 Governance Dashboards

- Per tenant and module, display:
  - activation state (POC / MVP / Pilot / Production),
  - volume of events,
  - decision distributions (pass/warn/soft_block/hard_block),
  - cascade usage (base vs large vs human),
  - guardrail incidents and hallucination audit metrics,
  - FinOps metrics (cost and budget usage).

#### 4.7.2 ZeroUI Platform Portal

- Exposes:

  - **Module Catalog**
    - descriptions,
    - inputs/outputs,
    - GSMD versions,
    - owners and escalation contacts.
  - **Solution Lifecycle**
    - state per module and tenant,
    - last evaluation run,
    - last policy change.
  - **Evidence Links**
    - pointers into receipts store and evaluation reports.

#### 4.7.3 Governance Processes

- Policy change workflow:
  - policy change PR → evaluation harness → shadow replay → governance approval → PolicyBundle release.
- Model governance:
  - register/approve models,
  - map models to modules/tenants,
  - track versions and deprecations.
- FinOps rules:
  - budgets per module and tenant,
  - automatic throttling or alerts when thresholds are approached.

---

## 5. Example End-to-End Flows

### 5.1 PR Risk Evaluation Flow

1. Developer opens a PR in VS Code.  
2. VS Code extension sends an `AgentEvent` to the Edge Agent.  
3. Edge Agent runs initial `CollectorNode` locally and fetches context via the Context Service.  
4. Edge redaction filter produces `safe_context_bundle` and `context_hash`.  
5. Graph’s `RouterNode` calls Layer 1 LLM Router with the chosen cascade profile.  
6. Cascaded LLM invokes base and possibly large model according to policy and budgets.  
7. `VerifierNode` applies guardrails and trust checks.  
8. `GateNode` computes decision; `CoachNode` produces guidance.  
9. Edge Agent writes receipts locally and (if allowed) to backend.  
10. VS Code surfaces the result via the status pill and diagnostics; CI sees the gate decision.

### 5.2 Policy Change Flow

1. Platform owner edits GSMD/policies for a module in the policy repo.  
2. CI pipeline validates schemas and runs evaluation harness.  
3. Shadow runner replays recent events using new policies; results are compared.  
4. Governance owner approves the change.  
5. Policy & GSMD Service publishes a new PolicyBundle with a new `snapshot_hash`.  
6. Edge Agents and backend workers pull the bundle and start using the new `policy_snapshot_hash` in receipts.  
7. Governance dashboards show rollout status and behavioural impact.

---

## 6. Phased Implementation Plan (High-Level)

1. **Phase 0 – Foundations**
   - Implement ZAP schemas and a minimal receipts library.
   - Implement simple config-driven Control Plane (no UI yet).

2. **Phase 1 – Edge Agent + Basic PR Risk Gate**
   - Build Edge Agent runtime and VS Code integration.
   - Implement deterministic PR size/risk gate without LLMs.
   - Wire receipts and basic governance views.

3. **Phase 2 – LLM Router & Guardrails**
   - Implement Layer 1 Router with cascades and budgets.
   - Implement redaction + guardrail engine.
   - Add LLM-powered explanations for the PR risk gate.

4. **Phase 3 – Graph Runtime + Additional Modules**
   - Implement generic graph runtime (Layer 4) and move M01 onto it.
   - Add additional modules (Merge Conflicts, Legacy Safety).

5. **Phase 4 – Governance Portal & Behavioural Analytics**
   - Build Behavioural Knowledge Graph and evaluation harness.  
   - Add governance dashboards and a minimal platform portal.  
   - Add shadow/replay runners for safe evolution.

---

This blueprint can be stored as `ARCH_ZEROUI_7_LAYER_BLUEPRINT.md` in the repository to guide implementation and reviews.
