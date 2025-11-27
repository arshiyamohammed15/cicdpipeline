PM-1 – MMM Engine (Mirror-Mentor-Multiplier Engine)
Module Type: Platform Module
Surfaces: VS Code Extension (ZeroUI), Edge Agent, CI/PR checks, Alerting & Notification Service
Planes: CCP-1 (Identity & Trust), CCP-2 (Policy & Config), CCP-3 (Evidence & Audit), CCP-4 (Observability), CCP-6 (Data & Memory), CCP-7 (AI Lifecycle & Safety)

1. Summary & Intent
The MMM Engine is the central behaviour change orchestration service for ZeroUI. It takes signals about engineering work (risk, opportunities, context) and turns them into Mirror, Mentor, and Multiplier interventions that are:
Context-aware – grounded in real signals from UBI, Observability, CI/CD, etc.
Policy-constrained – only actions allowed by tenant policy and Gold Standards.
Safe & privacy-preserving – following NIST-style AI risk and privacy frameworks.
MMM does not directly enforce gates or ship code. It proposes and orchestrates helpful, non-coercive interventions that other modules render or enforce (ZeroUI extension, CI gates, Alerting & Notification Service, Policy Engine).

2. Problem Statement
Engineering teams are flooded with signals:
CI failures, incidents, review comments, security alerts, behavioural signals, etc.
Messages arrive in many tools, often too late or too noisy.
Teams end up:
Ignoring important signals (alert fatigue).
Missing early, low-effort fixes (small refactors, early tests).
Getting “big stick” enforcement (hard gates) without prior coaching.
We need a central engine that turns raw signals into gentle, contextual nudges and guided actions aligned with each team’s goals, without dark patterns or coercion. Digital nudging research stresses goal alignment, context-awareness, and non-coercive design as core success factors.

3. Goals & Non-Goals
3.1 Goals
Right nudge, right time, right surface
Transform heterogeneous signals into targeted MMM interventions that respect developer flow and do not create alert fatigue.
Mirror → Mentor → Multiplier progression
Mirror = awareness only (facts, trends, reflections).
Mentor = guided suggestions (what/why/how).
Multiplier = safe automation (do it for me, with explicit consent + policy gates).
Policy & safety-aligned
Enforce that all MMM actions are within tenant policy, AI safety rules (LLM Gateway), and privacy constraints.
Receipts-first & measurable
Every MMM decision and outcome is recorded as a receipt (ERIS), enabling governance, audits, and impact analysis.
Actor parity
Treat human developers and AI coding agents as first-class actors with common abstractions but explicit actor_type.
3.2 Non-Goals
MMM is not:
A replacement for the Policy/Gold Standards engine (it consumes policies).
A general experimentation platform for marketing or growth.
A productivity scoring system for individuals (no ranking/de-ranking).

4. Scope
4.1 In-Scope (v1)
MMM Engine service in the Tenant/Product cloud.
ZeroUI extension + Edge Agent integration for:
Pre-commit / pre-push nudges (status pill + cards).
PR comments and CI summaries via existing GitHub/CI adapters.
Nudges driven by:
UBI signals (behavioural opportunities/risks).
Detection Engine alerts (risk deviations).
Release / Incident / Testing modules (e.g., repeated rollbacks, flaky tests).
Mirror, Mentor, Multiplier playbooks defined per tenant.
4.2 Out-of-Scope (for v1)
Slack/Teams/WhatsApp channels (can be added via Alerting & Notification later).
Sophisticated multi-armed bandit tuning across many tenants (v1 uses simple score-based selection, bandit-like approaches are optional and must still respect risk frameworks).

5. Personas
Actor – human developer or AI coding agent using ZeroUI surfaces.
Tech Lead / Architect – defines desired behaviours and approves playbooks.
SRE / Ops Engineer – cares about stability interventions (incident MMM playbooks).
Tenant Admin – configures policies, permissions, and MMM capabilities per tenant.
Product Owner / Engineering Manager – tracks outcome metrics (fewer rollbacks, faster fixes).

