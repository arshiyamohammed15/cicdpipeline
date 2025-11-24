
Health & Reliability Monitoring - PRD
1. Module Overview
Name: Health & Reliability Monitoring
Code: Health & Reliability Monitoring
Type: Embedded Platform Capability
Module ID: Health & Reliability Monitoring will follow the standard M-number mapping pattern (EPC-1 -> M21, EPC-3 -> M23, EPC-11 -> M33, EPC-12 -> M34). The specific M-number assignment will be determined during implementation to maintain consistency with the established naming convention. EPC-8 remains the sole exception using "EPC-8" directly due to its infrastructure classification and historical implementation timing.
Primary Planes:
CCP-1 - Identity & Trust Plane
CCP-2 - Policy & Configuration Plane
CCP-3 - Evidence & Audit Plane
CCP-4 - Observability & Reliability Plane
One-line definition:
A platform capability that continuously measures, evaluates, and exposes the health and reliability state of all ZeroUI components (services, agents, pipelines, planes) using standard SRE metrics and telemetry, so that humans and agents can make safe, informed decisions in real time.

2. Problem Statement
ZeroUI is a multi-plane, agentic system: Laptop, Tenant Cloud, Product Cloud, and Shared Services. Many decisions (gates, nudges, AI actions, releases, rollbacks) assume that core services, dependencies, and agents are healthy enough to act.
Without a dedicated Health & Reliability Monitoring module:
Each component implements its own ad-hoc health checks and metrics.
There is no single, authoritative health view for:
"Is the Edge Agent fleet healthy?"
"Is Detection Engine degraded in Tenant Cloud?"
"Is it safe to let agents auto-remediate right now?"
SLOs and error budgets cannot be consistently enforced across modules, even though SRE practice strongly recommends monitoring user-visible symptoms (latency, traffic, errors, saturation) and resource health (utilization, saturation, errors).
This module provides a unified health model and reliability signals for all other modules and planes.

3. Goals & Non-Goals
3.1 Goals
Unified Health Model
A standard way to represent health for any component (service, agent, job, dependency) as states such as OK / DEGRADED / FAILED / UNKNOWN, with reason codes and supporting metrics.
SRE-Aligned Metrics
Use widely accepted monitoring frameworks:
Four Golden Signals for user-facing services: latency, traffic, errors, saturation.
RED (Rate, Errors, Duration) for microservices.
USE (Utilization, Saturation, Errors) for infrastructure resources.
Cross-Plane, Cross-Tenant Health Views
Ability to compute health per:
Component
Plane (Laptop / Tenant / Product / Shared)
Tenant
Critical dependency group (e.g., "All AI gateways for Tenant T").
Safe Decision & Gating Inputs
Provide machine-readable health signals to:
Detection Engine, MMM Engine, LLM Gateway, Deployment & Infrastructure, Budgeting & Cost module, etc.
Allow gates to degrade or go into safe mode if health is below policy thresholds.
Telemetry-First Design
Use metrics, logs, and traces via OpenTelemetry (OTel)-style telemetry so signals are correlated and portable across backends.
Probes & Heartbeats
Standardise health probes / heartbeats across services and agents (liveness/readiness-style checks) to detect stuck or unhealthy components.
Evidence-Ready
Persist key health transitions and incident-level snapshots to the Evidence & Receipt Indexing Service (ERIS) as audit-grade evidence.
3.2 Non-Goals
Not a full APM UI or dashboard product
It exposes APIs, events, and standard telemetry for downstream dashboards (Grafana, Tempo, etc.) but does not itself render dashboards.
Not a generic log analytics platform
Raw application logs remain in CCP-4; Health & Reliability Monitoring consumes only selected, structured health metrics and events.
Not the policy engine for SLO values
SLO targets and error budget policies are defined in Configuration & Policy Management and consumed here.

