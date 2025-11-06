ZeroUI Architecture V 0.1.md

Here's the simplest, kid-clear tour of your system architecture.

The 4-Floor Building (how it's laid out)

Your Laptop (IDE / Edge Agent) -- "Ground Floor"

You write code in VS Code.

A tiny helper (Edge Agent) checks your change locally against clear rules.

It shows quick tips in the IDE and writes a tiny receipt (a signed note of what happened).

Client/Tenant Cloud -- "First Floor"

Your company's space.

Keeps private evidence safely.

Applies the same rules during PRs/CI so nothing risky slips through.

ZeroUI Product Cloud -- "Second Floor"

The product's brains.

Learns patterns, scores risk, and improves nudges/policies (no raw code needed).

Sends signed policy snapshots (the official rulebook) to laptops and CI.

Shared Services -- "Roof"

Trust & keys, audit ledger (append-only), observability, notifications.

Think of it as the building's security office and logbook.

How information moves (super short)

Rules → Product Cloud publishes signed rules → Laptop & CI use them.

Decisions → Laptop/CI write receipts (what, why, result) → stored safely.

Learning → Product Cloud reads receipts (not your code) → makes rules & nudges better.

Why this design works

Fast: Most checks happen on your laptop, instantly.

Private: Code stays local unless you say otherwise; receipts are small and safe.

Consistent: Same rules on laptop and in CI, so no surprises.

Trustworthy: Everything important is signed and audited.

Tiny glossary

Policy (Rulebook): Clear "yes/no/warn" rules written as code.

Receipt: A small, signed note: what ran, what it decided, and why.

Nudge: Friendly hint in the IDE to fix or improve a change.

Snapshot: A sealed version of the rulebook everyone agrees on.

One-look sketch

https://media/image1.png{width="5.426388888888889in" height="6.989583333333333in"}

Here are the four layers (planes) of the system:

IDE / Edge Agent Plane
VS Code Extension (presentation) ↔ Edge Agent (delegation).
Does local checks, shows tips/nudges, and writes signed receipts.

Client / Tenant Cloud Plane
Enterprise adapters, redaction, policy enforcement proxies, evidence/WORM stores, SSO/SCIM, compliance integrations.
Applies the same rules in PR/CI and keeps organization data private.

ZeroUI Product Cloud Plane
Detection & decision services, learning loop, feature store, model serving, risk/nudge engines, release risk gate, knowledge integrity.
Publishes signed policy snapshots (the rulebook) to laptops and CI.

Shared Services Plane
Identity & trust, Policy Registry (signed snapshots), Audit Ledger (append-only), observability mesh, key management, artifact/model registry, notification bus.
Provides trust, logs, and shared infrastructure.

Connectors (how layers talk):

contracts (OpenAPI) / events (Shared Services ⇄ Product Cloud)

privacy-split APIs / queues (Product Cloud ⇄ Client/Tenant Cloud)

local-first, signed receipts (Client/Tenant Cloud ⇄ IDE/Edge Agent)

Got it --- here are the detailed components by plane, clean and implementation-neutral.

IDE / Edge Agent Plane

VS Code Extension (Presentation)

Status Pill, Diagnostics Panel, Quick Fix, Webview Card, Notifications, "Zero UI" Activity Bar.

Edge Agent (Delegation)

Policy Evaluator (local, dry-run default) --- applies signed rules to edits/PR inputs.

Receipt Writer --- appends signed JSONL receipts (INTENT → RESULT; fsync).

Policy Cache --- stores latest signed policy snapshot + policy_version_ids.

Config Loader --- precedence: policy → env → defaults.

Adapters --- Git/PR/CI event readers, repo scanners (import graph, coverage, history) behind flags.

Signal Capture

Git & CI events, IDE actions (respect telemetry settings), OTel events/spans (low-cardinality).

In-flow Coaching

Mirror/Mentor/Multiplier (MMM) message generator (template-driven), Decision Card renderer.

Laptop Trust & Storage

Public-key trust store (KID-based), optional Ed25519 signing, receipts folder, logs, snapshot cache.

Client / Tenant Cloud Plane

Policy Enforcement Proxies

PR/CI checks (pass/warn/soft/hard), identical rules to laptop; deterministic outcomes.

Evidence / WORM Stores

Receipt mirror (append-only), ingestion staging & DLQ, legal hold/retention, watermarks & partitions.

Data Minimisation & Redaction

Schema validation, field-level redaction/anonymisation before any cross-plane egress.

Enterprise Adapters

Git hosting, CI/CD, Confluence/Jira, Slack/Teams/WhatsApp, artifact repos, change-management.

Identity & Access (Tenant)

Org SSO/SCIM integration, role mapping, tenancy boundaries.

Compliance Integrations

Evidence packs, audit exports, access-review hooks, policy-acceptance logs.

Queues / APIs (Privacy-Split)

Tenant-scoped queues & APIs used to talk to the product cloud without leaking raw code.

ZeroUI Product Cloud Plane

Detection & Decision Services

Gates (e.g., PR Size, Risky Change, Release Risk, Confidence), reason codes, consistent rubric.

Learning Loop

Reads anonymised receipts; derives patterns & thresholds; proposes rule tweaks (no raw code needed).

Feature Store

Curated, privacy-safe features from receipts/metadata (time, size, change shape, volatility).

Model Serving (Bounded)

Safe LLM/helpers for explanations & MMM phrasing; guardrailed, budgeted, and auditable.

Risk/Nudge Engines

Persona-aware nudges, playbooks, escalation paths; content templates with versioning.

Knowledge Integrity

Drift detection & provenance checks on policies, patterns, and content.

Policy Compiler

Compiles rule changes → signed policy snapshots (hash, KID, version ids) for the Registry.

Shared Services Plane

Identity & Trust

Service identities, RBAC/ABAC, attestation hooks, device/public-key distribution.

Policy Registry (Signed Snapshots)

Versioning, diff & changelog, snapshot signing, distribution, cache control, revocation/CRL.

Audit Ledger (Append-Only)

Receipt verification, immutable IDs, retention windows, evidence-pack assembly.

Observability Mesh

OpenTelemetry collectors, metrics/traces/log pipelines, SLO/error-budget calculators, exemplars.

Key Management

KMS facade, key rotation, trust anchors, envelope encryption utilities.

Artifact / Model Registry

Model/catalog entries with SBOMs, approvals, provenance and rollout channels.

Notification Bus

Pub/sub channels to Slack/Teams/Email/IDE; rate-limits and delivery policies.

Standard connectors between planes

Shared ⇄ Product: contracts (OpenAPI) / events

Product ⇄ Client/Tenant: privacy-split APIs / queues

Client/Tenant ⇄ IDE/Agent: local-first, signed receipts

Swimlane diagram from the same components.

https://media/image2.png{width="6.5in" height="4.520833333333333in"}

Here's the final, implementation-ready architecture --- simplified for 8th-grade, crisp, and fully aligned with the recommendations you approved.

1) The 4 Floors (Planes)