6. Key Concepts
MMMContext – all context needed to decide: tenant, actor, repo, file, event, signals, environment.
MMMSignalInput – input events/signals (UBI BehaviouralSignals, Detection alerts, CI events, etc.).
MMMPlaybook – declarative rules mapping conditions → Mirror/Mentor/Multiplier actions and target surfaces.
MMMDecision – a concrete set of actions chosen for a given context.
MMMAction – one Mirror/Mentor/Multiplier intervention with payload (copy, metadata, surfaces).
MMMOutcome – how the actor/system responded (ignored, accepted, dismissed, executed, failed).
MMMExperiment – optional experiment metadata (control vs variant, treatment identifier).

7. High-Level Architecture & Data Flow
Signal Intake
MMM subscribes to event streams from PM-3 (normalised events), UBI (BehaviouralSignals), Detection Engine, CI/Release modules, and Health & Reliability Monitoring.
Context Construction
For each candidate signal, MMM resolves MMMContext using:
Identity & Trust Plane (actor, roles).
Policy & Config Plane (tenant MMM config, quiet hours, feature flags).
Data & Memory Plane (recent MMMOutcomes, optional summary state).
Playbook Evaluation
MMM evaluates all active playbooks against MMMContext and MMMSignalInput.
Produces one or more MMMAction candidates with Mirror/Mentor/Multiplier type and surfaces.
Safety & Policy Gating
For Mentor/Multiplier actions with generated content, MMM calls the LLM Gateway & Safety Enforcement module, which applies AI safety controls and risk management guidelines like NIST AI RMF (trustworthiness, harm, transparency).
All actions are filtered through tenant policy and Gold Standards (EPC-3/EPC-10).
Rate-Limiting & Fatigue Control
MMM applies per-actor and per-tenant limits, quiet hours, and fatigue rules to suppress or batch actions.
Delivery & Rendering
MMM returns actions to:
Edge Agent → VS Code extension;
CI/PR integration;
Alerting & Notification (EPC-4) for channel delivery where appropriate.
Receipts & Outcomes
Each MMMDecision emits a DecisionReceipt via ERIS (EPC-7).
MMM consumes outcome events (click/accept/override/ignore) to update its Memory and metrics.

8. Detailed Functional Requirements (FR)
FR-1 – Signal Intake & Normalisation
MMM MUST ingest signals from:
UBI BehaviouralSignals,
Detection Engine alerts,
Release/Incident/Test modules, and
Explicit triggers from Edge Agent/CI (e.g., “pre-commit evaluation”).
All intakes MUST use the normalised envelope defined by PM-3 and the Contracts & Schema Registry (EPC-12), including tenant_id, actor_id, actor_type, source, event_type, ts, and a structured payload.

FR-2 – Context Assembly
For each candidate MMM decision:
MMM MUST construct an MMMContext with:
actor details (from Identity & Trust Plane);
current repository/branch/file when available (from Edge Agent);
recent UBI signals;
relevant infra state (e.g., active incidents from Health & Reliability Monitoring);
tenant MMM configuration and policies.
The context MUST be computed with data minimisation, including only what is necessary for the decision, in line with privacy frameworks that emphasise collecting and processing the minimum data required for the specified purpose.

FR-3 – MMM Playbook Registry
MMM MUST maintain a registry of playbooks per tenant:
Each playbook includes:
metadata (id, tenant_id, name, description, owner, status);
trigger conditions (event/signal types, severity, actor roles);
preconditions (e.g., SLO/SLA breaches, chronic patterns, repeated behaviour);
action templates for Mirror/Mentor/Multiplier;
routing rules (surfaces, channels, quiet hours, escalation behaviour).
Playbooks MUST be versioned and stored via EPC-3/EPC-12 (Evidence & Contracts).

FR-4 – Mirror Actions
A Mirror action is read-only reflection of reality:
Examples:
“Your team’s PRs have required 3+ review cycles this week.”
“This change touches a high-risk module with repeated incidents.”
Mirror actions MUST:
contain no prescriptive language (“should/must”) beyond neutral statements;
be renderable as small IDE cards, PR comments, or CI summary notes;
be safe to show even without LLM content.

