EPC-9 – User Behaviour Intelligence (UBI)
Module Type: Embedded Platform Capability
Plane Dependencies: CCP-1 (Identity & Trust), CCP-2 (Policy & Configuration), CCP-3 (Evidence & Audit), CCP-4 (Observability & Reliability), CCP-6 (Data & Memory), CCP-7 (AI Lifecycle & Safety)

1. Summary & Intent
The User Behaviour Intelligence (UBI) module provides a privacy-preserving, actor-aware behavioural analytics capability for ZeroUI. It transforms raw behavioural signals from humans and AI agents (“actors”) into structured profiles, metrics, risks, and opportunities that power:
MMM Engine: persona-aware nudges and recommendations.
Detection Engine Core: early warning signals and behavioural risk features.
Gold Standards & Policy Engine: enforcement inputs (e.g., gating, escalation).
ROI & Ops Dashboards: aggregated, de-identified views of engineering health.
UBI does not enforce actions directly; it generates intelligence (scores, labels, explanations) that downstream modules consume and enforce under policy.

2. Problem Statement
ZeroUI aims to “Prevent First on the Laptop” by understanding how actors actually work: context switching, focus time, risky patterns, stuck work, and collaboration dynamics. Today:
Behaviour signals are scattered across IDE, Git, CI/CD, ticketing, and LLM usage.
There is no unified, actor-centric view of behaviour aligned with modern frameworks like DORA (delivery performance) and SPACE (multi-dimensional developer experience).
Behavioural rules are either hard-coded or ad-hoc; they don’t adapt to teams, personas, or historical baselines.
Privacy and trust concerns block many organisations from enabling behavioural analytics at all.
We need a first-class platform capability that:
Unifies behavioural data for human and AI actors.
Derives explainable metrics, baselines, anomalies, and risk/opportunity signals.
Respects strict privacy and data minimisation constraints.

3. Goals & Non-Goals
3.1 Goals
Unified Behavioural Layer for Actors
Provide a consistent, tenant-scoped representation of actor behaviour across IDE, VCS, CI, work items, and LLM/agent usage.
Multi-Level Behavioural Intelligence
Compute features, profiles, and baselines per actor, team, and repository, inspired by product analytics and UEBA patterns (event-based, cohort-based, anomaly-aware).
Explainable Risk & Opportunity Signals
Provide machine-readable signals (scores, labels) and human-readable explanations (evidence snippets), suitable for MMM nudges, detection rules, and governance decisions.
Privacy-First, Data-Minimised Behaviour Analytics
Apply data minimisation, purpose limitation, and distributed processing principles: collect only what is needed, at the coarsest granularity possible, with strong tenant configuration options.
Framework-Aligned Metrics (DORA + SPACE-informed)
Expose metrics that support DORA delivery metrics (via other modules) and SPACE-style dimensions (satisfaction, activity, flow, collaboration) at a team/tenant level, not as weaponised individual KPIs.
Actor Parity (Human + AI Agents)
Treat human developers and AI coding agents uniformly as “actors” in the behavioural model, with consistent telemetry and risk/opportunity signals.
3.2 Non-Goals
UBI does not:
Implement low-level signal collection (handled by Signal Ingestion & Normalization).
Enforce gating or block actions (handled by Policy Engine / MMM / Detection Engine).
Perform HR-style performance review or surveillance; output is not a performance rating.
Replace DORA or SPACE; instead, it feeds those metrics with actor-centric context.

4. Scope
4.1 In Scope
Behavioural feature extraction from normalised events.
Actor and team behavioural profiles and baselines.
Behavioural scores and labels:
e.g., Focus Stability, Context Switch Rate, Collaboration Breadth, Risky Behaviour Score, Strain Indicators (patterns associated with burnout risk, e.g., extreme out-of-hours activity).
Detection of behavioural anomalies (UEBA-style but oriented to engineering health, not just security).
Exposed APIs for downstream consumers (MMM, Detection, dashboards, IDE/Edge).
4.2 Out of Scope
Direct security incident detection (covered by Security & Supply Chain plane, UEBA in SOC tools).
Psychological or medical inference (no health diagnoses).
Any crossing of tenant boundaries (multi-tenant isolation is mandatory).

5. Personas & Consumers
Actor (Human Engineer / AI Coding Agent) – produces behavioural signals; indirectly affected by UBI through MMM nudges and policy decisions.
Tech Lead / Manager – consumes aggregated metrics and patterns (team health, risk hotspots).
SRE / Reliability Lead – uses UBI signals correlated with incidents/outages.
Platform Owner / Governance Lead – configures UBI policies (what is collected, retention, aggregation thresholds).
MMM Engine / Detection Engine / ZeroUI Agent – direct API consumers for risk/opportunity features.

6. Key Concepts & Definitions
Actor – human developer, AI coding agent, or service entity, uniquely identified within tenant. Actor types are: `human`, `ai_agent`, `service` (standardized across platform modules).
Behavioural Event – a normalised, privacy-filtered event describing an actor action. UBI consumes `SignalEnvelope` from PM-3 (Signal Ingestion & Normalization), which contains events such as "file_edited", "build_failed", "llm_request_submitted" with properties such as timestamps, artefact IDs, and context.
Behavioural Feature – derived metric from events over a window, e.g. “average uninterrupted focus time per day”.
Baseline – normal range of a feature for a given actor/team/peer group over a historical window.
Anomaly – a statistically significant deviation from baseline.
Behavioural Score – normalised (e.g., 0–100) output indicating risk or opportunity within a dimension.
Dimension – conceptual axes inspired by SPACE (e.g., Activity, Collaboration, Flow) and extended for agentic systems.

7. Functional Overview
At a high level, UBI provides a pipeline:
Input: Normalised behavioural events from Signal Ingestion & Normalization (PM-3), with tenant, actor, and privacy annotations.
Feature Extraction: Rolling windows compute behavioural features (counts, ratios, time-based metrics).
Baseline & Profiling: Per actor, team, and peer groups, over configurable windows, using UEBA-style profiling.
Scoring & Labelling: Rules and ML models map features vs baselines to scores and flags.
Explanation & Evidence Linking: Each score/flag is linked to explainable evidence (summarised events, not raw data).
Output:
APIs: GET /v1/ubi/actors/{actor_id}/profile, POST /v1/ubi/query/signals, etc.
Streams: event streams for MMM and Detection (e.g., behavioural_signal events).

