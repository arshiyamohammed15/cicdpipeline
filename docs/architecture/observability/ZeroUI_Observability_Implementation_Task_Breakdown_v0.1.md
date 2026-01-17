# ZeroUI Observability Layer - Implementation Task Breakdown

Version: v0.1

## Document Control

| System      | ZeroUI (100% Agentic AI System)                                                                                                       |
|-------------|---------------------------------------------------------------------------------------------------------------------------------------|
| Scope       | Observability Layer implementation tasks (contracts, telemetry pipeline, SLIs/SLOs, dashboards, alerting, runbooks, acceptance tests) |
| Source      | ZeroUI Observability PRD v0.2 (internal attachment) + Web standards referenced below                                                  |
| Quality Bar | Deterministic-first, auditable, low false positives, minimal assumptions                                                              |

## ADR Summary (Locked Decisions)

-   Use OpenTelemetry data model and OTLP for telemetry export and collection (vendor-neutral).

-   Use OpenTelemetry Collector pipelines (receivers, processors, exporters) to receive, process, and export telemetry.

-   Use W3C Trace Context (traceparent, tracestate) for end-to-end correlation across boundaries.

-   Use multi-window, multi-burn-rate SLO alerting for reliability alerts, with ticket-first rollout and calibrated paging.

-   Enforce telemetry contracts: common envelope + per-event payload schemas + redaction allow/deny rules.

## Implementation Principles (Non-negotiable)

-   Do not block IDE UI thread; telemetry emission must be async/non-blocking on the IDE surface.

-   No raw secrets / code content egress by default; apply redaction and minimisation before export.

-   Every privileged or high-stakes decision must produce an immutable receipt ID and link to trace_id/run_id.

-   Every task must include: (a) deliverables, (b) acceptance criteria, (c) tests, (d) rollback plan.

## Phased Rollout Plan (Minimum viable sequence)

-   Phase 0 - Contracts & Correlation: event envelope, per-event schemas, redaction rules, trace propagation.

-   Phase 1 - Telemetry Backbone: Collector pipeline, storage adapters, baseline dashboards, SLI calculators.

-   Phase 2 - Alerting & Noise Control: burn-rate alert engine, dedup/rate-limit, ticket-mode operations.

-   Phase 3 - Forecast & Prevent-First: time-to-breach signals, prevent-first actions (safe-mode, routing).

-   Phase 4 - Replay & Continuous Improvement: replay bundles, post-incident learning loops, calibration.

## Task Breakdown (Patch-style microtasks)

Each task is designed to be small and non-breaking. IDs are stable. Use feature flags for rollout and keep defaults safe (ticket-only).