FR-5 – Mentor Actions
A Mentor action provides guided recommendations:
Examples:
Suggest tests, refactors, documentation, or pairing.
Link to specific runbooks, Gold Standards, or knowledge articles.
Mentor actions MAY use LLMs via the LLM Gateway & Safety Enforcement module, but:
generated content MUST pass safety filters and risk evaluation;
content MUST include why this action is proposed (linking to evidence and baseline deviations).

FR-6 – Multiplier Actions
A Multiplier action attempts to automate a safe change:
Examples:
Prepare a patch for adding missing tests.
Generate a draft rollback PR.
Multiplier actions MUST:
require explicit actor consent in the IDE/CI surface before execution;
be gated by policy and potentially dual-channel confirmation for sensitive operations (e.g., production rollback).
MMM orchestrates Multiplier actions but does not directly mutate code or infra; execution is delegated to Edge Agent/CI workflows that are subject to existing safety and approval flows.

FR-7 – Eligibility, Prioritisation & Fatigue Control
MMM MUST implement:
Eligibility checks, ensuring nudges are only evaluated when:
policy allows MMM for that actor/tenant;
signals meet minimum quality thresholds.
Prioritisation, so if multiple playbooks match, MMM ranks actions by:
severity/importance;
recency and frequency;
explicit tenant priority settings.
Fatigue control, enforcing:
max nudges per actor/time window and per repo;
quiet hours;
cool-downs for repeated conditions.

FR-8 – Surface Routing & Payload Adaptation
MMM MUST route each action to one or more surfaces:
IDE (ZeroUI extension via Edge Agent) – status pill + detail cards.
CI/PR – summary comment or check annotation.
Alerting & Notification Service – only for relevant events (e.g., serious incidents).
Payloads MUST be adapted per surface (short status vs detailed card) while preserving core content.

FR-9 – Adaptive Learning & Personalisation (Tenant-Scoped)
MMM MAY adapt playbook selection and intensities over time by:
Using aggregate response data (accept/ignore/dismiss/outcomes) at team/tenant level, not to rank individual performance.
Optionally using bandit-style or contextual bandit strategies (per tenant) to pick between candidate nudges and learn which patterns are more effective, a method widely used in recommendation systems for context-aware decision-making.
Adaptive logic MUST:
never override explicit policy;
never use protected attributes or unapproved features;
remain explainable at a high level (“this variant performed better for this type of situation”).

FR-10 – Safety, Ethics & Non-Coercion
MMM MUST:
follow digital nudging principles:
non-coercive, easy to ignore or opt out;
aligned with user/team goals;
context-aware and intuitive.
avoid “dark patterns” such as:
hiding dismissal controls;
making opt-out difficult;
using fear or misleading information.
honour tenant and actor-level preferences for categories of nudges.

FR-11 – Policy & Gold Standards Integration
MMM MUST:
resolve applicable policies and Gold Standards per decision via EPC-3/EPC-10 and CCP-2.
never propose actions that contradict:
explicit Gold Standard rules for that module or repo;
tenant restrictions (e.g., no auto-generated patches for production services).
respect override windows, exception approvals, and governance rules from Policy & Config.

FR-12 – Receipts & Governance Integration
For each MMMDecision and relevant MMMOutcome:
MMM MUST emit DecisionReceipts via ERIS that include:
tenant_id, actor_id/actor_scope, signal_ids, playbook_id/version;
proposed actions (type, surfaces);
policy snapshot identifiers;
whether content passed LLM safety (if applicable);
final outcome (shown/ignored/accepted/failed).
Receipts MUST conform to the ERIS schema and be written only through the Evidence & Audit Plane, not an ad-hoc local audit log.

