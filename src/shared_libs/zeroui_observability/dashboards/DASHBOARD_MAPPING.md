# ZeroUI Observability Layer - Dashboard Mapping

## Overview

This document maps each dashboard (D1-D15) to SLIs, event sources, and data sources per PRD Section 6.

## Dashboard Definitions

### D1: System Health (Golden Signals)

**Purpose**: Latency/traffic/errors/saturation by channel/component

**SLIs**: SLI-A (Success Rate), SLI-B (Latency)

**Event Sources**:
- `perf.sample.v1` (latency)
- Root spans (traffic, errors)
- `error.captured.v1` (errors)

**Panels**:
- Request rate (traffic)
- Error rate
- Latency (p50/p95/p99)
- Saturation indicators

**Grouping**: `component`, `channel`

**Refresh Interval**: 30 seconds

**Retention**: 30 days

---

### D2: Error Analysis and Debug

**Purpose**: Error clusters, classification, top traces, contextual coverage

**SLIs**: SLI-C (Error Capture Coverage)

**Event Sources**:
- `error.captured.v1`
- Trace root spans with `status=error`

**Panels**:
- Error rate by error_class
- Error capture coverage (SLI-C)
- Top error traces
- Error classification breakdown

**Grouping**: `error_class`, `component`, `channel`

**Refresh Interval**: 1 minute

**Retention**: 90 days

---

### D3: Prompt Quality and Regression

**Purpose**: Prompt validation pass rate, edge-case failures, version comparisons

**SLIs**: SLI-D (Prompt Validation Pass Rate)

**Event Sources**:
- `prompt.validation.result.v1`

**Panels**:
- Prompt validation pass rate (SLI-D)
- Pass rate by prompt_version
- Edge case failures
- Version comparison

**Grouping**: `prompt_id`, `prompt_version`

**Refresh Interval**: 5 minutes

**Retention**: 180 days

---

### D4: Memory Health

**Purpose**: Memory access logs, discards/overwrites, validation failures

**Event Sources**:
- `memory.access.v1`
- `memory.validation.v1`

**Panels**:
- Memory access patterns
- Memory validation status
- Discard/overwrite rates
- Window overflow indicators

**Grouping**: `memory_store_id`, `component`, `channel`

**Refresh Interval**: 1 minute

**Retention**: 30 days

---

### D5: Response Evaluation Quality

**Purpose**: Automated eval metrics + user flag trends

**SLIs**: SLI-F (Evaluation Quality Signal)

**Event Sources**:
- `evaluation.result.v1`
- `user.flag.v1`

**Panels**:
- Evaluation score distribution (SLI-F)
- User flag rate
- Score trends over time
- Flag breakdown by type

**Grouping**: `channel`, `component`, `eval_suite_id`

**Refresh Interval**: 5 minutes

**Retention**: 90 days

---

### D6: Bias Monitoring

**Purpose**: Bias detector results, counterfactual/adversarial outcomes, audit queue

**Event Sources**:
- `bias.scan.result.v1`

**Panels**:
- Bias detection results
- Bias category breakdown
- Confidence distribution
- Audit queue status

**Grouping**: `bias_category`, `component`, `channel`

**Refresh Interval**: 5 minutes

**Retention**: 180 days

---

### D7: Emergent Interaction and Fail-Safe

**Purpose**: Dependency indicators, stress test outcomes, isolation/reset activations

**Event Sources**:
- Trace spans for dependency/feedback indicators
- `error.captured.v1` (secondary)

**Panels**:
- Dependency graph indicators
- Stress test outcomes
- Isolation/reset activations
- Interaction patterns

**Grouping**: `component`, `channel`

**Refresh Interval**: 1 minute

**Retention**: 30 days

---

### D8: Multi-Agent Coordination

**Purpose**: Conflict rates, coordination protocol events, simulation outcomes

**Event Sources**:
- Trace spans for coordination/conflict indicators

**Panels**:
- Conflict rate
- Coordination protocol events
- Simulation outcomes
- Agent interaction patterns

**Grouping**: `component`, `channel`