8. Detailed Functional Requirements (FR)
FR-1 – Behavioural Event Consumption
UBI MUST consume normalised behavioural events from PM-3 (Signal Ingestion & Normalization), not raw device logs.
UBI MUST consume `SignalEnvelope` from PM-3, which contains the following fields:
- `signal_id` (global unique ID from PM-3)
- `tenant_id` (tenant identifier)
- `actor_id` (human or AI agent ID, if applicable)
- `signal_kind` (`event` | `metric` | `log` | `trace`)
- `signal_type` (e.g., `pr_opened`, `test_failed`, `gate_evaluated`, `build_metric`)
- `occurred_at` (ISO 8601 timestamp when signal occurred)
- `ingested_at` (ISO 8601 timestamp when signal was ingested)
- `trace_id`, `span_id`, `correlation_id` (when available)
- `resource` (service, repo, module, branch, commit, file path if allowed)
- `payload` (type-specific normalized payload)
- `schema_version` (schema version for forward/backward compatibility)

UBI MUST map PM-3 fields to internal representation:
- `occurred_at` → `timestamp_utc` (UBI internal timestamp field)
- `payload` → `properties` (UBI internal properties field)
- `signal_type` → `event_type` (UBI canonical event type taxonomy)
- `actor_id` → `actor_id` (preserved)
- `tenant_id` → `tenant_id` (preserved)

UBI MUST extract `actor_type` from PM-3's `resource` metadata or `payload` attributes. If not present, UBI MUST infer from context or default to `human`. Actor type values MUST be: `human`, `ai_agent`, or `service` (standardized across platform).

UBI MUST extract privacy classification from PM-3's `resource` metadata or `payload` attributes. If PM-3 does not provide explicit `privacy_tags`, UBI MUST classify based on event type and payload content using Data Governance classification rules.

Event Consumption Mechanism:
UBI MUST consume events via PM-3 routing. PM-3 routes signals to routing classes (per PM-3 PRD Section 4.6, F6). UBI MUST subscribe to PM-3 routing class `realtime_detection` or `analytics_store` (configurable per tenant). Event delivery semantics: at-least-once delivery. UBI MUST handle out-of-order events using `occurred_at` timestamp for ordering. Idempotency: UBI MUST use PM-3's `signal_id` as idempotency key to prevent duplicate processing.

Event Type Taxonomy:
UBI MUST maintain a canonical event type taxonomy. Supported event types include (non-exhaustive):
- `file_edited`, `file_created`, `file_deleted`
- `build_failed`, `build_succeeded`, `test_failed`, `test_passed`
- `pr_created`, `pr_merged`, `pr_closed`, `pr_reviewed`
- `commit_created`, `commit_pushed`
- `llm_request_submitted`, `llm_request_completed`, `llm_request_failed`
- `context_switch`, `focus_session_started`, `focus_session_ended`
- `gate_evaluated`, `policy_violation`, `override_attempted`

UBI MUST map PM-3 `signal_type` to UBI canonical `event_type` using configurable mapping rules. Mapping rules MUST be tenant-configurable and versioned.

UBI MUST support configurable inclusion/exclusion of event types per tenant (data minimisation). UBI MUST implement tenant-level filtering after receiving events from PM-3. UBI MUST maintain tenant configuration for allowed event types. UBI MUST drop events that don't match tenant configuration (with audit log entry).
FR-2 – Behavioural Feature Computation
UBI MUST compute feature sets over configurable windows (e.g., 24h, 7d, 28d) such as:
Activity features: event counts, commit frequency, build/test runs, PR creation/merge.
Flow & context features: context switches per hour, focus session lengths (time between context switches), after-hours activity.
Collaboration features: PR reviewers, comments, mentions, pair sessions, cross-team interactions.
Agent usage features: LLM requests per work item, retries, override frequency, tool call patterns.
Features MUST be computed for actors and teams, with tenant-configurable thresholds and windows.
FR-3 – Actor & Team Baselines
UBI MUST maintain rolling baselines for features:
Per actor, team, and peer cohort (e.g., similar seniority, same team).
Baselines MUST:
be recalculated periodically (e.g., nightly batch) or incrementally,
support configurable historical windows (e.g., last 90 days).

Baseline Computation Algorithm:
UBI MUST use exponential moving average (EMA) for baseline computation, with configurable alpha parameter (default: 0.1). For initial baseline computation, UBI MUST use simple moving average until sufficient data points are collected, then transition to EMA.

Minimum Data Points:
UBI MUST require minimum 7 days of data collection before baseline computation is considered valid. During warm-up period (first 7 days), UBI MUST:
- Mark baselines as "low confidence" (confidence < 0.5)
- Do not emit anomalies based on warm-up baselines
- Continue collecting data for baseline computation

Outlier Handling:
UBI MUST exclude outliers beyond 3 standard deviations during baseline computation. Outliers MUST be logged but excluded from mean and standard deviation calculations.

Warm-up Period:
UBI MUST implement a warm-up period of 7 days minimum data collection per tenant before baseline computation. During warm-up, baselines MUST be marked as "low confidence" and anomalies MUST NOT be emitted. After warm-up, baselines transition to "normal confidence" and anomaly detection is enabled.

UBI MUST compute z-scores or comparable deviation metrics to support anomaly detection.
FR-4 – Behavioural Anomaly Detection
UBI MUST flag anomalies where behaviour deviates significantly from baseline (configurable thresholds).

Anomaly Detection Thresholds:
UBI MUST use z-score based anomaly detection with configurable thresholds:
- Default WARN threshold: |z-score| > 2.5
- Default CRITICAL threshold: |z-score| > 3.5
- Thresholds MUST be configurable per tenant and per dimension
- False positive rate target: < 5% (industry standard for UEBA)
- UBI MUST implement feedback loop to tune thresholds based on false positive rate

Severity Enum:
UBI MUST define severity enum values: `INFO`, `WARN`, `CRITICAL`. "High-severity" signals are defined as `severity >= WARN`. Severity threshold MUST be configurable per tenant.

Anomalies MAY include:
Sudden drop in activity or engagement.
Sudden surge in after-hours work.
Unusual pattern of failed builds/tests related to an actor.
Outlier patterns of AI/LLM usage (e.g., repeated overrides of guardrails).