FR-13 – Admin & Configuration Interfaces
MMM MUST expose admin interfaces (via APIs, not UI dashboards) for:
Managing playbooks (create/update/deprecate/publish).
Setting tenant MMM policies (enabled surfaces, quotas, quiet hours).
Defining experiments (treatments vs control) within safe bounds.
Viewing summary metrics (for admin personas) without exposing actor-level sensitive history.
All admin mutations MUST be authenticated, authorised, and receipt-logged.

FR-14 – Actor Controls & Preferences
MMM MUST:
honour per-actor preferences:
opt-out from certain categories (e.g., Multiplier actions);
snooze MMM for a period;
change preferred surfaces (IDE vs CI only).
expose these controls via Edge Agent APIs so the ZeroUI extension can provide a simple settings panel linked into the Policy/Config plane.

FR-15 – Observability & Debuggability
MMM MUST be fully observable:
Metrics for:
signals received; decisions made; actions proposed; actions delivered; actions accepted; actions resulting in positive outcomes.
Traces for:
signal → context → playbook → LLM safety → policy gate → surfaces.
Logs for:
failures, degraded modes, policy conflicts, ERIS write failures.
All observability data MUST respect privacy and redaction rules (no sensitive payloads in logs).

9. Non-Functional Requirements (NFR)
NFR-1 – Latency
For synchronous IDE/Edge calls to /v1/mmm/decide, MMM SHOULD respond within 150 ms p95 under normal load.
For CI/PR decisions, MMM SHOULD respond within 500 ms p95.
When these targets cannot be met, MMM MUST degrade gracefully (e.g., no nudges rather than partial/incorrect ones).

NFR-2 – Scalability
MMM MUST handle:
At least N decisions per minute per tenant (final value set by infra PRD).
Horizontal scaling via stateless workers, backed by a shared store for playbooks and state.

NFR-3 – Privacy & Data Minimisation
MMM MUST:
only process data necessary for decisions, in line with privacy frameworks that emphasise minimising data collection and limiting use to specified purposes.
respect Data Governance rules for:
retention;
residency;
deletion of actor-level history when requested by upstream policies.

NFR-4 – Trustworthy AI & Risk Management
MMM MUST align with the NIST AI RMF characteristics of trustworthy AI (validity, reliability, security, explainability, privacy, fairness, accountability) as applied to AI-driven decisions.
Any LLM-driven Mentor/Multiplier content MUST pass through the LLM Gateway & Safety module, which enforces content and safety policies.

NFR-5 – Multi-Tenancy & Isolation
MMM MUST enforce:
strict tenant isolation in:
signals;
playbooks;
decisions;
metrics accessible to tenant admins.
No cross-tenant learning or shared bandit state is allowed unless explicitly approved in a future design.

NFR-6 – Reliability & Resilience
MMM MUST:
continue operating in degraded mode when dependencies (UBI, ERIS, LLM Gateway, Data Governance) are temporarily unavailable.
fail safe, preferring “no intervention” to unsafe or ambiguous interventions.

NFR-7 – Security
All APIs MUST be authenticated via CCP-1 and authorised according to roles/scopes.
No PII or source code content should be logged in plain text; secrets must never be processed.

10. Data Model (Conceptual)
MMMContext
tenant_id
actor_id, actor_type (human/agent)
actor_roles
repo_id, branch, file_path (optional)
source_event (reference to input signal/event)
environment (dev/stage/prod)
time_bucket (e.g., day, hour)
policy_snapshot_id
recent_ubi_signals[]
recent_incidents[] / recent_ci_results[]

MMMPlaybook
playbook_id
tenant_id
version
name, description, owner
status (draft/published/deprecated)
triggers[] (event types, signal types, severities)
conditions[] (filters over MMMContext)
actions[] (Mirror/Mentor/Multiplier templates with surfaces)
limits (per-actor, per-repo, per-time window)
experiment_metadata (optional)

MMMDecision
decision_id
tenant_id
actor_id / actor_scope (team, repo)
context_ref (MMMContext id or embedded summary)
playbooks_fired[]
actions[] (MMMAction list)
created_at
policy_snapshot_id
safety_summary (LLM safety metadata if used)