4. Scope
4.1 In-Scope
Health model definitions and state machine.
Registry of monitored components (services, agents, jobs, dependencies).
Telemetry ingestion (metrics / health events / probe results).
Health evaluation engine (rules, thresholds, aggregations).
Health roll-up logic (component -> service -> plane -> tenant).
Health APIs for:
Human-facing tools (Tenant Admin, Product Ops).
Agent/gate consumption.
Integration with:
Alerting & Notification Service (EPC-4) for alerts / pages.
ERIS (PM-7) for evidence.
Observability & Reliability Plane for storage and visualisations.
4.2 Out-of-Scope
Building custom dashboards or UIs.
Designing external monitoring backend (Prometheus, OTEL collector variants, etc.) implementation details.
ML-based anomaly detection (future extension; current scope uses rule-based thresholds and simple statistics).

5. Personas & Primary Use Cases
5.1 Personas
ZeroUI SRE / Platform Engineer
Needs: system health overview, error budget burn posture, dependency maps, quick triage.
ZeroUI Product Engineer
Needs: simple way to know if a failure is due to their service vs platform dependencies.
Tenant Admin / Engineering Manager
Needs: high-level reliability view of ZeroUI for their tenant; visibility into outages/degradation.
Agent / Gate (System Actors)
Needs: machine-readable "is it safe to act?" signals to decide whether to proceed, degrade, or abort actions.
5.2 Example Use Cases
UC-1: An Edge Agent on a laptop wants to run a high-risk remediation; it queries Health & Reliability Monitoring, sees Tenant Cloud Detection Engine is DEGRADED, and switches to read-only guidance instead of auto-fix.
UC-2: SRE wants to know if a production incident is due to AI Gateway saturation or a downstream dependency; they query health states and see saturation > 90% and error spikes for the AI Gateway.
UC-3: Tenant Admin wants a 30-day reliability report: % of time Tenant's gates were fully healthy vs degraded vs failed, based on SLO definitions.
UC-4: Deployment module wants to roll out a new release but sees Laptop Plane healthy, Product Cloud healthy, Tenant Cloud degraded, and automatically defers rollout to that tenant.

6. Concepts & Health Model
6.1 Metrics Framework
Health & Reliability Monitoring standardises on three complementary frameworks:
Four Golden Signals - For user-facing or API services:
Latency, Traffic, Errors, Saturation.
RED Method - For microservices endpoints:
Rate (requests/s), Errors, Duration (latency).
USE Method - For resources (CPU, memory, disk, network, GPU, queue):
Utilization, Saturation, Errors per resource.
These are implemented using OTel metrics (counters, histograms, gauges) and correlated to traces/logs where possible.
6.2 Health States
Each component is evaluated into one of:
OK
DEGRADED
FAILED
UNKNOWN (no signal or incomplete telemetry)
Transitions are driven by policy thresholds on the metrics/SLOs, e.g.:
Latency above SLO for a sustained window -> DEGRADED.
Error rate above critical threshold -> FAILED.
No recent heartbeats -> UNKNOWN or FAILED depending on policy.
6.3 Component Types
Service (API / microservice / job)
Agent (Edge Agent on laptop, background worker)
Dependency (database, queue, external API)
Plane (Laptop / Tenant Cloud / Product Cloud / Shared)
Composite Group (e.g., "All detection components for Tenant X")