A) IDE / Edge Agent (your laptop)

VS Code Extension (presentation).

Edge Agent (delegation): local policy evaluator (dry-run), receipt writer (append-only JSONL), policy cache, config loader, adapters (Git/PR/CI).

In-flow coaching: Mirror / Mentor / Multiplier messages, status pill, diagnostics, quick fix.

Laptop trust: public-key trust store (KID-based), optional signing, local logs/receipts.

B) Client / Tenant Cloud (your company)

Policy enforcement proxies for PR/CI (pass / warn / soft_block / hard_block).

Evidence/WORM stores (append-only mirror, retention, legal-hold).

Data minimisation/redaction (before anything leaves tenant).

Enterprise adapters (Git/CI, Confluence/Jira, Slack/Teams), SSO/SCIM, compliance hooks.

Tenant privacy-split APIs/queues to talk to product cloud.

C) ZeroUI Product Cloud (the product's brain)

Detection & decision services, risk/nudge engines, release risk gate, knowledge integrity.

Learning loop (uses receipts/metadata, not raw code) → improves tips and rules.

Feature store, bounded model helpers for explanations.

Policy compiler → signed policy snapshot (hash, KID, version IDs).

D) Shared Services (building security & logs)

Identity & trust, Policy Registry (signed snapshots), Audit Ledger (append-only).