MMMAction
action_id
decision_id
type (Mirror/Mentor/Multiplier)
surfaces[] (ide, ci, notification, etc.)
payload (immutable structured payload)
requires_consent (bool)
requires_dual_channel (bool)

MMMOutcome
outcome_id
decision_id, action_id
actor_id / actor_scope
result (shown, ignored, dismissed, accepted, failed)
reason (if dismissed/failed)
timestamps (shown_at, interacted_at, completed_at)

11. APIs & Integration Contracts (Logical)
All endpoints are logical contracts; concrete OpenAPI/JSON schemas must be defined under EPC-12.
11.1 Decision API (Synchronous)
POST /v1/mmm/decide
Request:
tenant_id (required)
actor_id, actor_type
context (subset of MMMContext fields)
source_event (event type, id)
Response:
decision_id
actions[] (MMMAction objects)
Used by Edge Agent and CI/PR integrations.

11.2 Playbook Management API
GET /v1/mmm/playbooks – list per tenant.
POST /v1/mmm/playbooks – create draft.
PUT /v1/mmm/playbooks/{playbook_id} – update.
POST /v1/mmm/playbooks/{playbook_id}/publish – change status to published.
All write operations MUST:
be authorised for admin roles only;
emit receipts via ERIS with playbook_id, version, prior vs new state.

11.3 Outcomes API
POST /v1/mmm/decisions/{decision_id}/outcomes
Request: MMMOutcome as defined above.
Used by Edge Agent/CI to report how the actor responded.
MMM persists outcomes and emits outcome receipts via ERIS.

11.4 Event Streams
mmm.decisions – produced whenever MMM makes a decision; consumed by Observability, Analytics, and optionally LLM Gateway for offline evaluation.
mmm.outcomes – produced when outcomes are recorded.
Schemas are defined in EPC-12 and MUST align with the data model.

12. Interactions with Other Modules
UBI (EPC-9) – source of BehaviouralSignals (input) and consumer of MMMOutcome aggregates (closing the loop).
Signal Ingestion & Normalization (PM-3) – provides canonical event envelopes.
Detection Engine Core (PM-4) – supplies risk alerts; uses MMM as one possible downstream consumer.
Alerting & Notification Service (EPC-4) – delivery channel for some actions.
LLM Gateway & Safety Enforcement (PM-6) – used to generate and vet Mentor/Multiplier content.
Evidence & Receipt Indexing Service (EPC-7) – sink for all DecisionReceipts and admin configuration receipts.
Policy & Config / Gold Standards (EPC-3/EPC-10) – provide policy constraints, thresholds, and priority rules.

13. Test Strategy & Representative Test Cases
13.1 Unit Tests
UT-MMM-01 – Playbook Matching Logic
Given different MMMContext + signals, ensure the correct playbooks fire or not.
UT-MMM-02 – Mirror/Mentor/Multiplier Action Composition
Verify action payloads match templates and respect type semantics (no prescriptive language in Mirror, consent flags for Multiplier).
UT-MMM-03 – Fatigue & Quiet Hours Logic
Ensure limits and quiet hours are correctly enforced per actor/tenant.
UT-MMM-04 – Policy & Safety Filters
Verify that actions violating policy or safety constraints are removed before response.
UT-MMM-05 – Receipt Composition
Validate that DecisionReceipts contain required identifiers and metadata, conforming to ERIS schema.

13.2 Integration Tests
IT-MMM-01 – UBI → MMM → IDE Flow
Simulate UBI emitting a BehaviouralSignal.
Call /v1/mmm/decide from Edge Agent with appropriate context.
Assert: actions returned, shown in IDE, outcome posted, receipts written.
IT-MMM-02 – Detection → MMM → Alerting Flow
Simulate a critical risk alert.
Assert: MMM emits high-priority Mirror+Mentor actions routed to Alerting & Notification, which delivers them using configured channels.
IT-MMM-03 – Mentor with LLM Safety
Trigger a Mentor playbook that uses LLM content.
Assert: MMM calls LLM Gateway & Safety; unsafe variants are filtered; only safe action payload is returned.
IT-MMM-04 – Multiplier with Consent & Policy
Trigger a Multiplier playbook.
Assert: MMM marks action as requires_consent; Edge Agent cannot execute without explicit consent; if policy forbids action, MMM refuses to propose it.

