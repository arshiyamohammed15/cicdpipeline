PM-1 – MMM Engine (Mirror-Mentor-Multiplier Engine)
Module Type: Platform Module
Surfaces: VS Code Extension (ZeroUI), Edge Agent, CI/PR checks, Alerting & Notification Service
Planes: CCP-1 (Identity & Trust), CCP-2 (Policy & Config), CCP-3 (Evidence & Audit), CCP-4 (Observability), CCP-6 (Data & Memory), CCP-7 (AI Lifecycle & Safety)

**Document Status**: Production-Ready PRD (v2.0)  
**Last Updated**: 2025-01-27  
**Implementation Status**: ~70% complete (core infrastructure done, production integrations pending)  
**Production Readiness**: Requires Phase 1-3 implementation (see Section 15)  
**Single Source of Truth**: This document is the authoritative specification for MMM Engine implementation.

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
Explicit triggers from Edge Agent/CI (e.g., "pre-commit evaluation").
All intakes MUST use the normalised envelope defined by PM-3 and the Contracts & Schema Registry (EPC-12), including tenant_id, actor_id, actor_type, source, event_type, ts, and a structured payload.

**Production Implementation Requirements**:
- PM-3 event stream integration: MUST support Kafka, RabbitMQ, and in-memory modes (for testing). Default to Kafka in production.
- Signal handler implementation: `_handle_ingested_signal()` MUST:
  1. Parse SignalEnvelope from PM-3 format.
  2. Convert to `MMMSignalInput` model.
  3. Trigger decision evaluation via `decide()` method with signal context.
  4. Handle errors gracefully (log, don't crash service).
- UBI signal integration: MUST subscribe to UBI event stream topic `ubi.behavioural_signals` and filter by tenant_id.
- Detection Engine integration: MUST subscribe to Detection Engine alerts topic `detection.alerts` and process high-severity alerts.
- Explicit trigger endpoint: POST `/v1/mmm/triggers/evaluate` for Edge Agent/CI to explicitly request decision evaluation with context.
- Signal validation: All signals MUST be validated against PM-3 schema before processing. Invalid signals MUST be logged and rejected.

FR-2 – Context Assembly
For each candidate MMM decision:
MMM MUST construct an MMMContext with:
actor details (from Identity & Trust Plane);
current repository/branch/file when available (from Edge Agent);
recent UBI signals;
relevant infra state (e.g., active incidents from Health & Reliability Monitoring);
tenant MMM configuration and policies.
The context MUST be computed with data minimisation, including only what is necessary for the decision, in line with privacy frameworks that emphasise collecting and processing the minimum data required for the specified purpose.

**Production Implementation Requirements**:
- IAM integration: MUST use real IAM client (not mock) calling IAM `/v1/iam/decision` endpoint to resolve actor roles, capabilities, and permissions. Timeout: 2.0s, circuit breaker pattern.
- UBI signal retrieval: MUST use real UBI client (not mock) calling UBI `/v1/ubi/signals/recent` endpoint with `tenant_id`, `actor_id`, `limit=10` to fetch recent BehaviouralSignals. Timeout: 1.0s.
- Data Governance integration: MUST use real Data Governance client (not mock) calling Data Governance `/v1/data-governance/tenants/{tenant_id}/config` to fetch tenant privacy config (quiet hours, retention policies). Timeout: 0.5s.
- Health & Reliability Monitoring integration: MUST query Health Monitoring service for active incidents affecting the tenant/repo. Optional integration, fail gracefully if unavailable.
- Data minimisation validation: Context builder MUST validate that only necessary fields are included. No PII beyond actor_id, no source code content, no secrets.
- Context caching: Recent contexts MAY be cached (TTL 30s) to reduce service calls, but MUST respect data freshness requirements.

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

**Production Implementation Requirements**:
- LLM Gateway integration: MUST use real HTTP client (not mock) calling LLM Gateway `/v1/llm/generate` endpoint with:
  - `prompt`: Generated from playbook template with context variables.
  - `tenant_id`, `actor_id`, `actor_type`: For policy and safety evaluation.
  - `operation_type`: "chat" or "completion".
  - `system_prompt_id`: From tenant policy.
  - `dry_run`: false for production.
- Safety enforcement: LLM Gateway response MUST include `safety` object with `status` (pass/fail/warn), `risk_flags` array, `redaction_summary`. If `status == "fail"`, Mentor action MUST be suppressed or fallback to Mirror action.
- Rationale linking: Mentor action payload MUST include `rationale` field with:
  - `evidence_links`: Array of signal IDs, baseline deviation IDs, or incident IDs that triggered this action.
  - `baseline_comparison`: Description of how current state deviates from expected baseline.
  - `why_relevant`: Explanation of why this action addresses the detected issue.
- Fallback behavior: If LLM Gateway unavailable or safety check fails, fallback to static Mentor template from playbook (no LLM content) or suppress action entirely if no template exists.
- Async LLM calls: LLM Gateway calls MUST be async (not blocking) with timeout (default 3.0s) and circuit breaker pattern.

FR-6 – Multiplier Actions
A Multiplier action attempts to automate a safe change:
Examples:
Prepare a patch for adding missing tests.
Generate a draft rollback PR.
Multiplier actions MUST:
require explicit actor consent in the IDE/CI surface before execution;
be gated by policy and potentially dual-channel confirmation for sensitive operations (e.g., production rollback).
MMM orchestrates Multiplier actions but does not directly mutate code or infra; execution is delegated to Edge Agent/CI workflows that are subject to existing safety and approval flows.

**Production Implementation Requirements**:
- Dual-channel confirmation logic: When `requires_dual_channel=True`, MMM MUST:
  1. Mark action with `dual_channel_required=True` flag in payload.
  2. Require explicit approval from both: (a) actor who triggered the action, and (b) designated approver (from policy or tenant admin).
  3. Store dual-channel approval state in database table `mmm_dual_channel_approvals` with fields: `approval_id`, `action_id`, `decision_id`, `actor_id`, `approver_id`, `first_approval_at`, `second_approval_at`, `status` (pending/first_approved/fully_approved/rejected).
  4. Only after both approvals, allow Edge Agent/CI to execute the action.
- Consent enforcement: Edge Agent/CI MUST check `requires_consent` flag and MUST NOT execute without explicit user consent UI interaction (button click, checkbox confirmation).
- Policy gating: Multiplier actions MUST be filtered if tenant policy disallows auto-generated patches, production changes, or specific action types.
- Execution delegation: MMM returns action with execution metadata; Edge Agent/CI workflows handle actual code/infra mutations with their own safety gates.

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

**Production Implementation Requirements**:
- Policy service integration: MUST use real Policy & Config client (not mock) calling Policy service `/v1/policy/tenants/{tenant_id}/evaluate` or `/v1/standards` endpoint to fetch policy snapshot. Timeout: 0.5s, latency budget: 500ms.
- Policy caching: Policy snapshots MUST be cached in-memory with TTL 60s and push invalidation support via webhook or message bus.
- Gold Standards integration: MUST query Gold Standards service (EPC-10) for module/repo-specific rules. If Gold Standards unavailable, fail-safe: only allow Mirror actions.
- Policy unavailable handling: If Policy service unavailable:
  - For safety-critical tenants (per tenant config): Fail-closed, return no actions.
  - For other tenants: Use last valid cached snapshot (max 5 minutes stale), mark decision with `policy_stale=true` flag, log warning.
  - After 5 minutes stale or hard failure: Reject requests with `POLICY_UNAVAILABLE` error, emit receipt with failure reason.
- Policy evaluation: Policy result MUST include: `allowed` (boolean), `policy_snapshot_id`, `policy_version_ids`, `restrictions` (array of disallowed action types), `override_windows` (if any).
- Action filtering: Actions MUST be filtered if policy `allowed == false` or if action type is in `restrictions` array.

FR-12 – Receipts & Governance Integration
For each MMMDecision and relevant MMMOutcome:
MMM MUST emit DecisionReceipts via ERIS that include:
tenant_id, actor_id/actor_scope, signal_ids, playbook_id/version;
proposed actions (type, surfaces);
policy snapshot identifiers;
whether content passed LLM safety (if applicable);
final outcome (shown/ignored/accepted/failed).
Receipts MUST conform to the ERIS schema and be written only through the Evidence & Audit Plane, not an ad-hoc local audit log.

**Production Implementation Requirements**:
- Decision receipts MUST be emitted synchronously in the `decide()` method immediately after decision creation, before returning response to caller.
- Outcome receipts MUST be emitted asynchronously via circuit breaker pattern to avoid blocking outcome recording.
- ERIS client MUST use real HTTP client (not mock) with timeout (default 2.0s), retry logic (3 attempts with exponential backoff), and circuit breaker for resilience.
- Receipt emission failures MUST be logged but MUST NOT block decision responses (best-effort auditability).
- Receipt payload MUST include all ERIS schema fields: receipt_id, gate_id="mmm", schema_version, policy_version_ids, snapshot_hash, timestamp_utc, timestamp_monotonic_ms, evaluation_point, inputs, decision_status, decision_rationale, decision_badges, result, actor_repo_id, actor_machine_fingerprint, actor_type, evidence_handles, degraded flag, signature.
- Receipts MUST be signed using Ed25519 per ERIS requirements.

FR-13 – Admin & Configuration Interfaces
MMM MUST expose admin interfaces (via APIs, not UI dashboards) for:
Managing playbooks (create/update/deprecate/publish).
Setting tenant MMM policies (enabled surfaces, quotas, quiet hours).
Defining experiments (treatments vs control) within safe bounds.
Viewing summary metrics (for admin personas) without exposing actor-level sensitive history.
All admin mutations MUST be authenticated, authorised, and receipt-logged.

**Production Implementation Requirements**:
- Playbook CRUD endpoints: GET `/v1/mmm/playbooks`, POST `/v1/mmm/playbooks`, PUT `/v1/mmm/playbooks/{playbook_id}`, POST `/v1/mmm/playbooks/{playbook_id}/publish`, DELETE `/v1/mmm/playbooks/{playbook_id}` (soft delete to deprecated status).
- Tenant MMM policy configuration endpoint: PUT `/v1/mmm/tenants/{tenant_id}/policy` with payload: `{enabled_surfaces: ["ide", "ci", "alert"], quotas: {max_actions_per_day: 10, max_actions_per_hour: 3}, quiet_hours: {start: 22, end: 6}, enabled_action_types: ["mirror", "mentor", "multiplier"]}`.
- Experiment management endpoints: GET `/v1/mmm/experiments`, POST `/v1/mmm/experiments`, PUT `/v1/mmm/experiments/{experiment_id}`, POST `/v1/mmm/experiments/{experiment_id}/activate`, POST `/v1/mmm/experiments/{experiment_id}/deactivate`.
- Summary metrics endpoint: GET `/v1/mmm/tenants/{tenant_id}/metrics` returning aggregate counts (decisions, actions, outcomes) without actor-level detail.
- All admin endpoints MUST require IAM authorization with admin role (tenant_admin or mmm_admin).
- All mutations MUST emit admin configuration receipts via ERIS with before/after state.

FR-14 – Actor Controls & Preferences
MMM MUST:
honour per-actor preferences:
opt-out from certain categories (e.g., Multiplier actions);
snooze MMM for a period;
change preferred surfaces (IDE vs CI only).
expose these controls via Edge Agent APIs so the ZeroUI extension can provide a simple settings panel linked into the Policy/Config plane.

**Production Implementation Requirements**:
- Actor preferences storage: Database table `mmm_actor_preferences` with fields: `preference_id`, `tenant_id`, `actor_id`, `opt_out_categories` (JSON array: ["multiplier", "mentor"]), `snooze_until` (TIMESTAMPTZ), `preferred_surfaces` (JSON array: ["ide", "ci"]), `created_at`, `updated_at`.
- Preference API endpoints: GET `/v1/mmm/actors/{actor_id}/preferences`, PUT `/v1/mmm/actors/{actor_id}/preferences`, POST `/v1/mmm/actors/{actor_id}/preferences/snooze` (with `duration_hours` or `until` timestamp).
- Preference enforcement: In `decide()` method, filter actions based on actor preferences:
  - If actor opted out of action type, exclude those actions.
  - If actor snoozed, return empty actions list.
  - If actor has preferred surfaces, filter actions to only those surfaces.
- Preference defaults: If no preferences exist, all action types and surfaces are allowed.
- Preference inheritance: Actor preferences override tenant policy but MUST NOT override Gold Standards or safety constraints.
- Edge Agent integration: Edge Agent MUST expose preferences API at `/api/v1/mmm/preferences` that proxies to MMM Engine.

FR-15 – Observability & Debuggability
MMM MUST be fully observable:
Metrics for:
signals received; decisions made; actions proposed; actions delivered; actions accepted; actions resulting in positive outcomes.
Traces for:
signal → context → playbook → LLM safety → policy gate → surfaces.
Logs for:
failures, degraded modes, policy conflicts, ERIS write failures.
All observability data MUST respect privacy and redaction rules (no sensitive payloads in logs).

**Production Implementation Requirements**:
- Prometheus metrics: `mmm_signals_received_total{tenant_id, source, event_type}`, `mmm_decisions_total{tenant_id, actor_type}`, `mmm_actions_total{tenant_id, action_type}`, `mmm_actions_delivered_total{tenant_id, surface, result}`, `mmm_actions_accepted_total{tenant_id, action_type}`, `mmm_decision_latency_seconds{tenant_id, p50/p95/p99}`, `mmm_circuit_breaker_state{service_name, state}`, `mmm_eris_receipt_emission_total{tenant_id, result}`.
- Distributed tracing: OpenTelemetry spans MUST be created for each decision flow with parent span linking signal → context → playbook → LLM safety → policy gate → delivery. Spans MUST include: `tenant_id`, `actor_id`, `decision_id`, `playbook_ids`, `action_count`, `latency_ms`, `degraded_mode` flag.
- Structured logging: JSON logs with fields: `timestamp`, `level`, `tenant_id`, `actor_id`, `decision_id`, `event_type`, `message`, `error` (if applicable), `degraded_mode`. NO PII, secrets, or raw action payloads in logs.
- Privacy redaction: Before logging, redact sensitive fields using Data Governance redaction service. Log only action type, surface, and metadata, not full payloads.
- Log retention: Logs MUST respect Data Governance retention policies (default 30 days, configurable per tenant).

9. Non-Functional Requirements (NFR)
NFR-1 – Latency
For synchronous IDE/Edge calls to /v1/mmm/decide, MMM SHOULD respond within 150 ms p95 under normal load.
For CI/PR decisions, MMM SHOULD respond within 500 ms p95.
When these targets cannot be met, MMM MUST degrade gracefully (e.g., no nudges rather than partial/incorrect ones).

**Production Implementation Requirements**:
- Latency monitoring: Track decision latency via Prometheus histogram `mmm_decision_latency_seconds` with buckets [0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0] seconds.
- Latency SLO enforcement: If decision latency exceeds 150ms (IDE) or 500ms (CI), log warning and emit telemetry. Do not fail the request, but mark decision with `latency_warning=true`.
- Timeout management: All external service calls MUST have timeouts:
  - IAM: 2.0s
  - Policy: 0.5s
  - UBI: 1.0s
  - Data Governance: 0.5s
  - LLM Gateway: 3.0s
  - ERIS: 2.0s
- Parallel service calls: Where possible, make service calls in parallel (IAM + Policy + UBI) to reduce total latency.
- Database query optimization: Playbook queries MUST use indexes on `tenant_id`, `status`. Decision queries MUST use indexes on `tenant_id`, `created_at`.
- Caching strategy: Policy snapshots cached (60s TTL), recent UBI signals cached (30s TTL), actor preferences cached (5min TTL).
- Graceful degradation: If latency budget exceeded, return cached decisions or empty actions list rather than blocking or timing out.

NFR-2 – Scalability
MMM MUST handle:
At least N decisions per minute per tenant (final value set by infra PRD).
Horizontal scaling via stateless workers, backed by a shared store for playbooks and state.

**Production Implementation Requirements**:
- Stateless service design: MMM service MUST be stateless (no in-memory state between requests). All state stored in database.
- Fatigue manager state: `FatigueManager` in-memory state MUST be moved to shared cache (Redis) with TTL-based expiration for horizontal scaling. Key format: `mmm:fatigue:{tenant_id}:{actor_id}:{action_type}` with TTL 24 hours.
- Database connection pooling: Use connection pool (min 5, max 20 connections) for database access.
- Horizontal scaling: Service MUST support multiple instances behind load balancer. Use database for shared state, Redis for fatigue tracking.
- Load testing: MUST be load tested to handle at least 1000 decisions/minute per tenant, 10,000 decisions/minute total across all tenants.
- Rate limiting: Implement per-tenant rate limiting at API gateway level (not in MMM service) to prevent abuse.
- Database sharding: For very large scale, playbooks and decisions MAY be sharded by tenant_id.

NFR-3 – Privacy & Data Minimisation
MMM MUST:
only process data necessary for decisions, in line with privacy frameworks that emphasise minimising data collection and limiting use to specified purposes.
respect Data Governance rules for:
retention;
residency;
deletion of actor-level history when requested by upstream policies.

**Production Implementation Requirements**:
- Data minimisation validation: Context builder MUST validate that only necessary fields are included. Validation rules:
  - Actor context: Only `actor_id`, `actor_type`, `actor_roles` (no PII, no email, no name).
  - Repository context: Only `repo_id`, `branch`, `file_path` (no source code content).
  - Signal context: Only signal metadata (signal_id, event_type, severity) not full payloads.
- Retention policy enforcement: Decisions and outcomes MUST be automatically deleted per Data Governance retention rules:
  - Default retention: 90 days for decisions, 365 days for outcomes (configurable per tenant).
  - Background job: Daily cleanup job deletes records older than retention period.
  - Legal hold: Records with `legal_hold=true` MUST NOT be deleted regardless of retention period.
- Actor-level deletion: When Data Governance triggers actor deletion request:
  1. Delete all actor preferences for that actor.
  2. Anonymize decisions: Set `actor_id` to `deleted-{hash}`, remove actor-specific metadata.
  3. Anonymize outcomes: Set `actor_id` to `deleted-{hash}`.
  4. Log deletion event via ERIS receipt.
- Data residency: All data MUST be stored in tenant-configured region per Data Governance rules. Database connections MUST use region-specific endpoints.
- Privacy by design: No PII, secrets, or source code content in logs, metrics, or traces. Use redaction service before logging.

NFR-4 – Trustworthy AI & Risk Management
MMM MUST align with the NIST AI RMF characteristics of trustworthy AI (validity, reliability, security, explainability, privacy, fairness, accountability) as applied to AI-driven decisions.
Any LLM-driven Mentor/Multiplier content MUST pass through the LLM Gateway & Safety module, which enforces content and safety policies.

**Production Implementation Requirements**:
- LLM Gateway integration: MUST use real LLM Gateway client (not mock) with full safety pipeline:
  - Input validation: Prompt injection detection, PII detection, content filtering.
  - Output validation: Harmful content detection, bias detection, accuracy validation.
  - Safety metadata: Response MUST include `safety.status`, `safety.risk_flags`, `safety.redaction_summary`.
- NIST AI RMF compliance:
  - **Validity**: Actions MUST be based on valid signals and context. Invalid inputs rejected.
  - **Reliability**: Service MUST operate consistently with circuit breakers and degraded modes.
  - **Security**: All APIs authenticated, data encrypted in transit and at rest.
  - **Explainability**: Receipts MUST include decision rationale, playbook IDs, policy snapshot IDs.
  - **Privacy**: Data minimisation, retention policies, actor deletion support.
  - **Fairness**: No individual performance scoring, no protected attribute discrimination.
  - **Accountability**: All decisions and outcomes recorded in receipts, audit trail via ERIS.
- Safety enforcement: If LLM Gateway safety check fails (`safety.status == "fail"`), action MUST be suppressed. If `safety.status == "warn"`, action MAY proceed with warning flag in receipt.
- Risk assessment: Each decision MUST include risk assessment in receipt: `risk_score` (0.0-1.0), `risk_flags` array, `safety_checks_passed` boolean.

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
fail safe, preferring "no intervention" to unsafe or ambiguous interventions.

**Production Implementation Requirements**:
- Degraded mode logic: When dependencies unavailable, MMM MUST:
  1. **LLM Gateway unavailable**: Suppress Mentor/Multiplier actions requiring LLM content, allow Mirror-only actions. Log degraded mode, emit telemetry.
  2. **ERIS unavailable**: Continue decision flow, queue receipts in local buffer (max 1000), retry via background worker. Mark receipts as `pending` in decision metadata.
  3. **Policy service unavailable**: Per FR-11, fail-closed for safety-critical tenants, use cached snapshot for others (max 5min stale).
  4. **UBI unavailable**: Use empty recent_signals array, continue with available context. Log warning.
  5. **Data Governance unavailable**: Use default quiet hours (22:00-06:00), continue with minimal privacy config. Log warning.
  6. **IAM unavailable**: Reject requests with 503 Service Unavailable (cannot authenticate without IAM).
- Circuit breakers: All external service clients MUST use circuit breaker pattern:
  - Failure threshold: 5 consecutive failures.
  - Recovery timeout: 60 seconds.
  - Half-open state: Allow 1 test request before fully opening.
  - State metrics: Expose circuit breaker state via Prometheus metrics.
- Fail-safe behavior: When in degraded mode or policy unavailable:
  - Prefer returning empty actions list over unsafe actions.
  - Never bypass safety checks even in degraded mode.
  - Log all degraded mode decisions with `degraded_mode=true` flag in receipts.
- Retry logic: For non-critical operations (ERIS receipts, telemetry), use exponential backoff retry (3 attempts: 0.5s, 1.0s, 2.0s).
- Health checks: `/v1/mmm/health` MUST return 200 if service is operational, 503 if critical dependencies unavailable. `/v1/mmm/ready` MUST return 200 only if all required dependencies are available.

NFR-7 – Security
All APIs MUST be authenticated via CCP-1 and authorised according to roles/scopes.
No PII or source code content should be logged in plain text; secrets must never be processed.

**Production Implementation Requirements**:
- IAM authentication: MUST use real IAM client (not mock) for all API requests:
  - Middleware: `IAMAuthMiddleware` validates JWT token via IAM `/v1/iam/verify` endpoint.
  - Token extraction: From `Authorization: Bearer <token>` header.
  - Tenant context: Extracted from token claims (`tenant_id` field).
  - Public paths: `/health`, `/ready`, `/metrics` excluded from auth (read-only).
- Role-based authorization: Admin endpoints (playbook CRUD, tenant policy config) MUST require `mmm_admin` or `tenant_admin` role. Decision endpoints require `mmm.decide` scope.
- PII redaction: Before logging, all log messages MUST be redacted using Data Governance redaction service:
  - Redact: actor_id (hash only), email addresses, names, source code snippets.
  - Log only: action types, surface types, decision IDs, playbook IDs (no sensitive content).
- Secret detection: Input validation MUST detect and reject requests containing secrets (API keys, passwords, tokens). Use Data Governance secret detection service.
- Encryption: All data in transit MUST use TLS 1.3. All data at rest MUST be encrypted (database encryption, file system encryption).
- Security headers: All HTTP responses MUST include security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000`.
- Audit logging: All admin mutations (playbook create/update/publish, tenant policy config) MUST be logged to security audit log with: timestamp, admin_user_id, action, resource_id, before/after state (redacted).

10. Data Model (Conceptual & Database Schema)

10.1 Conceptual Data Models

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
quiet_hours (from Data Governance config)

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

11. APIs & Integration Contracts (Production)

All endpoints are logical contracts; concrete OpenAPI/JSON schemas must be defined under EPC-12 (see `contracts/mmm_engine/openapi/openapi_mmm_engine.yaml`).

11.1 Decision API (Synchronous)
POST /v1/mmm/decide
**Authentication**: Required (IAM JWT token)
**Authorization**: Requires `mmm.decide` scope
**Request**:
```json
{
  "tenant_id": "string (required)",
  "actor_id": "string (optional)",
  "actor_type": "human|ai_agent (optional, default: human)",
  "context": {
    "repo_id": "string (optional)",
    "branch": "string (optional)",
    "file_path": "string (optional)",
    "roles": ["string"] (optional)
  },
  "signal": {
    "signal_id": "string (optional)",
    "source": "string (optional)",
    "event_type": "string (optional)",
    "severity": "string (optional)"
  }
}
```
**Response**:
```json
{
  "decision": {
    "decision_id": "uuid",
    "tenant_id": "string",
    "actor_id": "string",
    "actor_type": "human|ai_agent",
    "actions": [
      {
        "action_id": "uuid",
        "type": "mirror|mentor|multiplier",
        "surfaces": ["ide", "ci", "alert"],
        "payload": {
          "title": "string",
          "body": "string",
          "rationale": "string (for Mentor/Multiplier)",
          "evidence_links": ["string"]
        },
        "requires_consent": "boolean",
        "requires_dual_channel": "boolean"
      }
    ],
    "created_at": "iso8601",
    "policy_snapshot_id": "string",
    "degraded_mode": "boolean (if true, some dependencies unavailable)"
  }
}
```
**Latency SLO**: 150ms p95 (IDE), 500ms p95 (CI)
**Used by**: Edge Agent and CI/PR integrations.

11.2 Playbook Management API
GET /v1/mmm/playbooks
- **Authentication**: Required
- **Authorization**: Requires `mmm.read` scope
- **Query params**: `status` (optional: draft/published/deprecated)
- **Response**: Array of Playbook objects

POST /v1/mmm/playbooks
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Request**: PlaybookCreateRequest (name, version, triggers, conditions, actions, limits)
- **Response**: Playbook object (status: draft)
- **Receipt**: Emits admin config receipt via ERIS

PUT /v1/mmm/playbooks/{playbook_id}
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Request**: PlaybookUpdateRequest (same as create, all fields optional)
- **Response**: Playbook object
- **Receipt**: Emits admin config receipt via ERIS with before/after state

POST /v1/mmm/playbooks/{playbook_id}/publish
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Response**: Playbook object (status: published)
- **Receipt**: Emits admin config receipt via ERIS

DELETE /v1/mmm/playbooks/{playbook_id}
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Action**: Soft delete (sets status to deprecated)
- **Response**: 204 No Content
- **Receipt**: Emits admin config receipt via ERIS

11.3 Outcomes API
POST /v1/mmm/decisions/{decision_id}/outcomes
- **Authentication**: Required
- **Authorization**: Requires `mmm.outcome` scope
- **Request**:
```json
{
  "action_id": "uuid (required)",
  "result": "shown|ignored|dismissed|accepted|failed (required)",
  "reason": "string (optional, required if dismissed/failed)",
  "actor_id": "string (optional, defaults to authenticated actor)"
}
```
- **Response**: 202 Accepted
- **Used by**: Edge Agent/CI to report how the actor responded
- **Receipt**: MMM persists outcomes and emits outcome receipts via ERIS (async, non-blocking)

11.4 Actor Preferences API (NEW - FR-14)
GET /v1/mmm/actors/{actor_id}/preferences
- **Authentication**: Required
- **Authorization**: Actor can view own preferences, admin can view any
- **Response**: ActorPreferences object

PUT /v1/mmm/actors/{actor_id}/preferences
- **Authentication**: Required
- **Authorization**: Actor can update own preferences, admin can update any
- **Request**:
```json
{
  "opt_out_categories": ["multiplier", "mentor"],
  "preferred_surfaces": ["ide", "ci"],
  "snooze_until": "iso8601 (optional)"
}
```
- **Response**: ActorPreferences object

POST /v1/mmm/actors/{actor_id}/preferences/snooze
- **Authentication**: Required
- **Authorization**: Actor can snooze own, admin can snooze any
- **Request**:
```json
{
  "duration_hours": "integer (optional)",
  "until": "iso8601 (optional, one of duration_hours or until required)"
}
```
- **Response**: ActorPreferences object

11.5 Tenant Policy Configuration API (NEW - FR-13)
GET /v1/mmm/tenants/{tenant_id}/policy
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Response**: TenantMMMPolicy object

PUT /v1/mmm/tenants/{tenant_id}/policy
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Request**:
```json
{
  "enabled_surfaces": ["ide", "ci", "alert"],
  "quotas": {
    "max_actions_per_day": 10,
    "max_actions_per_hour": 3
  },
  "quiet_hours": {
    "start": 22,
    "end": 6
  },
  "enabled_action_types": ["mirror", "mentor", "multiplier"]
}
```
- **Response**: TenantMMMPolicy object
- **Receipt**: Emits admin config receipt via ERIS

11.6 Experiment Management API (NEW - FR-13)
GET /v1/mmm/experiments
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Query params**: `tenant_id` (required), `status` (optional)
- **Response**: Array of Experiment objects

POST /v1/mmm/experiments
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Request**: ExperimentCreateRequest
- **Response**: Experiment object

PUT /v1/mmm/experiments/{experiment_id}
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Request**: ExperimentUpdateRequest
- **Response**: Experiment object

POST /v1/mmm/experiments/{experiment_id}/activate
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Response**: Experiment object (status: active)

POST /v1/mmm/experiments/{experiment_id}/deactivate
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Response**: Experiment object (status: inactive)

11.7 Summary Metrics API (NEW - FR-13)
GET /v1/mmm/tenants/{tenant_id}/metrics
- **Authentication**: Required
- **Authorization**: Requires `mmm_admin` or `tenant_admin` role
- **Query params**: `start_date` (optional, iso8601), `end_date` (optional, iso8601)
- **Response**:
```json
{
  "tenant_id": "string",
  "period": {
    "start": "iso8601",
    "end": "iso8601"
  },
  "aggregates": {
    "decisions_total": "integer",
    "actions_total": "integer",
    "actions_by_type": {
      "mirror": "integer",
      "mentor": "integer",
      "multiplier": "integer"
    },
    "outcomes_total": "integer",
    "outcomes_by_result": {
      "accepted": "integer",
      "ignored": "integer",
      "dismissed": "integer"
    }
  }
}
```
- **Privacy**: No actor-level detail, only aggregate counts

11.8 Health & Readiness Endpoints
GET /v1/mmm/health
- **Authentication**: Not required (public)
- **Response**: `{"status": "healthy"}` (200) or `{"status": "unhealthy"}` (503)
- **Purpose**: Basic liveness check

GET /v1/mmm/ready
- **Authentication**: Not required (public)
- **Response**: `{"status": "ready"}` (200) if all required dependencies available, `{"status": "not_ready"}` (503) otherwise
- **Purpose**: Readiness check for Kubernetes/load balancer

GET /v1/mmm/metrics
- **Authentication**: Not required (public, but may be restricted in production)
- **Response**: Prometheus metrics format (text/plain)
- **Purpose**: Metrics scraping endpoint

11.9 Event Streams
**Kafka Topics**:
- `mmm.decisions` – produced whenever MMM makes a decision; consumed by Observability, Analytics, and optionally LLM Gateway for offline evaluation.
- `mmm.outcomes` – produced when outcomes are recorded.
- `mmm.admin_config` – produced when admin configurations change (playbooks, tenant policies, experiments).

**Schemas**: Defined in EPC-12 and MUST align with the data model. All events MUST include: `event_id`, `tenant_id`, `timestamp_utc`, `event_type`, `payload` (JSONB).

12. Interactions with Other Modules

**Production Integration Patterns**:

12.1 UBI (EPC-9)
- **Role**: Source of BehaviouralSignals (input) and consumer of MMMOutcome aggregates (closing the loop).
- **Integration**: HTTP client calling UBI `/v1/ubi/signals/recent` endpoint. Timeout: 1.0s. Circuit breaker pattern.
- **Event Stream**: Subscribe to Kafka topic `ubi.behavioural_signals` for real-time signals.
- **Data Flow**: UBI → MMM (signals) → MMM → UBI (outcome aggregates for learning).

12.2 Signal Ingestion & Normalization (PM-3)
- **Role**: Provides canonical event envelopes.
- **Integration**: Kafka/RabbitMQ consumer subscribing to PM-3 normalized event stream. Topic: `pm3.signals.normalized`. Group ID: `mmm-engine`.
- **Data Flow**: PM-3 → MMM (normalized signals) → MMM decision.

12.3 Detection Engine Core (PM-4)
- **Role**: Supplies risk alerts; uses MMM as one possible downstream consumer.
- **Integration**: Subscribe to Detection Engine alerts topic `detection.alerts`. Filter high-severity alerts only.
- **Data Flow**: Detection Engine → MMM (risk alerts) → MMM decision → Alerting Service.

12.4 Alerting & Notification Service (EPC-4)
- **Role**: Delivery channel for some actions.
- **Integration**: HTTP client calling Alerting `/api/v1/notifications/mmm` endpoint. Timeout: 2.0s. Retry: 3 attempts.
- **Data Flow**: MMM → Alerting Service (high-priority actions) → Notification channels (email, Slack, etc.).

12.5 LLM Gateway & Safety Enforcement (PM-6)
- **Role**: Used to generate and vet Mentor/Multiplier content.
- **Integration**: HTTP client calling LLM Gateway `/v1/llm/generate` endpoint. Timeout: 3.0s. Circuit breaker pattern.
- **Safety Pipeline**: All LLM-generated content MUST pass through LLM Gateway safety pipeline (prompt injection, PII detection, content filtering).
- **Data Flow**: MMM → LLM Gateway (prompt) → LLM Gateway (safe content) → MMM (Mentor/Multiplier action).

12.6 Evidence & Receipt Indexing Service (EPC-7)
- **Role**: Sink for all DecisionReceipts and admin configuration receipts.
- **Integration**: HTTP client calling ERIS `/v1/evidence/receipts` endpoint. Timeout: 2.0s. Retry: 3 attempts with exponential backoff. Circuit breaker pattern.
- **Receipt Format**: MUST conform to ERIS schema. Signed with Ed25519.
- **Data Flow**: MMM → ERIS (decision receipts, outcome receipts, admin config receipts) → ERIS indexing → Audit queries.

12.7 Policy & Config / Gold Standards (EPC-3/EPC-10)
- **Role**: Provide policy constraints, thresholds, and priority rules.
- **Integration**: HTTP client calling Policy service `/v1/policy/tenants/{tenant_id}/evaluate` or `/v1/standards` endpoint. Timeout: 0.5s. Latency budget: 500ms. Caching: 60s TTL with push invalidation.
- **Gold Standards**: Query Gold Standards service for module/repo-specific rules. Fail-safe if unavailable.
- **Data Flow**: MMM → Policy Service (policy evaluation) → MMM (policy result) → Action filtering.

12.8 Identity & Access Management (EPC-1)
- **Role**: Authentication and authorization for all API requests.
- **Integration**: HTTP client calling IAM `/v1/iam/verify` and `/v1/iam/decision` endpoints. Timeout: 2.0s. Circuit breaker pattern.
- **Middleware**: `IAMAuthMiddleware` validates JWT tokens and extracts tenant context.
- **Data Flow**: Client → IAM (token validation) → MMM (authenticated request) → IAM (authorization check) → MMM (authorized action).

12.9 Data Governance & Privacy (EPC-2)
- **Role**: Privacy configuration, data minimisation, retention policies.
- **Integration**: HTTP client calling Data Governance `/v1/data-governance/tenants/{tenant_id}/config` endpoint. Timeout: 0.5s.
- **Redaction**: Use Data Governance redaction service for log sanitization.
- **Data Flow**: MMM → Data Governance (tenant config) → MMM (privacy settings) → Data Governance (redaction) → MMM (sanitized logs).

**Integration Failure Handling**:
- All integrations MUST use circuit breaker pattern (failure threshold: 5, recovery timeout: 60s).
- All integrations MUST have timeouts to prevent blocking.
- All integrations MUST have retry logic for transient failures (non-critical operations).
- All integrations MUST degrade gracefully (see NFR-6 for degraded mode behavior).

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

15. Service Client Implementation Patterns (Production)

All service clients MUST follow these patterns for production readiness:

15.1 HTTP Client Pattern
- Use `httpx` library for HTTP clients (async or sync as appropriate).
- Base URL from environment variable with fallback to localhost for development.
- Timeout configuration per service (see timeouts in Section 12).
- Retry logic for transient failures (3 attempts, exponential backoff: 0.5s, 1.0s, 2.0s).
- Circuit breaker pattern (failure threshold: 5, recovery timeout: 60s).
- Error handling: Catch `httpx.HTTPStatusError` and `httpx.RequestError`, convert to appropriate exceptions.

15.2 IAM Client Implementation
```python
class IAMClient:
    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 2.0):
        self.base_url = base_url or os.getenv("IAM_SERVICE_URL", "http://localhost:8001/iam/v1")
        self.timeout = timeout_seconds
        self._breaker = CircuitBreaker("iam", failure_threshold=5, recovery_timeout=60.0)
    
    def verify_token(self, token: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        # Call IAM /v1/iam/verify endpoint
        # Return (success, claims, error_message)
    
    def validate_actor(self, actor: Actor, scope: str) -> None:
        # Call IAM /v1/iam/decision endpoint
        # Raise HTTPException if denied
```

15.3 ERIS Client Implementation
```python
class ERISClient:
    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 2.0):
        self.base_url = base_url or os.getenv("ERIS_SERVICE_URL", "http://localhost:8007")
        self.timeout = timeout_seconds
        self._breaker = CircuitBreaker("eris", failure_threshold=5, recovery_timeout=60.0)
    
    async def emit_receipt(self, receipt: Dict[str, Any]) -> Optional[str]:
        # Call ERIS /v1/evidence/receipts endpoint
        # Retry on failure (3 attempts)
        # Return receipt_id or None if failed (non-blocking)
