**ZeroUI Observability Layer Architecture Design (Implementation-Ready)**

Aligned to: ZeroUI_Observability_PRD_v0.2

# Document Control

| Version   | v0.1                                                                                                                                                                  |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Status    | Draft - Implementation Design                                                                                                                                         |
| Scope     | Observability Layer architecture to implement PRD v0.2 with schema validation, redaction/minimisation, SLI computation, burn-rate alerts, and challenge traceability. |
| Non-goals | No re-design of product functional modules beyond required telemetry hooks; no vendor-specific tooling assumptions.                                                   |

# ADR Summary

This document specifies the concrete architecture (components, data paths, data contracts, failure modes, and rollout) required to implement the ZeroUI Observability Layer defined in PRD v0.2. The architecture is designed to maximise prevent-first and forecast-first outcomes by making every decision auditable, correlated end-to-end, and measurable through explicit SLIs/SLOs and multi-window burn-rate alerting.

## Key Decisions (ADR)

-   Adopt OpenTelemetry signals (traces, metrics, logs) as the transport and data model, using OTLP for delivery between sources, collectors, and backends.

-   Use W3C Trace Context (traceparent/tracestate) for end-to-end correlation across VS Code extension, Edge Agent, backend services, and CI surfaces.

-   Represent ZeroUI domain events as OTLP Logs (log records) carrying the common envelope (zero_ui.obsv.event.v1) with event-specific payload validated against JSON Schemas (v1).

-   Enforce privacy-by-design: explicit allow-list and deny-list; redaction before export; compute fingerprints after redaction; emit privacy.audit.v1 for relevant workflows.

-   Compute SLIs from deterministic counters/histograms derived from traces and events; drive alerts via multi-window burn-rate rules with configuration-only thresholds (no hardcoded numeric targets).

-   Introduce an agentic Observability Plane (6 agents aligned to PRD components C1-C6) so that telemetry validation, SLI computation, noise control, and forecasting are autonomous but bounded by contracts and human escalation.

# System Context and Data Flow

ZeroUI produces telemetry from multiple execution surfaces (IDE/VS Code extension, Edge Agent, backend services, CI). All telemetry must be correlated by trace_id and must obey the redaction/minimisation contract before leaving the producer. Telemetry is transported via OTLP to the Collector/Normaliser, then routed to storage backends. SLI computation and alerting operate over the stored signals, and forecasting uses SLI/SLO time series to predict time-to-breach and trigger prevent-first escalation.

## High-Level Data Flow

\(1\) Producer (C1) -\> (2) Local Redaction + Schema Precheck -\> (3) OTLP Export  
-\> (4) Collector/Normaliser (C2) Schema Guard + Enrichment + Policy Enforcement  
-\> (5) Storage (C3): Traces / Metrics / Events  
-\> (6) SLI Computation (C4) -\> (7) Alerting + Noise Control (C5) -\> (8) Forecast/Prevent (C6)  
-\> (9) Dashboards + Runbooks + Evidence Packs

# Component and Agent Boundary Map

Each PRD component maps to an implementation agent (or small set of agents) with strict boundaries and data contracts. All agents write receipts (audit-friendly logs) and emit failure telemetry using the required event types.

| PRD Component                           | Implementation Agent                  | Deterministic vs AI                                 | Inputs                         | Outputs                                                     | Primary SLO/Focus                       |
|-----------------------------------------|---------------------------------------|-----------------------------------------------------|--------------------------------|-------------------------------------------------------------|-----------------------------------------|
| C1 Telemetry Instrumentation Layer      | Telemetry Emitter Agent               | Deterministic                                       | Runtime spans + domain signals | OTLP traces/metrics/logs + required events                  | Completeness + redaction compliance     |
| C2 Collector and Normaliser             | Telemetry Contract Guardian Agent     | Deterministic                                       | OTLP input                     | Validated/enriched OTLP routed to stores                    | Ingest success + schema compliance      |
| C3 Storage                              | Telemetry Store Router                | Deterministic                                       | Validated OTLP                 | Trace store, metric store, event store                      | Queryability + retention                |
| C4 Evaluation and Quality Pipeline      | SLI & Evaluation Builder Agent        | Deterministic (core) + Optional AI summarisation    | Events + traces                | Derived metrics, evaluation aggregates, calibration reports | SLI freshness + correctness             |
| C5 Alerting and Noise Control           | Burn-Rate Alert & Noise Control Agent | Deterministic                                       | Derived metrics + alert config | Alerts + alert.noise_control.v1 events                      | Low false positives + actionable alerts |
| C6 Forecasting and Prevent-First Engine | Forecast & Prevent Agent              | Deterministic forecasting + Optional AI explanation | SLI/SLO time series            | Time-to-breach forecasts + escalations                      | Early warning lead time                 |