13.3 Performance & Scale Tests
PT-MMM-01 – Decision Throughput
Generate high volume of decision requests across tenants.
Assert: latency SLOs (NFR-1) are met; backlog control works.
PT-MMM-02 – Playbook Explosion
Test large number of playbooks per tenant.
Assert: playbook evaluation remains performant; no timeouts.

13.4 Privacy & Compliance Tests
PR-MMM-01 – Data Minimisation in Context
Assert: only necessary fields appear in internal context structures and logs; no extra PII is stored.
PR-MMM-02 – Retention & Deletion Behaviour
When Data Governance triggers deletion for an actor, verify their MMMContext and actor-level history are removed or anonymised as required.

13.5 Observability Tests
OB-MMM-01 – Telemetry Emission
Run representative flows; assert metrics for decisions, actions, outcomes, errors, and latency are exported, with traces linking the full decision path.

13.6 Security & Authorisation Tests
ST-MMM-01 – Admin Playbook Access
Assert that only authorised admin roles can create/update/publish playbooks.
ST-MMM-02 – Decision Endpoint Access
Assert that calls to /v1/mmm/decide require valid tenant/actor identity and scopes.

13.7 Fairness & Misuse-Prevention Tests
FM-MMM-01 – Disabled Action Types
If a tenant disables Multiplier actions, verify no such actions are proposed or delivered.
FM-MMM-02 – No Individual Performance Scoring
Assert: MMM decisions and receipts do not include individual productivity scores or rank-ordering, only contextual behavioural nudges aligned with policy.

13.8 Resilience & Fault-Tolerance Tests
RF-MMM-01 – LLM Gateway Unavailable
Simulate LLM Gateway outage; Mentor/Multiplier requiring LLM content must either fall back to Mirror-only or suppress actions with clear telemetry.
RF-MMM-02 – ERIS Unavailable
Simulate ERIS write failures; assert MMM handles them via retries/DLQ and does not block safe decision responses, while marking receipts as pending.
RF-MMM-03 – Policy Service Degradation
Simulate slow or failing Policy service; assert MMM fails safe (e.g., only Mirror actions or no actions) rather than ignoring policy.

14. Risks & Mitigations
Risk: Alert Fatigue
Mitigations: FR-7 (fatigue control), quiet hours, opt-out and snooze functions.
Risk: Manipulative or Coercive Nudges
Mitigations: FR-10 (non-coercion principles), explicit dismissal controls, audits via ERIS, adherence to digital nudging best practices.
Risk: Policy Bypass
Mitigations: FR-11 (policy integration), tests ensuring no MMM action is emitted without policy resolution; explicit degraded mode when policy is unavailable.
Risk: Misinterpretation by Management (as surveillance)
Mitigations: documentation emphasising coaching and system-level outcomes, no individual scoring; aggregated reports only.

15. Implementation Notes & Phasing (High-Level)
A realistic phased plan (to be elaborated in engineering planning):
Phase 1 – Skeleton & Contracts
Define schemas in EPC-12.
Implement /v1/mmm/decide with static playbooks and Mirror-only.
Wire ERIS receipts for decisions.
Phase 2 – Policy & UBI Integration
Integrate UBI signals and Policy/Config; implement FR-7 fully.
Phase 3 – Mentor (LLM) & Safety
Integrate LLM Gateway & Safety Enforcement; implement Mentor actions.
Phase 4 – Multiplier & Consent
Add Multiplier semantics, consent flows, and required CI/Edge hooks.
Phase 5 – Observability, Outcomes & Adaptation
Implement MMMOutcome handling, metrics, traces, and simple adaptation.