| ID     | Title                                                                           | Component / Agent                | Scope                                                                                                    | Deliverables                                                                            | Acceptance Criteria                                                                                     | Tests                                                                             | Dependencies   |
|--------|---------------------------------------------------------------------------------|----------------------------------|----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|----------------|
| OBS-00 | Define Telemetry Envelope and 12 Event Types (v1)                               | Telemetry Contract (C1/C2)       | Define stable naming, required fields, enums, and versioning rules.                                      | Telemetry spec markdown + JSON Schema for envelope + list of 12 event type identifiers. | Envelope schema validates; event type list is fixed; versioning rules documented.                       | Schema unit tests (valid/invalid examples) executed locally in CI.                | None           |
| OBS-01 | Write Payload JSON Schemas for 12 Required Event Types                          | Schema Library (C2)              | Create one schema per event type with required payload fields; include redaction flags.                  | 12 JSON Schema files + example payload fixtures.                                        | All schemas compile; fixtures validate; missing required fields fail.                                   | Automated schema validation test suite; negative tests for deny-listed fields.    | OBS-00         |
| OBS-02 | Define Redaction / Minimisation Policy (Allow/Deny) and Tests                   | Privacy Guard (C2)               | Explicit allow-list fields; deny-list patterns (secrets/PII); hashing rules.                             | Redaction policy doc + deny-list patterns + redaction test fixtures.                    | Any deny-listed content is blocked or redacted according to rule; policy versioned.                     | Fixture-driven tests: pass cases (metadata-only) and fail cases (raw secrets).    | OBS-00         |
| OBS-03 | Trace Context Propagation Contract (IDE -\> Edge -\> Backend -\> CI)            | Correlation (C1)                 | Define propagation rules for traceparent/tracestate and required correlation fields in logs/events.      | Propagation spec + example headers for HTTP and message-based flows.                    | A single run produces a single trace_id across boundaries; logs include TraceId/SpanId where supported. | Integration test: emit synthetic run across surfaces; verify same trace_id.       | OBS-00         |
| OBS-04 | Collector Pipeline Blueprint (OTLP receiver -\> validate -\> enrich -\> export) | Collector/Normaliser (C2)        | Create collector config template with clear extension points for processors/exporters.                   | Collector config template + deployment notes + local dev run steps.                     | Collector starts; receives OTLP; rejects invalid schemas; exports valid telemetry.                      | Contract test harness sending valid/invalid OTLP payloads.                        | OBS-01, OBS-02 |
| OBS-05 | Schema Guard Service/Agent (Deterministic) in Collector Path                    | Telemetry Contract Enforcer (C2) | Implement schema validation step (envelope + payload schemas) with metrics for rejects.                  | Validation processor/service + reject counters + sampling policy for invalid events.    | Invalid events are rejected with reason_code; valid events pass; reject rate visible in metrics.        | Unit tests for validator; integration tests with collector template.              | OBS-04         |
| OBS-06 | Privacy Guard Enforcement (Deterministic) in Collector Path                     | Privacy Guard (C2)               | Apply allow/deny rules and verify redaction_applied field; reject unsafe payloads.                       | Redaction/deny enforcement processor + audit events for violations.                     | Any deny-listed data is blocked; privacy audit event emitted; policy version captured.                  | Fixture tests; integration test with schema guard + collector.                    | OBS-02, OBS-04 |
| OBS-07 | Baseline Telemetry Emission (IDE, Edge, Backend)                                | Instrumentation (C1)             | Add minimal OTLP exporters and correlation fields; emit perf.sample and error.captured events.           | Instrumentation wrappers + feature flag + sample emissions.                             | Telemetry emitted asynchronously; does not block UI; events appear in collector.                        | Smoke test per surface; verify trace_id present; verify schema validation passes. | OBS-03, OBS-04 |
| OBS-08 | SLI Computation Library (Explicit Numerators/Denominators)                      | Evaluation/SLI (C4)              | Implement SLI formulas exactly (counters from specified event sources).                                  | SLI calculator module + documented formulas + unit tests.                               | Given fixtures, SLI values match expected; missing data handled deterministically.                      | Fixture-driven unit tests; property tests for edge cases (zero traffic).          | OBS-01         |
| OBS-09 | Dashboards D1-D15 (Skeleton first, then populated)                              | Dashboards (Views)               | Create dashboards with placeholders wired to SLIs and key metrics; no thresholds hardcoded.              | Dashboard definitions (exportable JSON/YAML) + README mapping to SLIs.                  | Dashboards load; panels show data; drill-down via trace_id works.                                       | Dashboard smoke checks; manual QA checklist.                                      | OBS-07, OBS-08 |
| OBS-10 | Alert Config Contract + Loader (zero_ui.alert_config.v1)                        | Alerting (C5)                    | Implement config schema and loader; validate burn-rate windows and min-traffic rules.                    | Config JSON Schema + loader + default ticket-only config examples.                      | Invalid configs rejected; valid configs load; runtime reload supported.                                 | Config schema tests + hot-reload test.                                            | OBS-00         |
| OBS-11 | Burn-rate Alert Engine (Multi-window) - Ticket Mode                             | Alerting (C5)                    | Evaluate burn rates over configured windows; generate alert events; route to ticketing stub.             | Alert evaluator + alert event schema + ticket routing adapter stub.                     | Alerts fire only when both windows breach; low-traffic suppress works; no paging yet.                   | Synthetic time-series tests covering fast/slow burns; suppression tests.          | OBS-08, OBS-10 |
| OBS-12 | Noise Control (Dedup, Rate-limit, Suppression) + FPR SLI                        | Noise Control Agent (C5)         | Fingerprint alerts; dedup; rate-limit; measure false positive rate from feedback loops.                  | Noise-control processor + alert.noise_control events + FPR dashboard panel.             | Alert floods are suppressed; dedup works; noise metrics visible.                                        | Replay tests with duplicate alerts; rate-limit tests.                             | OBS-11         |
| OBS-13 | Forecast Signals (Time-to-breach, leading indicators) - Read-only               | Forecast Engine (C6)             | Compute time-to-breach using burn rate trends; publish forecast events; no auto-actions yet.             | forecast.signal.v1 schema + forecast calculator + dashboard panels.                     | Forecast outputs produced deterministically; units and horizons documented; no false actioning.         | Backtest on synthetic series; regression tests.                                   | OBS-08         |
| OBS-14 | Prevent-First Actions (Safe-mode / Routing) - Guarded by confidence gate        | Prevent-first Engine (C6)        | Define allowed actions and permissions; execute only when config confidence gate passes.                 | Action policy + action executor stubs + audit receipts for actions.                     | Actions never trigger without explicit enable; every action emits receipt_id + trace link.              | Permission tests; disabled-by-default tests; audit trail tests.                   | OBS-10, OBS-13 |
| OBS-15 | Failure Replay Bundle Builder (Deterministic)                                   | Replay (C6)                      | Build replay bundles referencing trace spans + events (no raw sensitive content).                        | failure.replay.bundle.v1 schema + builder + storage path.                               | Given trace_id/run_id, bundle can be constructed; bundle includes only allowed fields.                  | Fixture tests; redaction compliance tests.                                        | OBS-06, OBS-07 | ✅ COMPLETE |
| OBS-16 | Runbooks RB-1..RB-5 + On-call Playbook (Implementation)                         | Operations                       | Turn PRD runbooks into step-by-step procedures with validation checks and rollback steps.                | Runbook docs + command snippets + decision tree for false positives.                    | Each runbook has: triage, verify, mitigate, rollback, and post-incident actions.                        | Tabletop exercise checklist; dry-run verification steps.                          | OBS-09, OBS-11 | ✅ COMPLETE |
| OBS-17 | Acceptance Tests AT-1..AT-7 - Automation Harness                                | Testing                          | Create automated tests for schema validation, redaction, correlation, SLIs, alerts, forecasting, replay. | Test harness + CI job definitions.                                                      | All acceptance tests green; failures produce clear diagnostics and trace links.                         | AT-1..AT-7 automated + nightly synthetic checks.                                  | OBS-01..OBS-15 | ✅ COMPLETE |
| OBS-18 | Challenge Traceability Gates (20-row matrix enforced)                           | Governance                       | Validate that every challenge row has signal + dashboard + test; fail CI if missing.                     | Traceability matrix file + CI validator.                                                | CI fails if any challenge row lacks required mappings; matrix versioned.                                | Unit tests for validator; sample failing matrix tests.                            | OBS-09, OBS-17 | ✅ COMPLETE |