# Telemetry Data Contracts

All ZeroUI domain events MUST use the common envelope schema (zero_ui.obsv.event.v1) and MUST carry correlation.trace_id. The following 12 event types are the minimum required set and MUST be emitted where applicable.

-   alert.noise_control.v1

-   bias.scan.result.v1

-   error.captured.v1

-   evaluation.result.v1

-   failure.replay.bundle.v1

-   memory.access.v1

-   memory.validation.v1

-   perf.sample.v1

-   privacy.audit.v1

-   prompt.validation.result.v1

-   retrieval.eval.v1

-   user.flag.v1

## Event Transport Mapping (OTLP Logs)

ZeroUI events are transported as OTLP Logs (LogRecords). Each LogRecord MUST include:

-   body: JSON serialisation of the zero_ui.obsv.event.v1 envelope (recommended) OR equivalent attributes + body payload.

-   attributes: event_type, source.component, source.channel, correlation.trace_id, correlation.span_id (if available), event_id.

-   severity: mapped to OTLP severity.

-   timestamp: event_time.

# Privacy, Redaction, and Minimisation Enforcement

Redaction is enforced twice: (1) in-producer before export (mandatory), and (2) in Collector/Normaliser as a safety net. Producers MUST compute fingerprints after redaction and MUST set redaction_applied=true. Telemetry that violates the deny list is dropped or quarantined (depending on environment).

## Redaction Control Points

Producer (Edge/Extension/Backend)  
- redact(raw) -\> redacted  
- fingerprint(redacted) -\> message_fingerprint/input_fingerprint/...  
- validate(payload schema) -\> pass/fail  
- export(OTLP)  
Collector/Normaliser  
- schema_guard  
- denylist_filter  
- attribute_sanitise  
- route/export

# Collector/Normaliser Blueprint (OTel Collector)

Collector configuration uses pipelines of receivers, processors, exporters, and connectors. The blueprint below is vendor-agnostic and can be deployed as a scalable fleet. The Schema Guard may be implemented as a custom processor or as a sidecar validation service.

receivers:  
otlp:  
protocols:  
grpc:  
http:  
  