Each anomaly MUST be tagged with:
severity (INFO | WARN | CRITICAL), dimension, feature_ids, baseline_reference, and supporting_evidence (event summaries).

Anomaly Resolution:
UBI MUST automatically resolve anomalies when feature values return to baseline (within 1 standard deviation) for configurable duration (default: 24 hours). Resolved anomalies MUST be marked with `status = "resolved"` and `resolved_at` timestamp.
FR-5 – Behavioural Scores & Dimensions
UBI MUST compute scores in defined dimensions, informed by SPACE but extended for agent/LLM work:
Activity & Reliability: sustainable activity vs thrash, correlated with DORA metrics from Observability.
Flow & Context Stability: uninterrupted focus, context switching behaviour.
Collaboration & Knowledge Flow: depth/breadth of collaboration across repos/teams.
Agent Synergy: how effectively an actor uses AI/agents (e.g., balanced vs code-dumping).
Scores MUST:
be normalised to a known range (e.g., 0–100),
include confidence levels,
be available at actor, team, and tenant-aggregated levels.
FR-6 – Opportunity Signals
UBI MUST expose opportunity signals (not just risk), e.g.:
“High mentoring potential” (supports others often).
“Candidate for pair-work support” (high complexity work, frequent stuck signals).
“Agent usage optimisation” (over/under-use of certain AI patterns).
Each signal MUST specify:
intent (what MMM could do),
expected positive outcome,
confidence.
FR-7 – Risk Signals (Non-Security)
UBI MUST generate non-security behavioural risk signals such as:
Increased likelihood of burnout (sustained out-of-hours work, reduced collaboration).
Increasing rework loops (multiple failed builds/PR revisions).
High context switching across many tickets without completion.
Risk signals MUST only be interpretable within configured ethical and legal guidelines per tenant; UBI MUST allow disabling certain signal classes if compliance requires.
FR-8 – Privacy, Aggregation & De-Identification Controls
UBI MUST implement:
Data minimisation and purpose limitation: collect/features only what is required for configured use cases.
Configurable aggregation thresholds: no team metrics if team size below threshold (to avoid singling out individuals).
Aggregation threshold: Minimum 5 actors per team metric (k-anonymity requirement). Teams with fewer than 5 actors MUST only expose tenant-level aggregates, not team-level metrics.

Pseudonymisation at storage where feasible (actor IDs separated from personal identifiers managed by IAM).

Data Governance Integration:
UBI MUST honour per-tenant data residency and retention specified by Data Governance (EPC-2).
UBI MUST query Data Governance API for retention policies: `GET /privacy/v1/retention/policies?tenant_id={tenant_id}` (per Data Governance PRD).
UBI MUST implement periodic retention policy evaluation (daily batch job) to re-evaluate existing data against current retention policies.
UBI MUST implement data deletion callback from Data Governance (event-driven or polling): `POST /privacy/v1/retention/delete?tenant_id={tenant_id}&time_range={range}`.
When Data Governance triggers deletion, UBI MUST remove associated features, baselines, and signals for the specified time range or actor.

Privacy Classification Integration:
UBI MUST integrate with Data Governance classification service for payload content validation: `POST /privacy/v1/classification` (if available).
Alternatively, UBI MUST use privacy tags from PM-3 events to determine data minimisation.
UBI MUST document data minimisation rules per event type.

Privacy-Preserving Analytics:
UBI MUST implement k-anonymity requirements: minimum 5 actors per aggregated metric.
UBI MAY consider differential privacy techniques for sensitive metrics (if needed, per tenant configuration).
FR-9 – Actor Parity & Fairness
UBI MUST treat human, AI agent, and service actors uniformly in its data model:
same feature structures for all actor types, with `actor_type` tags. Actor type values MUST be: `human`, `ai_agent`, `service` (standardized across platform modules).
UBI MUST avoid using only volume metrics (e.g., LOC written) as direct quality proxies, following SPACE guidance that output-only metrics distort behaviour.
UBI MUST enforce policy-based prohibition of volume-only metrics as direct quality or performance proxies. If tenant policy forbids volume-only metrics, UBI MUST NOT use such metrics as direct triggers or primary score inputs; any use MUST be limited to supporting context consistent with policy.
FR-10 – Explainability & Evidence
UBI MUST provide:
reason strings and evidence references for every score and anomaly,
e.g., "focus_flow_score dropped from 75→50; 5+ context switches per hour over the last 3 days; see events E1–E9".

Evidence Storage and Linking:
Evidence MUST be stored in ERIS (PM-7) and referenced via `evidence_handles` array (per ERIS PRD Section 8.1).
Evidence handle format MUST conform to ERIS evidence handle structure:
- `evidence_id` (unique identifier)
- `evidence_type` (e.g., "event_summary", "feature_snapshot", "baseline_reference")
- `storage_location` (ERIS reference)
- `expires_at` (optional expiration timestamp)

Alternatively, if evidence is small (< 1KB), UBI MAY embed evidence summaries directly in BehaviouralSignal `evidence_refs` field (as JSON objects, not ERIS handles).

Evidence retention policy MUST align with ERIS evidence retention policies and Data Governance requirements.

Evidence for downstream modules MUST be summarised, not raw logs, and always respect privacy tags.
FR-11 – Interfaces for MMM, Detection, Dashboards
UBI MUST expose:
Query APIs for:
Get actor profile & recent signals.
Get team-level summaries.
Query signals by dimension and interval.

Event Streams:
UBI MUST expose event stream `ubi.behavioural_signals` for downstream consumers (MMM Engine, Detection Engine).

Event Stream Specification:
- Message format: Serialized `BehaviouralSignal` JSON object (per Section 10.4 data model)
- Delivery semantics: At-least-once delivery (recommended for auditability)
- Consumer acknowledgment: If using message queue, consumers MUST acknowledge message receipt
- Error handling: Failed message delivery MUST be routed to DLQ (Dead Letter Queue) with retry logic
- Backpressure handling: UBI MUST implement signal buffering and rate limiting to prevent consumer overwhelm
- Message schema: Each message MUST include:
  - `signal_id`, `tenant_id`, `actor_scope`, `actor_or_group_id`
  - `dimension`, `signal_type`, `score`, `severity`, `status`
  - `evidence_refs`, `created_at`, `updated_at`
  - Snapshot of relevant features (if applicable)