7. Functional Requirements
FR-1: Monitored Component Registry
Maintain an internal registry of all monitored components with:
component_id, component_type
plane, environment
tenant_scope (per-tenant, global, shared)
dependencies (IDs of components it relies on)
metrics_profile (which metrics apply: Golden Signals, RED, USE)
health_policies (references to SLO/error budget definitions in Config & Policy)
APIs:
POST /v1/health/components - register/update component metadata.
GET /v1/health/components/{component_id} - retrieve definition.
FR-2: Telemetry Ingestion (Health Signals)
Health & Reliability Monitoring must ingest health-related telemetry from:
Metrics pipelines (OTel or equivalent).
Health / status endpoints (HTTP, gRPC, etc.).
Agent heartbeats.
Resource monitors (CPU, memory, disk, GPU, network).
Telemetry types:
Service metrics: request rate, error counts, latency distributions, queue depth, etc.
Resource metrics: CPU/memory utilization, saturation, I/O errors.
Probe results: liveness/readiness/startup type outcomes.
Telemetry must be tagged with:
component_id, plane, environment, tenant_id (if tenant-scoped)
Time, metric name, labels (e.g., endpoint, status code).
FR-3: Health Evaluation Engine
Evaluate raw metrics into health states using:
Policy-driven rules from Configuration & Policy module:
thresholds (e.g., error_rate > X%, latency > Y ms, CPU util > Z%)
time windows (e.g., 5-minute rolling)
aggregation (P95 latency, error proportion, etc.).
SLO definitions & error budgets (from Config & Policy / Gold Standards).
Health evaluation must support anti-flapping behaviour (for example, hysteresis between enter/exit thresholds and minimum time-in-state) configurable via the Configuration & Policy module, so that transient spikes do not cause rapid OK <-> DEGRADED <-> FAILED transitions.
Engine must:
Compute health state, reason code, and supporting metrics snapshot per evaluation cycle.
Support per-component and per-tenant overrides (e.g., stricter SLO in prod vs dev).
FR-4: Heartbeats & Probes
Service probes:
Standardise probe endpoints for components (HTTP or equivalent) that support:
liveness (is process alive / not deadlocked).
readiness (ready to serve traffic; dependencies OK).
startup (initial boot success).
Interpret probe failures into health degradation and restart signals where relevant (e.g., downstream to Kubernetes / orchestrator).
Agent heartbeats:
Edge Agents emit periodic heartbeat messages including:
version, last action timestamp, current load, last error type, environment labels.
Missed heartbeats degrade agent health state according to policy.
FR-5: Health Roll-Up & Dependency Awareness
Compute roll-up health across:
Dependencies: if a component is OK but a critical dependency is FAILED, mark component at least DEGRADED.
Plane: aggregate component health into per-plane status.
Tenant: roll-up health of tenant-scoped components.
Provide configurable aggregation rules (strict vs lenient):
Example: if any critical dependency is FAILED -> component FAILED.
If 20% of agents for a tenant are FAILED, overall tenant agent health is DEGRADED.
FR-6: SLI/SLO Tracking & Error Budget Hooks
For each SLO-configured component:
Compute SLIs (e.g., successful request rate, latency quantiles, uptime) from metrics.
Track SLO conformance over rolling windows.
Track error budget burn rate over time.
Provide API for other modules to query:
Current SLO status (within_budget / breached / approaching).
Burn rate metrics.
FR-7: Health APIs for Humans & Agents
Component Health API
GET /v1/health/components/{component_id}/status
Returns:
state (OK/DEGRADED/FAILED/UNKNOWN)
reason_code
last_updated
selected supporting metrics
SLO_state (if applicable)
Tenant Health API
GET /v1/health/tenants/{tenant_id}
Returns:
Overall state per plane.
counts of OK/DEGRADED/FAILED components.
error budget posture by critical module.
Plane Health API
GET /v1/health/planes/{plane}/{environment}
Gating / Safe-to-Act API
POST /v1/health/check_safe_to_act
Request:
tenant_id, plane, action_type (e.g., auto_remediate, rollout, risky_migration)
Response:
allowed (true/false)
recommended_mode (normal/degraded/read_only)
reason_codes
If the Safe-to-Act API cannot evaluate health because Health & Reliability Monitoring is unavailable or underlying telemetry is stale beyond a configured window, it must return a deterministic degraded/deny answer (for example, allowed=false and recommended_mode=read_only) with an explicit reason code such as health_system_unavailable, so that callers can apply local offline policies.
FR-8: Events & Alerts
Health & Reliability Monitoring must emit health change events:
Component or tenant health state transitions (e.g., OK -> DEGRADED, DEGRADED -> FAILED).
These events are:
Forwarded to Alerting & Notification Service (EPC-4) for routing to humans (pager, email, chat).
Optionally exported as structured logs/metrics for external APM.
FR-9: Evidence & Audit Integration
For important health transitions and SLO breaches:
Emit health receipts into ERIS (PM-7) including:
component_id, old/new state, reason, time, plane, environment, tenant, key metrics snapshots.
Meta-audit:
Access to sensitive health views (e.g., multi-tenant) should emit meta-receipts in ERIS (who accessed what, when).
FR-10: Multi-Tenant Isolation
APIs must enforce IAM-based permissions:
Tenant-scoped actors can view only their tenant's health data.
Product Ops / SRE can view cross-tenant health for operational purposes, subject to audit.
FR-11: Self-Monitoring
Health & Reliability Monitoring itself must expose:
Its own health endpoint (internal).
Telemetry about evaluation delays, queue lengths, rule evaluation errors.
Failures inside Health & Reliability Monitoring must be visible (e.g., UNKNOWN states, stale metrics).