```

15.4 LLM Gateway Client Implementation
```python
class LLMGatewayClient:
    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 3.0):
        self.base_url = base_url or os.getenv("LLM_GATEWAY_SERVICE_URL", "http://localhost:8006")
        self.timeout = timeout_seconds
        self._breaker = CircuitBreaker("llm_gateway", failure_threshold=5, recovery_timeout=60.0)
    
    async def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Call LLM Gateway /v1/llm/generate endpoint
        # Return response with content and safety metadata
        # Raise exception if safety check fails
```

15.5 Policy Client Implementation
```python
class PolicyClient:
    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 0.5):
        self.base_url = base_url or os.getenv("POLICY_SERVICE_URL", "http://localhost:8003")
        self.timeout = timeout_seconds
        self._cache = PolicyCache(ttl_seconds=60)
        self._breaker = CircuitBreaker("policy", failure_threshold=5, recovery_timeout=60.0)
    
    def evaluate(self, tenant_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Check cache first
        # Call Policy /v1/policy/tenants/{tenant_id}/evaluate endpoint
        # Return policy result with allowed flag and snapshot_id
        # Handle unavailable: fail-closed for safety-critical, cached for others
```

15.6 Circuit Breaker Pattern
All service clients MUST use circuit breaker pattern:
- **States**: Closed (normal), Open (failing), Half-Open (testing recovery)
- **Failure threshold**: 5 consecutive failures → Open state
- **Recovery timeout**: 60 seconds → Half-Open state
- **Half-open logic**: Allow 1 test request, if success → Closed, if failure → Open
- **Metrics**: Expose circuit breaker state via Prometheus gauge metric

16. Implementation Notes & Phasing (Production-Ready)

**Current Status**: Core infrastructure implemented (~70% complete). Production readiness requires real service integrations and missing features.

**Phase 1 – Production Service Integrations** (CRITICAL - Blocking Production)
- Replace all mock clients with real HTTP clients:
  - IAM client: Real HTTP client calling IAM `/v1/iam/decision` and `/v1/iam/verify` endpoints.
  - ERIS client: Real HTTP client calling ERIS `/v1/evidence/receipts` endpoint with retry and circuit breaker.
  - LLM Gateway client: Real HTTP client calling LLM Gateway `/v1/llm/generate` endpoint with safety pipeline.
  - Policy client: Real HTTP client calling Policy service `/v1/policy/tenants/{tenant_id}/evaluate` with caching.
  - Data Governance client: Real HTTP client calling Data Governance `/v1/data-governance/tenants/{tenant_id}/config`.
  - UBI client: Real HTTP client calling UBI `/v1/ubi/signals/recent` endpoint.
- Implement decision receipt emission in `decide()` method (synchronous, before response).
- Implement degraded mode handling for all dependencies (circuit breakers, fallback logic).
- Implement policy unavailable handling (fail-closed for safety-critical, cached snapshot for others).

**Phase 2 – Missing Features** (IMPORTANT - Feature Completeness)
- Implement actor preferences (FR-14):
  - Database table `mmm_actor_preferences`.
  - API endpoints: GET/PUT `/v1/mmm/actors/{actor_id}/preferences`, POST `/v1/mmm/actors/{actor_id}/preferences/snooze`.
  - Preference enforcement in `decide()` method.
  - Edge Agent proxy API.
- Implement experiment management (FR-13):
  - CRUD endpoints for experiments.
  - Experiment activation/deactivation.
  - A/B testing logic (if adaptive learning implemented).
- Implement tenant MMM policy configuration (FR-13):
  - PUT `/v1/mmm/tenants/{tenant_id}/policy` endpoint.
  - Policy storage and retrieval.
  - Policy enforcement in decision flow.
- Implement dual-channel confirmation (FR-6):
  - Database table `mmm_dual_channel_approvals`.
  - Approval workflow logic.
  - Integration with Edge Agent for approval UI.

**Phase 3 – Production Hardening** (IMPORTANT - Reliability)
- Implement distributed tracing (OpenTelemetry):
  - Span creation for decision flow.
  - Parent-child span linking.
  - Trace export to observability backend.
- Move fatigue manager state to Redis (for horizontal scaling):
  - Redis client integration.
  - Key-based fatigue tracking.
  - TTL-based expiration.
- Implement data retention/deletion:
  - Background cleanup job.
  - Retention policy enforcement.
  - Actor-level deletion support.
- Implement latency SLO monitoring and alerting.
- Implement comprehensive error handling and recovery.

**Phase 4 – Advanced Features** (OPTIONAL - Future Enhancements)
- Implement adaptive learning (FR-9) if desired:
  - Aggregate outcome analysis.
  - Bandit-style playbook selection (per tenant).
  - Explainable adaptation logic.
- Implement advanced observability:
  - Custom dashboards.
  - Anomaly detection.
  - Predictive analytics.

**Production Readiness Checklist**:
- [ ] All mock clients replaced with real HTTP clients
- [ ] Decision receipts emitted synchronously in `decide()` method
- [ ] Degraded mode handling for all dependencies
- [ ] Policy unavailable handling implemented
- [ ] Actor preferences implemented (FR-14)
- [ ] Experiment management implemented (FR-13)
- [ ] Tenant MMM policy configuration implemented (FR-13)
- [ ] Dual-channel confirmation implemented (FR-6)
- [ ] Distributed tracing implemented (FR-15)
- [ ] Fatigue manager state in Redis
- [ ] Data retention/deletion implemented (NFR-3)
- [ ] Latency SLO monitoring implemented (NFR-1)
- [ ] Security audit logging implemented (NFR-7)
- [ ] Load testing completed (NFR-2)
- [ ] All integration tests passing
- [ ] All resilience tests passing (RF-MMM-01, RF-MMM-02, RF-MMM-03)