Stream Filtering:
- MMM Engine: Receives all BehaviouralSignals (risk and opportunity signals)
- Detection Engine: Receives high-severity signals only (`severity >= WARN`)
- Filtering MUST be configurable per consumer subscription

Batch export interface for:
ROI dashboards and periodic reporting (de-identified).
FR-12 – Configuration APIs
Tenants MUST be able to configure:
Which event categories are allowed.
Calculation windows, thresholds, aggregation levels.
Which signal classes are enabled (risk vs opportunity).
Changes MUST be versioned and auditable (via CCP-3 / ERIS).

FR-13 – Evidence & Receipts Integration
UBI MUST integrate with the Evidence & Audit plane (CCP-3 / PM-7 – ERIS) so that key configuration and signal-related operations are recorded as machine-readable receipts.

Receipt Schema:
All receipts emitted by UBI MUST conform to the canonical receipt schema defined in `docs/architecture/receipt-schema-cross-reference.md` and ERIS PRD Section 8.1.
UBI receipt `gate_id` MUST be: `"ubi"` (standardized across platform).
Required receipt fields for UBI receipts:
- `receipt_id` (UUID, unique per receipt)
- `gate_id` = `"ubi"`
- `schema_version` (receipt schema version, e.g., "1.0.0")
- `policy_version_ids` (array of policy version IDs, if applicable)
- `snapshot_hash` (SHA256 hash of policy snapshot, if applicable)
- `timestamp_utc` (ISO 8601 UTC timestamp)
- `timestamp_monotonic_ms` (hardware monotonic timestamp in milliseconds)
- `evaluation_point` (enum: `pre-commit`, `pre-merge`, `pre-deploy`, `post-deploy`, or `"config"` for configuration changes)
- `inputs` (metadata-only JSON object with operation inputs)
- `decision.status` (enum: `pass`, `warn`, `soft_block`, `hard_block`; for config changes: use `pass` for success, `warn` for failure)
- `decision.rationale` (human-readable explanation string)
- `decision.badges` (array of badge strings, optional)
- `result` (metadata-only JSON object with operation results)
- `actor.repo_id` (repository identifier, required)
- `actor.machine_fingerprint` (optional machine fingerprint)
- `actor.type` (enum: `human`, `ai_agent`, `service`)
- `evidence_handles` (optional array of evidence references)
- `degraded` (boolean flag indicating degraded mode operation)
- `signature` (cryptographic signature, required)
- `tenant_id` (derived from receipt metadata or IAM context)

UBI MUST validate receipts against schema before emission. UBI MUST specify schema version in receipt `schema_version` field.

ERIS Integration:
UBI MUST use ERIS ingestion API: `POST /v1/evidence/receipts` (per ERIS PRD Section 9.1).
UBI MUST implement retry logic with exponential backoff (max 24 hours) for receipt emission failures.
UBI MUST handle ERIS unavailability gracefully:
- Queue receipts in local persistent store (e.g., SQLite, file-based queue)
- Retry with exponential backoff (max 24 hours)
- If retry fails: Move to DLQ for manual intervention
- Surface telemetry about receipt emission failures
- Do not block behavioural processing due to receipt emission failures (degrade gracefully)

Receipt Emission Triggers:
For each successful or failed write to `/v1/ubi/config/{tenant_id}`, UBI MUST emit a configuration-change receipt that, at minimum, references:
- `tenant_id`
- The new configuration version identifier
- The triggering actor identity (IAM identity of the requester, e.g., tenant admin)
- For configuration changes: `actor.type = "human"` (tenant admin) or `actor.type = "service"` (if triggered by system service)
- The outcome (`decision.status = "pass"` for success, `"warn"` for failure)
- A monotonic timestamp (`timestamp_monotonic_ms`)

For the creation or state change of high-severity BehaviouralSignals (`severity >= WARN`) at team or tenant scope, UBI MUST emit a receipt that references:
- `signal_id`
- `tenant_id`
- `actor_scope` (team or tenant)
- `severity` (WARN or CRITICAL)
- `dimension`
- `evidence_refs`
- `created_at`/`updated_at` timestamps

For signal generation receipts: `actor.type = "service"` (UBI service identity), with signal subject (the actor/team the signal is about) in receipt `inputs` or `result` metadata.

These receipts MUST be persisted via the Evidence & Receipt Indexing Service (ERIS) rather than any ad-hoc UBI-local audit log.

All receipts emitted by UBI MUST conform to the receipt schema defined by ERIS and flow exclusively through the Evidence & Audit plane; UBI MUST NOT implement a separate, divergent audit store for these operations.

9. Non-Functional Requirements (NFR)
NFR-1 – Privacy & Compliance:
Align with NIST Privacy Framework and data protection principles of data minimisation, accuracy, storage limitation, and purpose limitation.
NFR-2 – Latency:
Behavioural features: near-real time (e.g., 1–5 minutes) or batch, depending on use case; configurable per signal class.

Performance SLOs:
- Event processing: 1000 events/second throughput, p95 latency < 5 seconds per event
- Feature computation: p95 latency < 1 minute for 24-hour window features
- Baseline recompute: 1000 actors within 1 hour (nightly batch job)
- API query latency: p95 < 500ms for actor profile queries, p95 < 2 seconds for signal queries
- Backlog limit: < 1000 events in processing queue
NFR-3 – Scalability:
Support up to many thousands of actors per tenant and high event volumes; design should be horizontally scalable (time-series/columnar storage for features).

Data Partitioning Strategy:
UBI MUST partition data by `tenant_id` and `dt` (date, derived from `timestamp_utc`) for efficient queries and retention management.
Partition size limit: Maximum 10GB per partition.
Partitioning enables efficient:
- Time-range queries (by date partition)
- Retention policy enforcement (delete entire partitions)
- Tenant isolation (partition by tenant_id)
NFR-4 – Multi-Tenancy & Isolation:
Hard isolation by tenant_id; no cross-tenant feature computation or baselines.
NFR-5 – Observability:
Emit metrics/logs/traces via CCP-4, including:
number of events processed, features computed,
number of anomalies detected,
computation latencies,
error rates.