8. Non-Functional Requirements
NFR-1: Reliability
Health & Reliability Monitoring must be at least as reliable as the critical components it monitors:
High availability configuration in the product plane.
Graceful degradation when telemetry is temporarily delayed (e.g., mark health as UNKNOWN with clear reason).
NFR-2: Performance & Overhead
Health evaluation must impose minimal overhead:
Metrics collection uses sampling and aggregation to avoid excessive cost.
Probe intervals and thresholds are tuned to avoid flapping and unnecessary traffic.
NFR-3: Security & Privacy
Health metrics must avoid PII and sensitive content:
Only operational metadata and counters.
APIs and events must be secured via standard authN/authZ.
Cross-tenant aggregation must not leak tenant identifiers inappropriately.
NFR-4: Telemetry Standards & Portability
All metrics and traces must use OpenTelemetry or compatible conventions:
Standard metric types (counters, histograms, gauges).
Resource attributes for service name, version, environment, tenant/plane labels.
Health & Reliability Monitoring must enforce guardrails on metric label cardinality (for example, disallowing high-cardinality labels such as raw user identifiers and capping the number of distinct label values per metric), and any new metric profile must be reviewed against a label budget defined in Configuration & Policy Management.
NFR-5: Observability
Health & Reliability Monitoring must be fully observable:
Own metrics: evaluation time, backlog size, number of components, etc.
Own logs: rule failures, schema mismatches, failed exports.
Traces of key flows: telemetry -> evaluation -> event/alert.

9. Data Model (Conceptual)
9.1 Component
component_id
component_type (service, agent, dependency, plane, group)
plane, environment
tenant_scope (tenant, global, shared)
dependencies (list of component_ids)
metrics_profile (enum/bitmask for GoldenSignals/RED/USE)
policy_refs (SLO/error budget IDs from Config & Policy)
9.2 HealthSnapshot
snapshot_id
component_id
tenant_id (if applicable)
plane, environment
state (OK/DEGRADED/FAILED/UNKNOWN)
reason_code (e.g., error_rate_above_threshold, latency_slo_breach, no_heartbeat)
metrics_summary (small JSON with selected metrics)
slo_state (within_budget, breached, approaching, or none)
health_policy_id or policy_version_ids (identifiers of the health/SLO policy versions used at evaluation time)
created_at
9.3 SLOStatus
component_id
slo_id
window (e.g., 7d, 30d)
sli_values (e.g., availability %, P95 latency)
error_budget_total
error_budget_consumed
burn_rate
(Concrete storage schema left to Contracts & Schema Registry.)

10. Interfaces & APIs (High-Level)
Already outlined under FR-1/2/7; summarised here:
Component Registry
POST /v1/health/components
GET /v1/health/components/{component_id}
Health Status
GET /v1/health/components/{component_id}/status
GET /v1/health/tenants/{tenant_id}
GET /v1/health/planes/{plane}/{environment}
Safe-to-Act
POST /v1/health/check_safe_to_act
SLO Status
GET /v1/health/components/{component_id}/slo
Events Export
Internal bus topic(s) for health-state transitions.
Integration hooks to Alerting & Notification and ERIS.

11. Interactions with Other Modules
Deployment & Infrastructure (EPC-8):
Uses health & SLO status to gate rollouts and rollbacks.
Alerting & Notification Service (EPC-4):
Receives health change events and SLO breaches for paging and notifications.
Evidence & Receipt Indexing Service (PM-7):
Receives health receipts and meta-audit of access.
Budgeting, Rate-Limiting & Cost Observability (EPC-13):
Correlates cost spikes with degraded health (e.g., thrashing).
Signal Ingestion & Normalization (PM-3) & Detection Engine (PM-4):
Use health signals as features or gating inputs.
ZeroUI Agent / Edge Agent:
Uses Safe-to-Act API to choose between normal/degraded/read-only modes.