## Contract Test Plan (Must pass before enabling paging/actions)

### CT-1 Schema Validation

-   Validate envelope schema for every event.

-   Validate payload schema for each of the 12 event types.

-   Negative tests: missing required fields, wrong enum values, wrong types.

### CT-2 Redaction / Minimisation

-   Deny-list detection triggers block or redaction according to rule.

-   Allow-list enforcement: only approved fields are exported.

-   Audit event emitted for every block/redaction decision.

### CT-3 Correlation Propagation

-   Given a synthetic request, verify trace_id is identical across IDE -\> Edge -\> Backend -\> CI boundary.

-   Verify logs include TraceId and SpanId when supported by runtime/SDK.

### CT-4 SLI Computation

-   Verify numerator/denominator counters from specified sources.

-   Verify deterministic behaviour for zero traffic and missing data.

### CT-5 Burn-rate Alerts (Multi-window)

-   Alerts fire only when both fast and confirm windows exceed threshold.

-   Low-traffic suppression works as per min_traffic rules.

-   Ticket-mode routing only (paging disabled by default).

### CT-6 Forecast Signals

-   Time-to-breach computed deterministically from burn-rate trend inputs.

-   Forecast outputs include horizon, units, and confidence fields.

### CT-7 Replay Bundle

-   Replay bundle can be built from trace_id/run_id and contains only allowed metadata.

-   Bundle references event_ids and span_ids for drill-down.

## References (Standards and Guidance)

-   OpenTelemetry Collector Architecture: https://opentelemetry.io/docs/collector/architecture/

-   OpenTelemetry Collector Configuration: https://opentelemetry.io/docs/collector/configuration/

-   W3C Trace Context: https://www.w3.org/TR/trace-context/ (and Trace Context Level 2)

-   Google SRE Workbook - Alerting on SLOs (multi-window burn-rate): https://sre.google/workbook/alerting-on-slos/

-   OpenTelemetry Logs Specification (TraceId/SpanId correlation): https://opentelemetry.io/docs/specs/otel/logs/