Observability Metrics Schema:
UBI MUST emit the following Prometheus-format metrics:
- `ubi_events_processed_total{tenant_id, event_type, status}` (counter) - Total events processed, labeled by tenant, event type, and processing status (success/failure)
- `ubi_signals_generated_total{tenant_id, dimension, signal_type}` (counter) - Total signals generated, labeled by tenant, dimension, and signal type (risk/opportunity/informational)
- `ubi_anomalies_total{tenant_id, dimension, severity}` (counter) - Total anomalies detected, labeled by tenant, dimension, and severity (INFO/WARN/CRITICAL)
- `ubi_feature_computation_duration_seconds{tenant_id, feature_name}` (histogram) - Feature computation latency, labeled by tenant and feature name
- `ubi_baseline_recompute_duration_seconds{tenant_id, actor_scope}` (histogram) - Baseline recompute latency, labeled by tenant and scope (actor/team/cohort)
- `ubi_receipt_emission_total{tenant_id, status}` (counter) - Total receipts emitted to ERIS, labeled by tenant and status (success/failure)
- `ubi_api_request_duration_seconds{tenant_id, endpoint, method}` (histogram) - API request latency, labeled by tenant, endpoint, and HTTP method
- `ubi_queue_size{tenant_id}` (gauge) - Current event processing queue size, labeled by tenant

Traces MUST link event→feature→signal spans with correlation IDs.
NFR-6 – Reliability:
Graceful degradation: if UBI is unavailable, other modules see "no signal" or "stale data" status; no inconsistent partial writes.

Degradation Behavior:
UBI MUST mark data as "stale" when:
- Data is older than 1 hour (configurable threshold, default: 1 hour)
- PM-3 ingestion is unavailable for longer than usual processing interval
- Baseline recomputation has not completed within expected window

UBI MUST add `stale: true` flag to API responses when data is stale.
UBI MUST continue serving existing profiles and signals when PM-3 is unavailable, but MUST mark them as stale.
UBI MUST NOT corrupt baselines or generate spurious anomalies due to missing data during outages.
UBI MUST resume processing automatically once dependencies recover, without manual intervention.

10. Data Model (Conceptual)
10.1 BehaviouralEvent (derived from PM-3 SignalEnvelope)
UBI consumes `SignalEnvelope` from PM-3 and maps to internal `BehaviouralEvent` representation:
- `event_id` (mapped from PM-3 `signal_id`)
- `tenant_id` (from PM-3 `tenant_id`)
- `actor_id` (from PM-3 `actor_id`)
- `actor_type` (extracted from PM-3 `resource` or `payload`; enum: `human`, `ai_agent`, `service`)
- `source_system` (extracted from PM-3 `producer_id` or `resource.service_name`; e.g., IDE, Git, CI, LLM_GATEWAY)
- `event_type` (mapped from PM-3 `signal_type` using canonical taxonomy; e.g., `file_edited`, `build_failed`, `pr_created`, `llm_request_submitted`)
- `timestamp_utc` (mapped from PM-3 `occurred_at`; ISO 8601 format)
- `ingested_at` (from PM-3 `ingested_at`; ISO 8601 format)
- `properties` (mapped from PM-3 `payload`; key/value, privacy-tagged)
- `privacy_tags` (extracted from PM-3 `resource` metadata or `payload` attributes; e.g., `contains_PI: true/false`, `contains_code_snippet: true/false`)
- `schema_version` (from PM-3 `schema_version`; for forward/backward compatibility)
- `trace_id`, `span_id`, `correlation_id` (from PM-3, when available)
- `resource` (from PM-3 `resource`; service, repo, module, branch, commit, file path if allowed)
10.2 BehaviouralFeature
feature_id
tenant_id
actor_scope (actor | team | cohort)
actor_or_group_id
feature_name
window_start, window_end
value
dimension (activity, flow, collaboration, agent_usage, etc.)
confidence
metadata (calculation details)
10.3 BehaviouralBaseline
baseline_id
tenant_id
actor_scope
actor_or_group_id
feature_name
window
mean, std_dev, percentiles
last_recomputed_at
10.4 BehaviouralSignal
signal_id
tenant_id
actor_scope (actor | team | cohort | tenant)
actor_or_group_id
dimension (activity, flow, collaboration, agent_usage, etc.)
signal_type (risk | opportunity | informational)
score (0–100)
severity (INFO | WARN | CRITICAL)
status (active | resolved)
evidence_refs (array of evidence references: event summaries, feature IDs, baseline ID, ERIS evidence handles)
created_at, updated_at
resolved_at (optional; timestamp when anomaly was resolved)

11. APIs & Integration Contracts (Logical)
(All URLs are logical; concrete OpenAPI specs live in the Contracts & Schema Registry.)

Authentication & Authorization:
All UBI API endpoints MUST require authentication via IAM (EPC-1).
UBI MUST integrate with IAM for token verification: `POST /iam/v1/verify` (per IAM module pattern).
UBI MUST enforce authorization using IAM roles:
- `ubi:read:actor` - Read actor-level behavioural data
- `ubi:read:team` - Read team-level aggregated data
- `ubi:read:tenant` - Read tenant-level aggregated data
- `ubi:write:config` - Write configuration changes
- `product_ops` or `admin` - Privileged access to all tenants (for ZeroUI Product Ops)

UBI MUST enforce tenant isolation: all queries MUST be scoped to caller's `tenant_id` from IAM token.
Cross-tenant queries are only allowed for privileged roles (`product_ops` or `admin`).

11.1 Get Actor Behaviour Profile
GET /v1/ubi/actors/{actor_id}/profile
Authentication: Required (IAM JWT token)
Authorization: Requires `ubi:read:actor` role for the tenant
Query params:
- `tenant_id` (required; MUST match IAM token `tenant_id` claim)
- `window` (optional; default last 7 days)
Response:
- Actor metadata (pseudonymised)
- Recent BehaviouralSignals, grouped by dimension
- Summary of key BehaviouralFeatures and deviations
- `stale: boolean` (indicates if data is stale, per NFR-6)
Error responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: Insufficient permissions (missing `ubi:read:actor` role)
- 404 Not Found: Actor not found or not accessible
11.2 Query Signals
POST /v1/ubi/query/signals
Authentication: Required (IAM JWT token)
Authorization: Requires `ubi:read:actor` (for actor scope) or `ubi:read:team` (for team scope) or `ubi:read:tenant` (for tenant scope)
Body:
- `tenant_id` (required; MUST match IAM token `tenant_id` claim)
- `scope` (actor | team | tenant)
- `dimensions` [optional] (array of dimension names)
- `time_range` (required; `from` and `to` ISO 8601 timestamps)
- `filters` (optional; e.g., `min_severity` (INFO | WARN | CRITICAL), `actor_ids`, `team_ids`, `signal_types`)
Response:
- List of BehaviouralSignals with `evidence_refs`
- `stale: boolean` (indicates if data is stale, per NFR-6)
Error responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: Insufficient permissions (missing required role for scope)
- 400 Bad Request: Invalid query parameters
11.3 Stream: Behavioural Signal Updates
Channel: internal event bus topic, e.g. `ubi.behavioural_signals` (sink for MMM, Detection).