12. Test Strategy & Implementation Details
12.1 Unit Tests
Health Rule Evaluation
Given metrics where latency > threshold for window -> state changes to DEGRADED.
Given high error rate -> FAILED.
Given missing heartbeats -> UNKNOWN or FAILED per policy.
Roll-Up Logic
Component OK, dependency FAILED -> component DEGRADED/FAILED per aggregation rule.
Various combinations (OK, DEGRADED, FAILED) aggregated to correct plane/tenant health.
SLO & Error Budget
Correct computation of SLI values from time-series data.
Correct burn rate calculation and classification into within/approaching/breached.
API Responses
Health status endpoints return correct states and summaries for different scenarios.
Safe-to-Act API returns allowed=false when critical components are FAILED.
12.2 Component / Integration Tests
IT-1: Telemetry -> Health
Feed synthetic metrics (Golden Signals, RED/USE) into the metrics pipeline.
Verify resulting health states, reasons, and SLO statuses.
IT-2: Probes & Heartbeats
Simulate liveness/readiness probe failures and agent heartbeat gaps.
Confirm expected state transitions and alert events.
IT-3: Cross-Module Interaction
Trigger health degradation and verify:
Alerting module receives events.
ERIS receives health receipts.
Deployment module gates rollouts correctly.
IT-4: Multi-Tenant Isolation
Seed multiple tenants; verify tenant-scoped tokens can see only their data.
12.3 Performance & Load Tests
PT-1: High Metric Volume
Simulate high-volume metrics/heartbeat events.
Confirm evaluation pipeline keeps up and doesn't violate processing SLOs (no unbounded backlog).
PT-2: High Query Rate
Load test health APIs and Safe-to-Act API.
Confirm latency remains within defined SLO for queries.
12.4 Security Tests
ST-1: AuthN/AuthZ
Ensure unauthenticated access is rejected.
Ensure tenant-scoped actors cannot view others' health.
ST-2: Telemetry Taint
Simulate malformed or malicious metric payloads (e.g., extreme values).
Confirm they are validated, rejected, or clamped safely without crashing evaluators.
12.5 Resilience & Chaos Tests
RT-1: Telemetry Outage
Simulate metrics pipeline outage.
Confirm Health & Reliability Monitoring transitions to UNKNOWN where appropriate, with clear reasons.
RT-2: Health & Reliability Monitoring Restart
Restart Health & Reliability Monitoring during load.
Confirm component registry and state are recovered and newly ingested telemetry is evaluated correctly.

13. Acceptance Criteria (Definition of Ready / Done)
Health & Reliability Monitoring - Health & Reliability Monitoring is implementation ready and can be marked Done when:
All Functional Requirements FR-1 through FR-11 are implemented.
At minimum, all P0 modules (Deployment & Infrastructure, Detection Engine Core, LLM Gateway & Safety Enforcement, Signal Ingestion & Normalization, Evidence & Receipt Indexing Service, Identity & Access Management, and the Edge Agent) must be registered in the component registry with defined SLO profiles before declaring Health & Reliability Monitoring Done. "P0" here refers to the foundational modules that hold sequence positions 1-6 in `docs/architecture/Module_Implementation_Prioritization_Reordered.md` (plus EPC-8 as a historical exception) rather than introducing a new prioritization label.
Health states for all registered components (including Edge Agents, critical services, dependencies) are computed and queryable.
Golden Signals / RED / USE-style metrics are ingested and used in evaluation for relevant components.
SLO tracking and error budget hooks are wired, with well-defined APIs and metrics.
Health events and SLO breaches are forwarded to:
Alerting & Notification Service, and
ERIS for evidence.
Safe-to-Act API is integrated into at least one critical gate (e.g., deployment or high-risk agent action) and covered by tests.
Multi-tenant isolation is enforced, tested, and meta-audited.
Health & Reliability Monitoring is fully observable (metrics, logs, traces) and passes resilience tests (telemetry outages, restarts).
This PRD is complete and internally consistent and can be used as the single source of truth for implementing the Health & Reliability Monitoring module in the ZeroUI platform.