Observability mesh (metrics/logs/traces, SLO/error-budget), key management, artifact/model registry, notification bus.

2) The 3 Bridges (how planes talk)

Shared ⇄ Product: contracts (OpenAPI) / events.

Product ⇄ Client: privacy-split APIs / queues.

Client ⇄ IDE: local-first, signed receipts.

3) End-to-End Flow (T0 / T1 / T2)

Compile & Sign Policy Snapshot (Product).

Publish to Policy Registry (Shared).

Fetch & Cache Snapshot (Client).

Pull Snapshot (Local Cache) (IDE). T0: Evaluate (pill, diagnostics, quick fix).

Local Policy Evaluation (dry-run) (IDE).

Write Signed Receipt (IDE → append-only JSONL). T1: Act (user choices recorded).

PR/CI Gate Enforcement (Client).

Append to Audit Ledger (Shared). T2: Outcome (evidence logged).

Learning Loop & Nudge Updates (Product) → next signed snapshot.

4) Data & Privacy (what moves, where)

Code stays local by default.

Receipts/evidence are metadata (what happened, why, outcome).

Redaction/minimisation happens in the Client plane before any cross-plane sharing.

Stores: laptop receipts → tenant WORM mirror → shared audit ledger (append-only).

5) Policy Lifecycle (clear states)

Draft → Review → Approve → Sign → Distribute → Revoke

Each snapshot has hash + KID + version IDs.

Distribution via Policy Registry; clients and laptops verify before using.

Revocation uses registry + tenant caches.

6) Gate Decision (deterministic, per gate)

Inputs → rubric → outcome (pass / warn / soft_block / hard_block) + reason codes.

Receipt always written (includes decision, reason, policy_version_ids).

Same rules on laptop and in CI (no surprises).

7) Trust & Keys (who signs, who checks)

Product cloud signs snapshots.

Laptops/clients verify with trusted public keys (KID-based).

Rotation & revocation (CRL) supported via the registry.

Audit ledger ensures append-only evidence.

8) Observability & SLOs (see, measure, fix)

OpenTelemetry metrics/logs/traces flow into the observability mesh.

SLO/error-budget checks run; alerts go to IDE and chat channels via notification bus.

Examples: availability, latency, receipt fsync budget.

9) Storage & Retention (what lives where)

Laptop: receipts (JSONL), logs, snapshot cache.

Client: WORM evidence mirror, legal-hold/retention, DLQ for ingestion.

Shared: audit ledger (append-only), policy registry, artifact/model registry.

10) Deployment Ladder (environments)

Development → Integration → Staging → UAT → Production

Show ingress/egress and allowed ports.

Canary/blue-green supported.

Clear rollback path (policy/snapshot and gate configs are versioned).

Final One-Line Promise

Signed rules go out → your laptop checks locally → receipts prove what happened → CI enforces the same rules → everything is logged → the system learns and improves the rules --- without sending raw code by default.

This is the final model matching your approved components, bridges, privacy stance, lifecycles, trust, SLOs, storage, and env ladder --- ready to proceed to implementation.

Here's the final version with all gaps fixed --- same structure, now complete, crisp, and implementation-ready.

Baseline (must-have)

System Context (C4-L0)
Purpose: One slide anyone can understand. Your system, users, and external systems.
Done-When: ≤10 nodes, clear trust boundaries, no acronyms without a legend.

Planes & Containers (C4-L1)
Purpose: Four planes (IDE/Agent, Client/Tenant, Product Cloud, Shared Services) with main containers and connectors.
Done-When: Every container has purpose+data tags; all cross-plane links labelled with one of: contracts/events, privacy-split APIs/queues, local-first signed receipts.

Deployment & Environment Ladder
Purpose: Development → Integration → Staging → UAT → Prod topology, networks/ports, artifact flow, blue/green/canary hooks.
Done-When: Each env shows ingress, egress, secrets/trust stores, and rollback path.