**Refresh Interval**: 1 minute

**Retention**: 30 days

---

### D9: Retrieval Evaluation

**Purpose**: Relevance/timeliness compliance, with/without retrieval benchmark results

**SLIs**: SLI-E (Retrieval Compliance)

**Event Sources**:
- `retrieval.eval.v1`

**Panels**:
- Retrieval compliance (SLI-E)
- Relevance score distribution
- Timeliness score distribution
- Compliance by corpus_id

**Grouping**: `corpus_id`, `component`, `channel`

**Refresh Interval**: 5 minutes

**Retention**: 90 days

---

### D10: Failure Analysis and Replay

**Purpose**: Root cause tags, replay bundle explorer, post-failure analytics

**Event Sources**:
- `failure.replay.bundle.v1`
- `error.captured.v1`

**Panels**:
- Failure replay bundles
- Root cause analysis
- Post-failure analytics
- Replay bundle explorer

**Grouping**: `error_class`, `component`, `channel`

**Refresh Interval**: 1 minute

**Retention**: 180 days

---

### D11: Production Readiness and Rollout Safety

**Purpose**: Versioning/rollback signals, incremental rollout status

**Event Sources**:
- `evaluation.result.v1` (time series by version)
- `user.flag.v1`

**Panels**:
- Version rollout status
- Rollback signals
- Incremental rollout progress
- Version comparison

**Grouping**: `component`, `channel`, `version`

**Refresh Interval**: 5 minutes

**Retention**: 90 days

---

### D12: Performance Under Load

**Purpose**: Cache indicators, async indicators, RAG latency breakdown

**Event Sources**:
- `perf.sample.v1`

**Panels**:
- Cache hit rate
- Async path indicators
- RAG latency breakdown
- Queue depth

**Grouping**: `component`, `channel`, `operation`

**Refresh Interval**: 30 seconds

**Retention**: 30 days

---

### D13: Privacy and Compliance Audit

**Purpose**: Audit events for data handling, encryption/access control signals

**Event Sources**:
- `privacy.audit.v1`

**Panels**:
- Privacy audit events
- Encryption status (in-transit, at-rest)
- Access control enforcement
- Compliance status

**Grouping**: `component`, `channel`, `operation`

**Refresh Interval**: 5 minutes

**Retention**: 365 days (compliance requirement)

---

### D14: Cross-Channel Consistency

**Purpose**: Consistency signals across supported interfaces

**Event Sources**:
- `perf.sample.v1`
- `evaluation.result.v1` by channel

**Panels**:
- Cross-channel latency comparison
- Consistency indicators
- Channel-specific metrics
- Consistency trends

**Grouping**: `channel`, `component`

**Refresh Interval**: 5 minutes

**Retention**: 30 days

---

### D15: False Positive Control Room

**Purpose**: Alert volume, dedup/rate-limit outcomes, FPR trends, confidence distribution

**SLIs**: SLI-G (False Positive Rate)

**Event Sources**:
- `alert.noise_control.v1`
- `evaluation.result.v1` (human validation)

**Panels**:
- Alert volume
- False positive rate (SLI-G)
- Dedup/rate-limit outcomes
- Confidence distribution

**Grouping**: `detector_type`, `alert_fingerprint`

**Refresh Interval**: 1 minute

**Retention**: 90 days

---

## Drill-Down Support

All dashboards support drill-down via `trace_id`:

- Click on any metric/panel → View trace details
- Filter by `trace_id` → Show all events/spans for that trace
- Link to failure replay bundles (D10)

## Configuration

**No Hardcoded Thresholds**: All thresholds come from:
- Environment variables
- Configuration files
- Policy settings

**Example**:
```yaml
thresholds:
  error_rate_warning: ${ERROR_RATE_WARNING_THRESHOLD:0.01}
  error_rate_critical: ${ERROR_RATE_CRITICAL_THRESHOLD:0.05}
```

## References

- PRD Section 6: Dashboards
- Architecture Document: Dashboard definitions
- SLI Formulas: `src/shared_libs/zeroui_observability/sli/SLI_FORMULAS.md`