Event Stream Specification:
- Message format: Serialized `BehaviouralSignal` JSON object (per Section 10.4 data model)
- Delivery semantics: At-least-once delivery (recommended for auditability)
- Consumer acknowledgment: If using message queue, consumers MUST acknowledge message receipt
- Error handling: Failed message delivery MUST be routed to DLQ (Dead Letter Queue) with retry logic
- Backpressure handling: UBI MUST implement signal buffering and rate limiting to prevent consumer overwhelm

Message Schema:
Each message MUST include:
- `signal_id`, `tenant_id`, `actor_scope`, `actor_or_group_id`
- `dimension`, `signal_type` (risk | opportunity | informational), `score` (0-100), `severity` (INFO | WARN | CRITICAL), `status` (active | resolved)
- `evidence_refs` (array of evidence references)
- `created_at`, `updated_at`, `resolved_at` (if resolved)
- Snapshot of relevant features (if applicable; embedded as JSON object)

Stream Filtering:
- MMM Engine: Receives all BehaviouralSignals (risk and opportunity signals)
- Detection Engine: Receives high-severity signals only (`severity >= WARN`)
- Filtering MUST be configurable per consumer subscription
11.4 Configuration APIs
GET /v1/ubi/config/{tenant_id}
Authentication: Required (IAM JWT token)
Authorization: Requires `ubi:read:tenant` role for the tenant
Response:
- Current configuration for tenant
- Configuration version identifier
- `enabled_event_categories` (array of allowed event types)
- `feature_windows` (object with window configurations)
- `aggregation_thresholds` (object with threshold values, e.g., `min_team_size: 5`)
- `enabled_signal_types` (array: risk, opportunity, informational)
- `privacy_settings` (object with privacy configuration)
- `anomaly_thresholds` (object with z-score thresholds per dimension)
- `baseline_algorithm` (object with algorithm parameters, e.g., `alpha: 0.1`)

PUT /v1/ubi/config/{tenant_id}
Authentication: Required (IAM JWT token)
Authorization: Requires `ubi:write:config` role for the tenant
Body:
- Settings include:
  - `enabled_event_categories` (array of allowed event types)
  - `feature_windows` (object with window configurations)
  - `aggregation_thresholds` (object with threshold values)
  - `enabled_signal_types` (array: risk, opportunity, informational)
  - `privacy_settings` (object with privacy configuration)
  - `anomaly_thresholds` (object with z-score thresholds per dimension)
  - `baseline_algorithm` (object with algorithm parameters)
Response:
- Configuration version identifier
- Updated configuration
- Receipt ID (for configuration change receipt emitted to ERIS)

Error responses:
- 401 Unauthorized: Missing or invalid token
- 403 Forbidden: Insufficient permissions (missing `ubi:write:config` role)
- 400 Bad Request: Invalid configuration values

12. Interactions with Other Modules

PM-3 – Signal Ingestion & Normalization:
- Supplies `SignalEnvelope` events (privacy-filtered, normalised) via routing classes `realtime_detection` or `analytics_store`
- UBI consumes events via PM-3 routing (per FR-1)
- Event consumption: At-least-once delivery, out-of-order handling, idempotency via `signal_id`
- Field mapping: PM-3 `SignalEnvelope` → UBI `BehaviouralEvent` (per Section 10.1)

PM-7 – Evidence & Receipt Indexing Service (ERIS):
- Receipt emission: UBI emits receipts to ERIS via `POST /v1/evidence/receipts` (per FR-13)
- Receipt schema: Canonical receipt schema from `docs/architecture/receipt-schema-cross-reference.md`
- Receipt `gate_id`: `"ubi"`
- Error handling: Retry with exponential backoff, local queueing, DLQ on failure
- Evidence storage: Evidence handles stored in ERIS, referenced in BehaviouralSignals

PM-4 – Detection Engine Core:
- Consumes high-severity BehaviouralSignals (`severity >= WARN`) as features in risk detection
- Signal format: Serialized `BehaviouralSignal` via event stream `ubi.behavioural_signals`
- Integration clarification: Detection Engine PRD (Section 3.1) states it operates on normalized signals from PM-3. UBI signals are consumed directly by Detection Engine via event stream, not re-ingested through PM-3.

PM-1 – MMM Engine:
- Subscribes to BehaviouralSignals via event stream `ubi.behavioural_signals`
- Receives all signal types (risk and opportunity signals)
- Uses dimensions to prioritise nudges and MMM actions
- Signal format: Serialized `BehaviouralSignal` (per Section 11.3)

EPC-1 – Identity & Access Management (IAM):
- Token verification: `POST /iam/v1/verify` (per IAM module pattern)
- Access decisions: IAM evaluates RBAC/ABAC policies for API access
- IAM roles: `ubi:read:actor`, `ubi:read:team`, `ubi:read:tenant`, `ubi:write:config`
- Tenant isolation: Enforced via IAM token `tenant_id` claim
- Actor identity resolution: UBI validates `actor_id` against IAM (if `actor_id` is IAM user ID) or trusts `actor_id` from PM-3 (if PM-3 validates identity)

EPC-2 – Data Governance & Privacy:
- Retention policies: `GET /privacy/v1/retention/policies?tenant_id={tenant_id}` (per Data Governance PRD)
- Data deletion: `POST /privacy/v1/retention/delete?tenant_id={tenant_id}&time_range={range}`
- Privacy classification: `POST /privacy/v1/classification` (if available)
- UBI MUST honour per-tenant data residency and retention specified by Data Governance
- UBI MUST implement periodic retention policy evaluation (daily batch job)

EPC-10 – Gold Standards:
- Provides reference policies that convert BehaviouralSignals into gating or recommendations
- Policy format: GSMD snapshots or policy-as-code (to be clarified with Gold Standards PRD)
- UBI emits signals that Gold Standards consumes (or UBI evaluates Gold Standards policies, to be clarified)