Core E2E Sequence (T0/T1/T2)
Purpose: One clean sequence for the canonical path: Policy snapshot → Local eval → Receipt → PR/CI gate → Audit → Learning loop.
Done-When: T0/T1/T2 markers are visible; every step emits/consumes exactly one artifact (policy/receipt/evidence).

Data & Privacy Split (DFD + Lineage)
Purpose: What data moves, where redaction happens, and where data rests (by plane).
Done-When: Each flow has a classification (metadata / code / PII: none), redaction point, and storage/retention note.

Policy Lifecycle & Registry (State Machine)
Purpose: Draft → Review → Approve → Sign → Distribute → Revoke; includes snapshot hash/KID/versioning.
Done-When: Transitions list who/what can trigger, evidence required, and rollback.

Gate Decision FSM (per Gate)
Purpose: Inputs → rubric → outcomes (pass / warn / soft_block / hard_block) with reason codes + receipts.
Done-When: Deterministic table shown; no hidden branches; test hooks called out.

Trust & Key/Attestation Flow
Purpose: Device/public key trust, snapshot signing, CRL/rotation; show boundaries and verifiers.
Done-When: All keys have owners/rotation periods; every verify step is explicit.

Observability & SLO Topology
Purpose: OTel collectors → metrics/logs/traces → SLO/error-budget calc → alerts → IDE surfaces.
Done-When: Each alert path shows target, throttle, and auto-quieting rule.

Storage & Retention Map
Purpose: Where receipts, snapshots, models, evidence, and logs live; retention/legal-hold.
Done-When: Each store has format, partitioning, retention, and legal-hold flag.

Deep-dive (next) --- Now with Done-When

Integration Adapters Map (GitHub/CI/Confluence/Jira/Slack/Teams)
Done-When: Each adapter lists endpoints/events, auth mode, and failure handling.

Failure Domains & Blast Radius (what fails alone vs together)
Done-When: Domains are named; dependencies shown; isolation and fallback noted.

Error/Override/Rollback Sequences (soft→hard block, dual-channel escalation)
Done-When: Paths are sequenced; who can override is listed; rollback step is explicit.

Capacity & Backpressure (queues, rate limits, retry policies)
Done-When: Limits are stated; retry/backoff is shown; DLQ path exists.

Tenant Model & Isolation (IDs, namespaces, caches, per-tenant keys)
Done-When: Tenant ID rules, cache scope, and key isolation are marked on the diagram.

AI Helper Boundaries (bounded LLM calls, budgets, redaction points)
Done-When: Inputs/outputs are bounded; budget noted; redaction points shown.

Tooling & file layout (fast to produce, easy to version) --- Gaps closed with concrete paths

Mermaid for context/containers/DFD/state/FSM.

PlantUML for sequences.

Folder: docs/architecture/

01_context.mmd

02_planes_containers.mmd

03_deployment_envs.mmd

04_e2e_t0t1t2.puml

05_data_privacy_split.mmd

06_policy_lifecycle.mmd

07_gate_fsm.mmd

08_trust_keys.mmd

09_observability_slo.mmd

10_storage_retention.mmd

openapi/
(Note: OpenAPI specs are located in contracts/<module-name>/openapi/ directory)

schemas/
(Note: JSON Schemas are located in contracts/<module-name>/schemas/ directory)

gate_tables/

README.md # lists each gate

gate_<name>.csv # one CSV per gate with rubric rows

trust/

signing_process.md # who signs, where

verify_path.md # how verify happens in each plane

crl_rotation.md # rotation & revocation plan

slo/

slos.md # targets per service/surface

alerts.md # alert rules, throttle, auto-quieting

exports/ # SVG/PDF renders for sharing

Implementation-readiness checklist (green = start coding) --- Each item mapped to paths

