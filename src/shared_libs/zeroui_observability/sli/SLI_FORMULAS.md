# ZeroUI Observability Layer - SLI Formulas

## Overview

This document defines the exact formulas for all 7 SLIs (Service Level Indicators) implemented in the ZeroUI Observability Layer.

**Source**: PRD Section 5.1 and Architecture Document Section "SLI Computation Architecture"

## SLI-A: End-to-End Decision Success Rate

**Formula**: `successful_runs / total_runs`

**Numerator**: Count of root spans with attribute `run_outcome=success`

**Denominator**: Count of all root spans

**Source**: Root spans in traces

**Grouping**: `component`, `channel`

**Edge Cases**:
- Zero traffic: Returns `0.0` with `zero_traffic: true` metadata
- Missing `run_outcome`: Treated as non-success

**Example**:
```
total_runs = 100
successful_runs = 95
SLI-A = 95 / 100 = 0.95 (95%)
```

## SLI-B: End-to-End Latency

**Formula**: `p50/p95/p99 decision latency`

**Source**: 
- Root span duration (from traces)
- `perf.sample.v1` events where `operation=decision`

**Grouping**: `component`, `channel`

**Output**: Distribution metrics (p50, p95, p99, mean, min, max)

**Edge Cases**:
- Zero traffic: Returns `0.0` for all percentiles
- Missing duration: Skipped

**Example**:
```
latencies = [100, 120, 150, 200, 250] ms
p50 = 150 ms
p95 = 250 ms
p99 = 250 ms
```

## SLI-C: Error Capture Coverage

**Formula**: `count(error.captured.v1 with required fields) / count(root spans with status=error)`

**Numerator**: Count of `error.captured.v1` events with all required fields:
- `error_class`
- `error_code`
- `stage`
- `message_fingerprint`
- `input_fingerprint`
- `output_fingerprint`
- `internal_state_fingerprint`

**Denominator**: Count of root spans with `status=error`

**Source**: 
- `error.captured.v1` events
- Trace root spans

**Grouping**: `error_class`, `component`, `channel`

**Edge Cases**:
- Zero traffic: Returns `0.0` with `zero_traffic: true`
- Missing required fields: Not counted in numerator

**Example**:
```
total_errors = 50
captured_errors = 45
SLI-C = 45 / 50 = 0.90 (90% coverage)
```

## SLI-D: Prompt Validation Pass Rate

**Formula**: `count(prompt.validation.result.v1 status=pass) / count(prompt.validation.result.v1)`

**Numerator**: Count of `prompt.validation.result.v1` events with `status=pass`

**Denominator**: Count of all `prompt.validation.result.v1` events

**Source**: `prompt.validation.result.v1` events

**Grouping**: `prompt_id`, `prompt_version`

**Edge Cases**:
- Zero traffic: Returns `0.0` with `zero_traffic: true`
- Missing status: Not counted

**Example**:
```
total_validations = 200
pass_validations = 190
SLI-D = 190 / 200 = 0.95 (95% pass rate)
```

## SLI-E: Retrieval Compliance

**Formula**: `count(retrieval.eval.v1 where relevance_compliant=true AND timeliness_compliant=true) / count(retrieval.eval.v1)`

**Numerator**: Count of `retrieval.eval.v1` events where both `relevance_compliant=true` AND `timeliness_compliant=true`

**Denominator**: Count of all `retrieval.eval.v1` events

**Source**: `retrieval.eval.v1` events

**Grouping**: `corpus_id`, `component`, `channel`

**Edge Cases**:
- Zero traffic: Returns `0.0` with `zero_traffic: true`
- Missing compliance fields: Treated as non-compliant

**Example**:
```
total_retrievals = 1000
compliant_retrievals = 950
SLI-E = 950 / 1000 = 0.95 (95% compliance)
```

## SLI-F: Evaluation Quality Signal

**Formula**: `user_flags + score_distribution`

**Components**:
- **User flag rate**: `count(user.flag.v1) / count(evaluation.result.v1)`
- **Score distribution**: p50/p95/p99/mean of scores from `evaluation.result.v1` metrics

**Source**: 
- `evaluation.result.v1` events (metrics: score, accuracy, quality)
- `user.flag.v1` events

**Grouping**: `channel`, `component`, `eval_suite_id`

**Output**: 
- Primary value: Mean score
- Metadata: User flag rate, score distribution (p50, p95, p99, mean, count)

**Edge Cases**:
- Zero traffic: Returns `0.0` with empty distribution
- Missing scores: Skipped from distribution
- No evaluations: User flag rate is `0.0`

**Example**:
```
evaluations = 100
user_flags = 5
scores = [0.85, 0.90, 0.95, ...]
user_flag_rate = 5 / 100 = 0.05 (5%)
score_mean = 0.90
```

## SLI-G: False Positive Rate (FPR)

**Formula**: `false_positive / (false_positive + true_positive)`

**Numerator**: Count of `alert.noise_control.v1` events with `validation_outcome=false_positive`

**Denominator**: Count of `alert.noise_control.v1` events with `validation_outcome` in `{false_positive, true_positive}`

**Source**: `alert.noise_control.v1` events enriched by human validation outcomes

**Grouping**: `detector_type`, `alert_fingerprint`

**Edge Cases**:
- Zero traffic: Returns `0.0` with `zero_traffic: true`
- Missing validation outcome: Not counted
- Only false positives: FPR = 1.0
- Only true positives: FPR = 0.0

**Example**:
```
false_positives = 10
true_positives = 90
total_positive = 100
SLI-G = 10 / 100 = 0.10 (10% FPR)
```

## Implementation Notes

### Deterministic Computation

All SLIs are computed deterministically:
- Same input events → same SLI values
- No randomness or AI-based decisions
- Reproducible results

### Missing Data Handling

- **Zero traffic**: Returns `0.0` with `zero_traffic: true` metadata
- **Missing fields**: Skipped or treated as non-compliant (per SLI logic)
- **Invalid data**: Logged and skipped

### Grouping Dimensions

Each SLI supports filtering and grouping by specific dimensions:
- Component: Service/component identifier
- Channel: ide, edge_agent, backend, ci, other
- Additional dimensions per SLI (error_class, prompt_id, corpus_id, etc.)

### Time Windows

SLIs are computed over configurable time windows:
- Default: Last 1 hour, 24 hours, 7 days
- Configurable via environment variables or policy
- No hardcoded time windows

## References

- PRD Section 5.1: SLIs and SLOs
- Architecture Document: SLI Computation Architecture
- Phase 0 Contracts: Event payload schemas