EPC-8 – Deployment & Infrastructure / CCP-4 – Observability & Reliability:
- Provide runtime, storage, and observability standards for UBI
- Observability metrics emitted via CCP-4 (per NFR-5)

13. Test Strategy & Representative Test Cases
13.1 Unit Tests
UT-UBI-01 – Feature Calculation Correctness
Setup: synthetic BehaviouralEvents representing focused work vs fragmented work.
Assert: features like focus_session_length_avg and context_switch_rate are computed correctly.
UT-UBI-02 – Baseline Computation
Setup: time series for an actor over 30 days with known mean=50, std_dev=10.
Assert: `baseline.mean ≈ 50`, `baseline.std_dev ≈ 10` (within tolerance, e.g., ±0.1).
Test edge cases:
- Insufficient data (< 7 days): Baseline marked as "low confidence"
- All zeros: Baseline computed correctly (mean=0, std_dev=0)
- Outliers beyond 3 standard deviations: Excluded from baseline computation
UT-UBI-03 – Anomaly Threshold Logic
Setup: baseline and new feature with large deviation.
Assert: anomaly is raised when z-score exceeds configured threshold; properly tagged.
Test cases:
- Z-score exactly at threshold (e.g., |z-score| = 2.5): Anomaly triggered (WARN)
- Z-score above CRITICAL threshold (e.g., |z-score| = 3.6): Anomaly triggered (CRITICAL)
- Multiple anomalies in sequence: Anomalies created without duplication
- Anomaly resolution: When feature returns to baseline (within 1 std dev) for 24 hours, anomaly status changes to "resolved"
UT-UBI-04 – Privacy Filtering
Setup: events with privacy_tags indicating sensitive properties.
Assert: features and signals never expose raw sensitive properties; only aggregated indications.
UT-UBI-05 – Actor Parity
Setup: one human actor, one AI agent with identical event patterns.
Assert: features and scores are computed identically; only actor_type differs.
13.2 Integration Tests
IT-UBI-01 – End-to-End from Events to Signals
Flow: inject `SignalEnvelope` events via PM-3 ingestion API `POST /v1/signals/ingest` → PM-3 routes to UBI → UBI processes events → query signals via UBI API `POST /v1/ubi/query/signals`.
Event injection: Use PM-3 ingestion API with test events. Wait for PM-3 processing, then query UBI.
Assert: expected features, baselines, and signals are present; evidence_refs resolve to ERIS evidence handles (if stored in ERIS) or embedded evidence summaries.
IT-UBI-02 – MMM Subscription
Flow: generate anomaly; UBI emits BehaviouralSignal to `ubi.behavioural_signals` stream; MMM consumes.
Assert: MMM receives correctly formatted signal (per Section 11.3 message schema) and can tie it back to actor/team.
Note: MMM PRD does not exist in codebase. Test MUST mock MMM consumer and verify signal format matches UBI specification. When MMM PRD is available, coordinate signal format contract.
IT-UBI-03 – Tenant Isolation
Setup: events for tenants A and B.
Assert: baselines, features, and signals for A never include data from B; cross-tenant queries are rejected.
IT-UBI-04 – Config Change Effect
Flow: change tenant config via `PUT /v1/ubi/config/{tenant_id}` to disable a dimension (e.g., after-hours) by setting `enabled_signal_types = ["risk", "opportunity"]` (excluding "informational").
Assert: 
- UBI stops producing after-hours signals for that tenant
- Query signals → only enabled signal types returned
- Stream subscription → only enabled signal types emitted
- Receipt emitted to ERIS with `gate_id = "ubi"` and `resource_type = "config"`
- Query ERIS for receipt: `POST /v1/evidence/search` with filters `gate_id = "ubi"`, `resource_type = "config"`, `tenant_id = {tenant_id}`
- Validate receipt fields: `tenant_id`, `policy_version_ids` (config version), `decision.status` (`pass` for success, `warn` for failure), `timestamp_utc`
- Verify receipt signature (if applicable)
13.3 Performance & Scale Tests
PT-UBI-01 – High Volume Event Processing
Setup: simulate sustained event rate per actor (e.g., active working day) via PM-3 ingestion API.
Assert: 
- Feature processing keeps up with SLO: 1000 events/second throughput, p95 latency < 5 seconds per event
- Backlog stays within limits: < 1000 events in processing queue
- Metrics `ubi_events_processed_total` and `ubi_feature_computation_duration_seconds` emitted correctly
PT-UBI-02 – Baseline Recompute Load
Setup: 1000 actors, 100 teams, 90 days of history.
Assert: 
- Nightly or periodic baseline recompute completes within SLO: 1000 actors within 1 hour
- No timeouts
- Metrics `ubi_baseline_recompute_duration_seconds` emitted correctly
13.4 Privacy & Compliance Tests
PR-UBI-01 – Data Minimisation
Setup: Configure tenant via `PUT /v1/ubi/config/{tenant_id}` to allow only `event_type`, `timestamp_utc`, `actor_id` fields.
Inject event via PM-3 with additional fields: `properties.secret_key = "sensitive"`, `properties.pii_email = "user@example.com"`.
Assert: 
- Stored event in UBI does not contain `properties.secret_key` or `properties.pii_email`
- Only configured fields are stored
- Disallowed properties are dropped at ingestion (with audit log entry)
PR-UBI-02 – Aggregation Thresholds
Test: for teams below configured size, only tenant-level aggregates are available; team-level queries fail or return masked results.
PR-UBI-03 – Retention & Deletion Integration
Setup: Use Data Governance API to trigger deletion: `POST /privacy/v1/retention/delete?tenant_id={tenant_id}&time_range={range}` (or equivalent API per Data Governance PRD).
Assert: 
- Query UBI for deleted time range → returns empty result
- Query ERIS for deleted receipts → returns empty result (if receipts reference deleted data)
- Associated features, baselines, and signals are removed
- Deletion is logged for audit
13.5 Observability Tests
OB-UBI-01 – Telemetry Emission
Test: run representative workload; ensure metrics are emitted per NFR-5 metrics schema:
- `ubi_events_processed_total{tenant_id, event_type, status}` (counter)
- `ubi_signals_generated_total{tenant_id, dimension, signal_type}` (counter)
- `ubi_anomalies_total{tenant_id, dimension, severity}` (counter)
- `ubi_feature_computation_duration_seconds{tenant_id, feature_name}` (histogram)
- `ubi_baseline_recompute_duration_seconds{tenant_id, actor_scope}` (histogram)
- `ubi_receipt_emission_total{tenant_id, status}` (counter)
- `ubi_api_request_duration_seconds{tenant_id, endpoint, method}` (histogram)
- `ubi_queue_size{tenant_id}` (gauge)
Traces link event→feature→signal spans with correlation IDs.