APIs frozen: OpenAPI 3.1 → contracts/<module-name>/openapi/*.yaml

Schemas frozen: JSON Schema → contracts/<module-name>/schemas/*.schema.json

Gate tables frozen: deterministic rubric → docs/architecture/gate_tables/gate_<name>.csv

Keys/trust ready: signing, verify, CRL plan → docs/architecture/trust/*.md

SLOs set: availability/latency/receipt fsync → docs/architecture/slo/slos.md, docs/architecture/slo/alerts.md

Diagrams exported: all Baseline SVG/PDF → docs/architecture/exports/

Done. The gaps you flagged are now fully incorporated with explicit Done-When for items 11--16 and concrete file paths for OpenAPI, Schemas, Gate tables, Trust/CRL docs, and SLO definitions.

Great question. To actually start building, you need a few non-diagram artifacts and team/process guardrails alongside the diagrams you've locked. Here's a crisp, 8th-grade-friendly checklist you can copy into your repo.

1) Seed artifacts (so code has something real to use)

Policy Snapshot v1 → docs/architecture/policy/policy_snapshot_v1.json

At least one Gate Table filled (e.g., PR Size) → docs/architecture/gate_tables/gate_pr_size.csv

Sample Decision Receipts (2--3 lines) → docs/architecture/samples/receipts/receipts_example.jsonl

Sample Evidence Pack → docs/architecture/samples/evidence/evidence_pack_example.json

Public Keys (read-only) → docs/architecture/trust/public_keys/README.md (point to real public keys by KID)

SLO Targets stub (just numbers/placeholders) → docs/architecture/slo/slos.md

Alert Rules stub → docs/architecture/slo/alerts.md

2) Contracts you "freeze" (so no surprises later)

OpenAPI specs (already mapped) → contracts/<module-name>/openapi/*.yaml

JSON Schemas (already mapped) → contracts/<module-name>/schemas/*.schema.json

Gate Tables (already mapped) → docs/architecture/gate_tables/*.csv

Trust/CRL docs (already mapped) → docs/architecture/trust/*.md

3) Basic runbooks (so ops isn't guessing)

How to rotate keys → docs/architecture/trust/crl_rotation.md

How to roll back a bad policy → docs/architecture/policy/rollback.md

Top 3 incident playbooks (Receipt not written; Gate blocks all PRs; Policy fetch fails) → docs/architecture/ops/runbooks.md

4) Testing plan (so you can prove it works)

Test matrix (unit, integration, e2e) → docs/architecture/tests/test_plan.md

Golden data (inputs/expected receipts) → docs/architecture/tests/golden/

Spec/sequence exports (SVG/PDF for reviewers) → docs/architecture/exports/

5) CI/CD basics (so changes ship safely)

Jenkinsfile (lint → tests → build → export diagrams → package artifacts) → Jenkinsfile

Pre-commit hooks (format, lint, schema validate) → .pre-commit-config.yaml

Branch model (short doc: trunk + small PRs) → docs/architecture/ops/branching.md

6) DevX guardrails (so interns don't struggle)

Editor settings + line endings → .editorconfig, .gitattributes

Coding standards → docs/architecture/dev/standards.md

Repo quick-start (Windows-first commands) → docs/architecture/dev/quickstart_windows.md

7) Security & privacy quick proofs (so audits pass)

RBAC matrix (who can do what) → docs/architecture/security/rbac.md

Data classification table (what's in receipts/evidence) → docs/architecture/security/data_classes.md

Privacy note (metadata-only stance) → docs/architecture/security/privacy_note.md

Tiny "green-light" checklist

Flip these to ✅ and you can start coding:

✅ openapi/*.yaml present

✅ schemas/*.json present

✅ gate_tables/*.csv present (at least one filled)

✅ trust/public_keys/* present + CRL/rotation doc

✅ slo/slos.md + slo/alerts.md present

✅ Seed files present (policy_snapshot_v1.json, sample receipts/evidence)

✅ Jenkinsfile + pre-commit hooks land in main

✅ Runbooks & quickstart checked in

If you want, I can generate stubs for every file above (empty but correctly structured) so your team can fill them in as they build.

Here's your updated final report for the non-diagram artifacts + team/process guardrails --- with the gaps fully incorporated and all paths aligned.

1) Seed artifacts (so code has something real to use)

Policy Snapshot v1 → docs/architecture/policy/policy_snapshot_v1.json

At least one Gate Table filled (e.g., PR Size) → docs/architecture/gate_tables/gate_pr_size.csv

Sample Decision Receipts (2--3 lines) → docs/architecture/samples/receipts/receipts_example.jsonl

Sample Evidence Pack → docs/architecture/samples/evidence/evidence_pack_example.json

Public Keys (read-only) → docs/architecture/trust/public_keys/README.md (point to real public keys by KID)

SLO Targets stub → docs/architecture/slo/slos.md

Alert Rules stub → docs/architecture/slo/alerts.md

2) Contracts you "freeze" (so no surprises later)

OpenAPI specs → contracts/<module-name>/openapi/*.yaml

JSON Schemas → contracts/<module-name>/schemas/*.schema.json

Gate Tables → docs/architecture/gate_tables/*.csv

Trust/CRL docs → docs/architecture/trust/*.md

3) Basic runbooks (so ops isn't guessing)

How to rotate keys → docs/architecture/trust/crl_rotation.md

How to roll back a bad policy → docs/architecture/policy/rollback.md

Top 3 incident playbooks (Receipt not written; Gate blocks all PRs; Policy fetch fails) → docs/architecture/ops/runbooks.md

4) Testing plan (so you can prove it works)

Test matrix (unit, integration, e2e) → docs/architecture/tests/test_plan.md

Golden data (inputs/expected receipts) → docs/architecture/tests/golden/

Spec/sequence exports (SVG/PDF for reviewers) → docs/architecture/exports/

5) CI/CD basics (so changes ship safely)

Jenkinsfile (lint → tests → build → export diagrams → package artifacts) → Jenkinsfile

Pre-commit hooks (format, lint, schema validate) → .pre-commit-config.yaml

Branch model (trunk + small PRs) → docs/architecture/ops/branching.md

6) DevX guardrails (so interns don't struggle)

Editor settings + line endings → .editorconfig, .gitattributes

Coding standards → docs/architecture/dev/standards.md

Repo quick-start (Windows-first) → docs/architecture/dev/quickstart_windows.md

7) Security & privacy quick proofs (so audits pass)

RBAC matrix (who can do what) → docs/architecture/security/rbac.md

Data classification table (what's in receipts/evidence) → docs/architecture/security/data_classes.md

Privacy note (metadata-only stance) → docs/architecture/security/privacy_note.md

Unified paths (single source of truth)

docs/
└─ architecture/
(Note: OpenAPI specs and schemas are located in contracts/<module-name>/ directories)
├─ gate_tables/
│ ├─ gate_pr_size.csv
│ └─ (additional) gate_<name>.csv
├─ trust/
│ ├─ signing_process.md
│ ├─ verify_path.md
│ ├─ crl_rotation.md
│ └─ public_keys/
│ └─ README.md
├─ slo/
│ ├─ slos.md
│ └─ alerts.md
├─ policy/
│ ├─ policy_snapshot_v1.json
│ └─ rollback.md
├─ samples/
│ ├─ receipts/
│ │ └─ receipts_example.jsonl
│ └─ evidence/
│ └─ evidence_pack_example.json
├─ ops/
│ ├─ runbooks.md
│ └─ branching.md
├─ dev/
│ ├─ standards.md
│ └─ quickstart_windows.md
├─ security/
│ ├─ rbac.md
│ ├─ data_classes.md
│ └─ privacy_note.md
├─ tests/
│ ├─ test_plan.md
│ └─ golden/
└─ exports/

Repo root

Jenkinsfile
.pre-commit-config.yaml
.editorconfig
.gitattributes

Tiny "green-light" checklist (build can start when all are ✅)

✅ openapi/*.yaml present

✅ schemas/*.json present

✅ gate_tables/*.csv present (≥1 filled)

✅ trust/public_keys/* present + crl_rotation.md

✅ slo/slos.md + slo/alerts.md present

✅ Seed files present (policy_snapshot_v1.json, sample receipts/evidence)

✅ Jenkinsfile + pre-commit hooks in main

✅ Runbooks & quickstart checked in