processors:  
memory_limiter: {}  
batch: {}  
attributes_enrich: { \# add standard resource/tenant/version dims }  
transform_sanitise: { \# strip/normalise fields }  
filter_denylist: { \# drop forbidden content }  
schema_guard: { \# validate zero_ui.obsv.event.v1 + payload schemas }  
  
exporters:  
traces_backend: { \# OTLP exporter }  
metrics_backend: { \# OTLP exporter }  
events_backend: { \# OTLP exporter or log exporter }  
  
service:  
pipelines:  
traces: { receivers: \[otlp\], processors: \[memory_limiter,batch,attributes_enrich\], exporters: \[traces_backend\] }  
metrics: { receivers: \[otlp\], processors: \[memory_limiter,batch,attributes_enrich\], exporters: \[metrics_backend\] }  
logs/events:  
{ receivers: \[otlp\], processors: \[memory_limiter,schema_guard,filter_denylist,transform_sanitise,batch,attributes_enrich\], exporters: \[events_backend\] }

# SLI Computation Architecture

SLIs are computed by converting events/spans into monotonic counters and latency distributions. The SLI & Evaluation Builder Agent produces these derived metrics in the metric store and documents the exact numerator/denominator sources. Burn-rate alerting and forecasting consume the derived metrics.

## Extracted SLI Definitions (from PRD v0.2)

| SLI ID | Name                             | Numerator                                                                             | Denominator                         | Event/Source                                                                                          | Notes                                         |
|--------|----------------------------------|---------------------------------------------------------------------------------------|-------------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| SLI-A  | End-to-End Decision Success Rate | successful_runs                                                                       | total_runs                          | Source: root spans in traces. Count root spans with attribute run_outcome=success vs all root spans.  | Group by component and channel.               |
| SLI-B  | End-to-End Latency               | latency_ms (distribution)                                                             | n/a                                 | Source: root span duration OR perf.sample.v1 where operation=decision. Compute p50/p95/p99.           | Group by component and channel.               |
| SLI-C  | Error Capture Coverage           | count(error.captured.v1 with required fields present)                                 | count(root spans with status=error) | Source: error.captured.v1 + trace root spans. Coverage = emitted_contextual_errors / total_errors.    | Group by error_class, component, channel.     |
| SLI-D  | Prompt Validation Pass Rate      | count(prompt.validation.result.v1 status=pass)                                        | count(prompt.validation.result.v1)  | Source: prompt.validation.result.v1.                                                                  | Group by prompt_id and prompt_version.        |
| SLI-E  | Retrieval Compliance             | count(retrieval.eval.v1 where relevance_compliant=true AND timeliness_compliant=true) | count(retrieval.eval.v1)            | Source: retrieval.eval.v1.                                                                            | Group by corpus_id, component, channel.       |
| SLI-F  | Evaluation Quality Signal        | user_flags + score_distribution                                                       | n/a                                 | Source: evaluation.result.v1 (metrics) and user.flag.v1. Track score distribution and user flag rate. | Group by channel, component, eval_suite_id.   |
| SLI-G  | False Positive Rate (FPR)        | false_positive                                                                        | false_positive + true_positive      | Source: alert.noise_control.v1 enriched by human validation outcomes where applicable.                | Group by detector type and alert_fingerprint. |

# Alerting Architecture (Multi-Window Burn-Rate + Noise Control)

Alerts are derived from SLO error budgets using multi-window burn-rate logic. Thresholds and window durations are supplied by configuration objects (zero_ui.alert_config.v1). Alert noise control is enforced via deduplication, rate limiting, prioritisation, and human validation outcomes recorded in alert.noise_control.v1.

## Alert Rule Template (Pseudo-Logic)

Given SLO with objective S and error_budget = 1 - S  
Compute burn_rate(window) = (error_rate(window) / error_budget)  
FAST alert when burn_rate(short) \> fast AND burn_rate(mid) \> fast_confirm  
SLOW alert when burn_rate(mid) \> slow AND burn_rate(long) \> slow_confirm  
Apply min_traffic gate. Deduplicate by alert_fingerprint. Emit alert.noise_control.v1 for every suppression/merge.

# Forecasting and Prevent-First Engine

Forecasting uses SLI and burn-rate time series to estimate time-to-breach (TTB) for each SLO and to surface leading indicators (increasing latency p95, rising error capture gaps, rising bias signals, rising user flags). Prevent-first actions are limited to safe escalation paths: create tickets, request human validation, or reduce autonomy levels (e.g., gate mode changes) as governed by policy.

# Contract Test Plan (Implementation Gate)

**CT-1 Schema Conformance (producer):** For each required event type, emit a valid payload and an invalid payload. Expect valid passes local validator; invalid is rejected and produces error.captured.v1 with error_class=architecture and stage=telemetry_emit.

**CT-2 Redaction Guarantee:** Attempt to include denylisted raw input/output. Expect exporter to drop raw fields, set redaction_applied=true, and compute fingerprints after redaction. Collector denylist_filter must also block if raw fields appear.

**CT-3 Correlation Propagation:** Create a synthetic end-to-end run spanning IDE -\> Edge Agent -\> Backend. Verify a single trace_id links root span, events, and derived metrics.

**CT-4 SLI Metric Correctness:** Replay a fixed set of events/spans. Verify derived counters and p95/p99 latency match the SLI table definitions.

**CT-5 Multi-Window Burn Rate Alerting:** Simulate error-rate steps. Verify FAST and SLOW alerts trigger only when both windows exceed thresholds, and suppress duplicates.

**CT-6 Noise Control and FPR accounting:** Generate repeated near-identical alerts. Expect dedup + rate limiting; alert.noise_control.v1 emitted with suppression_reason; FPR tracked when human validation marks false_positive.

**CT-7 Replay Bundle Minimalism:** Generate failure.replay.bundle.v1 and verify it contains only fingerprints, IDs, and allowlisted metadata (no raw content).

# Phased Rollout Plan (No Hardcoded Thresholds)

**Phase 0 - Foundations:** Ship contract libraries (schemas + redaction), trace context propagation, and collector in dev/staging. All alerts disabled.

**Phase 1 - Signal Coverage:** Instrument all components to emit the 12 required event types. Enable dashboards. Alerts in ticket-only mode.

**Phase 2 - SLI/SLO Calibration:** Validate SLI correctness, establish baselines, configure SLO targets and burn-rate thresholds per environment. Start paging only for high-confidence conditions.

**Phase 3 - Forecast + Prevent-First:** Enable time-to-breach forecasts and safe prevent-first escalations (HITL validation requests, risk escalation). Expand to more channels/tenants via canary.

**Phase 4 - Optimisation:** Tune noise control, improve coverage, enforce governance reporting cadence, and automate replay bundles for top incident classes.

# Appendix: Challenge Traceability Matrix (from PRD v0.2)

| Challenge                                        | Signals (Events/Traces)                                                               | Dashboards    | Alerts                           | Acceptance Tests |
|--------------------------------------------------|---------------------------------------------------------------------------------------|---------------|----------------------------------|------------------|
| 1\. LLM Error Analysis Challenges                | error.captured.v1; trace root spans (status=error)                                    | D2            | A3; A1                           | AT-1             |
| 2\. System Prompt Optimization Challenges        | prompt.validation.result.v1                                                           | D3            | N/A                              | AT-2             |
| 3\. Memory Management Challenges                 | memory.access.v1; memory.validation.v1                                                | D4            | N/A                              | N/A              |
| 4\. Response Evaluation Challenges               | evaluation.result.v1; user.flag.v1                                                    | D5            | A5                               | N/A              |
| 5\. Prompt Bias Challenges                       | bias.scan.result.v1                                                                   | D6            | A6                               | AT-7             |
| 6\. Prompt Response Bias Challenges              | bias.scan.result.v1; evaluation.result.v1; user.flag.v1                               | D6; D5        | A6; A5                           | AT-7             |
| 7\. Emergent Interaction Effects                 | trace spans for dependency/feedback indicators; error.captured.v1 (secondary)         | D7            | N/A                              | N/A              |
| 8\. Agent Evaluation Frameworks Challenges       | evaluation.result.v1; user.flag.v1                                                    | D5            | A5                               | N/A              |
| 9\. LLM-as-Judge Patterns Challenges             | evaluation.result.v1 (judge_type); user.flag.v1                                       | D5            | A5                               | AT-7             |
| 10\. Retrieval Evaluation Challenges             | retrieval.eval.v1                                                                     | D9            | A4                               | AT-3             |
| 11\. Failure Analysis Challenges                 | failure.replay.bundle.v1; error.captured.v1                                           | D10; D2       | A1; A3                           | AT-4; AT-1       |
| 12\. Production-Grade Thinking Challenges        | perf.sample.v1; alert.noise_control.v1                                                | D11; D12; D15 | A1; A2; A7                       | AT-6             |
| 13\. Continuous Model Adaptation and Fine-Tuning | evaluation.result.v1 (time series by version); user.flag.v1                           | D5; D11       | N/A                              | N/A              |
| 14\. Cross-Domain Knowledge Integration          | retrieval.eval.v1 (corpus_id); memory.access.v1                                       | D9; D4        | A4 (if retrieval non-compliance) | AT-3             |
| 15\. System Transparency and Explainability      | error.captured.v1 (reason codes); evaluation.result.v1 (judge rationale fingerprints) | D2; D5        | N/A                              | AT-1             |
| 16\. Latency and Performance Optimization        | perf.sample.v1                                                                        | D12; D1       | A2                               | N/A              |
| 17\. Adaptation to Multi-Agent Interactions      | trace spans for coordination/conflict indicators                                      | D8            | N/A                              | AT-7             |
| 18\. User Privacy and Data Security              | privacy.audit.v1                                                                      | D13           | N/A                              | AT-5             |
| 19\. Multi-Modal and Cross-Channel Interactions  | perf.sample.v1; evaluation.result.v1 by channel                                       | D14; D12      | A2 (if latency regression)       | N/A              |
| 20\. Handling False Positives                    | alert.noise_control.v1; evaluation.result.v1 (human validation)                       | D15           | A7                               | AT-6; AT-7       |

# Appendix: External Standards and References

-   OpenTelemetry Collector Architecture (pipelines, receivers/processors/exporters): https://opentelemetry.io/docs/collector/architecture/

-   OpenTelemetry Collector Configuration (receivers/processors/exporters/connectors): https://opentelemetry.io/docs/collector/configuration/

-   OTLP Specification (encoding/transport/delivery for traces, metrics, logs): https://opentelemetry.io/docs/specs/otlp/

-   OTLP Exporter behaviour (retries/config): https://opentelemetry.io/docs/specs/otel/protocol/exporter/

-   W3C Trace Context (traceparent/tracestate) and Trace Context Level 2: https://www.w3.org/TR/trace-context/ ; https://www.w3.org/TR/trace-context-2/

-   Google SRE Workbook - Alerting on SLOs (multi-window burn-rate): https://sre.google/workbook/alerting-on-slos/

-   Google SRE Workbook - Monitoring (use counters as basis for burn-rate alerting): https://sre.google/workbook/monitoring/