13.6 Security & Authorisation Tests
ST-UBI-01 – Actor-Level Profile Access Control
Setup: Use IAM test token generation API or mock IAM to generate token bound to correct tenant but without `ubi:read:actor` scope.
Call `GET /v1/ubi/actors/{actor_id}/profile` with token missing `ubi:read:actor` scope.
Assert: the request is rejected with 403 Forbidden; no actor-level profile or signals are returned.

Setup (permitted case): Generate token with `ubi:read:actor` scope via IAM test API or mock IAM.
Call the same endpoint with token that has correct IAM scopes/roles.
Assert: the request succeeds (200 OK); only data for actors and scopes allowed by the caller's IAM permissions are returned.

ST-UBI-03 – Cross-Tenant Access Control
Setup: Generate token for tenant A via IAM test API.
Call `GET /v1/ubi/actors/{actor_id}/profile` with tenant A token, querying actor from tenant B.
Assert: the request is rejected with 403 Forbidden; tenant isolation enforced.

Setup (privileged case): Generate token with `product_ops` or `admin` role via IAM test API.
Call `POST /v1/ubi/query/signals` with privileged token, querying all tenants.
Assert: the request succeeds (200 OK); all tenant data returned (privileged access verified).
ST-UBI-02 – Aggregated vs Actor-Level Access
Setup: issue queries for team-level/tenant-level aggregated BehaviouralSignals using a token that is allowed to see only aggregated data.
Assert: aggregated metrics and signals are returned, but no actor-level identifiers or profiles are exposed. The same token MUST be rejected if it attempts an actor-level profile query.

13.7 Fairness & Misuse-Prevention Tests
FM-UBI-01 – Disabled Signal Classes
Setup: Configure tenant via `PUT /v1/ubi/config/{tenant_id}` with `enabled_signal_types = ["risk", "opportunity"]` (excluding "informational"), or disable individual actor-level risk signals while enabling team-level equivalents.
Assert: 
- UBI does not emit the disabled signals for that tenant (neither via APIs nor streams)
- Query signals with disabled signal type → returns no data or appropriate error
- Stream subscription → only enabled signal types emitted
- Permitted team-level or tenant-level signals still produced
FM-UBI-02 – Prohibited Feature Use
Setup: inspect the metadata and configuration of BehaviouralSignals for a tenant where policy forbids the use of volume-only metrics (such as lines of code written) as direct quality or performance proxies.
Assert: no BehaviouralSignal for that tenant uses prohibited features as a direct trigger or primary score input; any use of such metrics is limited to supporting context consistent with policy and documentation.

13.8 Resilience & Fault-Tolerance Tests
RF-UBI-01 – PM-3 Ingestion Outage
Setup: simulate a sustained outage or delay in the Signal Ingestion & Normalization module (PM-3) so that no new `SignalEnvelope` events arrive for a period longer than the usual processing interval (e.g., > 1 hour).
Assert: 
- UBI continues to serve existing profiles and signals
- Data older than 1 hour is marked as `stale: true` in API responses
- UBI does not corrupt baselines or generate spurious anomalies due to missing data
- Once PM-3 recovers, UBI resumes processing without manual intervention
- Metrics `ubi_queue_size` and `ubi_events_processed_total` reflect outage state
RF-UBI-02 – Evidence & Governance Dependencies
Setup: simulate temporary unavailability of the Evidence & Receipt Indexing Service (ERIS) or Data Governance deletion triggers during normal UBI operation.
Assert: 
- UBI fails receipt writes in a controlled way: receipts queued in local persistent store (e.g., SQLite, file-based queue)
- Retry with exponential backoff (max 24 hours) implemented
- If retry fails: receipts moved to DLQ for manual intervention
- Telemetry about receipt emission failures surfaced: `ubi_receipt_emission_total{status="failure"}` metric
- UBI does not drop or silently ignore required evidence operations
- Behavioural processing degrades gracefully: missing evidence links treated as soft failure, not blocking signal computation
- Data Governance deletion callbacks fail gracefully with retry logic

14. Risks & Mitigations
Risk: Misuse of behavioural scores as individual performance KPIs.
Mitigation: Documentation and configuration emphasise team-level use, configurable disabling of actor-level views, privacy-tiered access via IAM roles.

Risk: Over-collection of behavioural data.
Mitigation: Strong data minimisation defaults; tenant config required for additional event types; privacy review hooks; integration with Data Governance classification service.

Risk: Incorrect baselines and false positives early on.
Mitigation: Warm-up period per tenant (7 days minimum); initial signals flagged as "low confidence" until baseline stabilises; false positive rate target < 5% with feedback loop for threshold tuning.

Risk: Integration contract mismatches with PM-3, ERIS, IAM.
Mitigation: Explicit field mapping specifications (FR-1), receipt schema alignment (FR-13), IAM integration requirements (Section 11), comprehensive integration tests (Section 13.2).

15. Implementation Notes (Non-Binding)
Implementation technologies (DB choice, streaming tech, etc.) are governed by Deployment & Infrastructure and Cross-Cutting Concern Services PRDs. UBI must:
Reuse the platform's event bus, feature store, and schema registry (contracts live under EPC-12).
Store features and baselines in a time-series or columnar-optimised structure consistent with those modules.
Data partitioning: By `tenant_id` and `dt` (date) for efficient queries and retention management. Partition size limit: Maximum 10GB per partition.
Avoid introducing technology not covered by those PRDs without a formal ADR.

Module ID Mapping:
UBI uses module ID `EPC-9`. M-number mapping (e.g., EPC-9 → M35) to be defined in `docs/architecture/MODULE_ID_MAPPING.md` or equivalent mapping document.

Feature Store Integration:
UBI may use platform feature store (if exists) or implement local feature storage. Feature store requirements and integration pattern to be documented during implementation.
