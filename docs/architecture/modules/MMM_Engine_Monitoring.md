# MMM Engine Monitoring & Observability

## Overview

Per PRD Phase 5, this document describes monitoring, alerting, and observability configuration for the MMM Engine in production.

## Prometheus Metrics

### Core Metrics

#### Decision Metrics
- `mmm_decisions_total{tenant_id, actor_type}` - Counter: Total MMM decisions
- `mmm_decision_latency_seconds{tenant_id}` - Histogram: Decision latency with buckets [0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0]
- `mmm_decision_latency_warning_total{tenant_id, exceeded_threshold}` - Counter: Latency SLO warnings

#### Action Metrics
- `mmm_actions_total{tenant_id, action_type}` - Counter: Total actions proposed
- `mmm_outcomes_total{tenant_id, result}` - Counter: Total outcomes recorded

#### Service Integration Metrics
- `mmm_eris_receipt_emission_total{tenant_id, result}` - Counter: ERIS receipt emission results (success/failure)
- `mmm_circuit_state{name}` - Gauge: Circuit breaker state (0=closed, 1=open, 2=half-open)
- `mmm_delivery_attempts_total{channel, result}` - Counter: Delivery attempts per channel

### Metric Collection

Metrics are exposed at `/v1/mmm/metrics` endpoint in Prometheus format.

## Alert Rules

### Critical Alerts

#### High Latency (IDE)
```yaml
- alert: MMMEngineHighLatencyIDE
  expr: histogram_quantile(0.95, rate(mmm_decision_latency_seconds_bucket{tenant_id=~".+"}[5m])) > 0.15
  for: 5m
  labels:
    severity: warning
    component: mmm-engine
  annotations:
    summary: "MMM Engine IDE latency p95 exceeds 150ms SLO"
    description: "Tenant {{ $labels.tenant_id }} has p95 latency of {{ $value }}s (SLO: 0.15s)"
```

#### High Latency (CI)
```yaml
- alert: MMMEngineHighLatencyCI
  expr: histogram_quantile(0.95, rate(mmm_decision_latency_seconds_bucket{tenant_id=~".+"}[5m])) > 0.5
  for: 5m
  labels:
    severity: warning
    component: mmm-engine
  annotations:
    summary: "MMM Engine CI latency p95 exceeds 500ms SLO"
    description: "Tenant {{ $labels.tenant_id }} has p95 latency of {{ $value }}s (SLO: 0.5s)"
```

#### Circuit Breaker Open
```yaml
- alert: MMMEngineCircuitBreakerOpen
  expr: mmm_circuit_state{name=~".+"} == 1
  for: 2m
  labels:
    severity: critical
    component: mmm-engine
  annotations:
    summary: "MMM Engine circuit breaker open for {{ $labels.name }}"
    description: "Circuit breaker {{ $labels.name }} is open, indicating service unavailability"
```

#### ERIS Receipt Emission Failures
```yaml
- alert: MMMEngineERISReceiptFailures
  expr: rate(mmm_eris_receipt_emission_total{result="failure"}[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
    component: mmm-engine
  annotations:
    summary: "MMM Engine ERIS receipt emission failures high"
    description: "Receipt emission failure rate is {{ $value }} failures/second"
```

#### Degraded Mode Activations
```yaml
- alert: MMMEngineDegradedMode
  expr: rate(mmm_decisions_total{degraded_mode="true"}[5m]) > 0.1
  for: 5m
  labels:
    severity: warning
    component: mmm-engine
  annotations:
    summary: "MMM Engine operating in degraded mode"
    description: "{{ $value }} decisions/second are being made in degraded mode"
```

### Warning Alerts

#### Low Throughput
```yaml
- alert: MMMEngineLowThroughput
  expr: rate(mmm_decisions_total[5m]) < 10
  for: 10m
  labels:
    severity: warning
    component: mmm-engine
  annotations:
    summary: "MMM Engine throughput below expected"
    description: "Decision rate is {{ $value }} decisions/second"
```

## Grafana Dashboards

### MMM Engine Overview Dashboard

**Panel 1: Decision Rate**
- Query: `rate(mmm_decisions_total[5m])`
- Visualization: Time series graph
- Y-axis: Decisions per second

**Panel 2: Latency Distribution**
- Query: `histogram_quantile(0.95, rate(mmm_decision_latency_seconds_bucket[5m]))`
- Visualization: Time series graph
- Y-axis: Latency (seconds)
- Threshold lines: 0.15s (IDE), 0.5s (CI)

**Panel 3: Action Types Distribution**
- Query: `sum by (action_type) (rate(mmm_actions_total[5m]))`
- Visualization: Pie chart

**Panel 4: Circuit Breaker States**
- Query: `mmm_circuit_state`
- Visualization: Gauge
- States: 0=Closed (green), 1=Open (red), 2=Half-Open (yellow)

**Panel 5: ERIS Receipt Emission Success Rate**
- Query: `rate(mmm_eris_receipt_emission_total{result="success"}[5m]) / rate(mmm_eris_receipt_emission_total[5m])`
- Visualization: Gauge
- Threshold: < 0.95 (warning)

**Panel 6: Degraded Mode Rate**
- Query: `rate(mmm_decisions_total{degraded_mode="true"}[5m]) / rate(mmm_decisions_total[5m])`
- Visualization: Time series graph
- Y-axis: Percentage

**Panel 7: Top Tenants by Decision Volume**
- Query: `topk(10, sum by (tenant_id) (rate(mmm_decisions_total[5m])))`
- Visualization: Bar chart

**Panel 8: Outcome Results Distribution**
- Query: `sum by (result) (rate(mmm_outcomes_total[5m]))`
- Visualization: Stacked area chart

### MMM Engine Performance Dashboard

**Panel 1: Latency Percentiles (p50, p95, p99)**
- Queries:
  - `histogram_quantile(0.50, rate(mmm_decision_latency_seconds_bucket[5m]))`
  - `histogram_quantile(0.95, rate(mmm_decision_latency_seconds_bucket[5m]))`
  - `histogram_quantile(0.99, rate(mmm_decision_latency_seconds_bucket[5m]))`
- Visualization: Time series graph with multiple series

**Panel 2: Latency SLO Compliance**
- Query: `mmm_decision_latency_warning_total`
- Visualization: Counter
- Alert threshold: > 0

**Panel 3: Service Call Latencies**
- Breakdown by service (IAM, ERIS, LLM Gateway, Policy, Data Governance, UBI)
- Visualization: Time series graph

**Panel 4: Cache Hit Rates**
- Policy cache hit rate
- Preference cache hit rate
- Visualization: Gauge

## Distributed Tracing

### OpenTelemetry Configuration

Per PRD Phase 3, MMM Engine uses OpenTelemetry for distributed tracing:

- **Service Name**: `mmm-engine`
- **Exporter**: OTLP gRPC
- **Endpoint**: Configured via `OTLP_EXPORTER_ENDPOINT` environment variable

### Trace Spans

Key spans in decision flow:
- `mmm.decide` - Parent span for decision flow
- `context.build` - Context assembly
- `playbook.evaluate` - Playbook evaluation
- `policy.gate` - Policy evaluation
- `eris.receipt` - Receipt emission
- `delivery.route` - Action delivery

### Span Attributes

Each span includes:
- `tenant_id` - Tenant identifier
- `actor_id` - Actor identifier
- `decision_id` - Decision identifier
- `playbook_ids` - List of evaluated playbooks
- `action_count` - Number of actions generated
- `latency_ms` - Operation latency
- `degraded_mode` - Degraded mode flag

## Logging

### Log Levels

- **ERROR**: Service failures, circuit breaker opens, receipt emission failures
- **WARNING**: Degraded mode, latency SLO violations, policy unavailable
- **INFO**: Decision creation, playbook evaluation, action delivery
- **DEBUG**: Detailed operation traces (disabled in production)

### Log Format

Structured JSON logs with fields:
- `timestamp` - ISO 8601 UTC timestamp
- `level` - Log level
- `service` - Service name (`mmm-engine`)
- `tenant_id` - Tenant identifier
- `actor_id` - Actor identifier
- `decision_id` - Decision identifier (if applicable)
- `trace_id` - OpenTelemetry trace ID
- `message` - Log message
- `error` - Error details (if applicable)

### Audit Logging

Per PRD NFR-7, security audit logs are written to `/var/log/mmm_engine/audit.log`:
- Admin mutations (playbook create/update/publish, tenant policy updates, experiment management)
- Redacted before/after state
- Admin user ID
- Timestamp

## Health Checks

### Readiness Probe

Endpoint: `/v1/mmm/ready`

Checks:
- Service initialized
- All required dependencies available (IAM, Policy, ERIS)
- Database connection
- Redis connection (if enabled)

Returns:
- `200 OK` if ready
- `503 Service Unavailable` if not ready

### Liveness Probe

Endpoint: `/v1/mmm/health`

Checks:
- Service operational
- Basic functionality

Returns:
- `200 OK` if healthy
- `503 Service Unavailable` if unhealthy

## Performance Targets

Per PRD NFR-1:
- **IDE Calls**: p95 latency ≤ 150ms
- **CI Calls**: p95 latency ≤ 500ms
- **Throughput**: 1000 decisions/minute per tenant
- **Total Throughput**: 10,000 decisions/minute

## Capacity Planning

### Resource Requirements

Per pod:
- **CPU**: 500m request, 2 cores limit
- **Memory**: 1Gi request, 4Gi limit

### Scaling

- **Min Replicas**: 3
- **Max Replicas**: 10
- **HPA Metrics**: CPU (70%), Memory (80%)
- **Scale Up**: 100% or +2 pods per minute
- **Scale Down**: 50% per 5 minutes

### Database

- Connection pool: 10 connections, max overflow 20
- Read replicas recommended for high read load

### Redis

- Used for fatigue state (horizontal scaling)
- TTL: 24 hours
- Key pattern: `mmm:fatigue:{tenant_id}:{actor_id}:{action_type}`

## Troubleshooting

### High Latency

1. Check service call latencies (IAM, ERIS, LLM Gateway, Policy)
2. Check database query performance
3. Check Redis latency
4. Review circuit breaker states
5. Check for degraded mode activations

### Circuit Breaker Opens

1. Check downstream service health
2. Review error logs for connection failures
3. Check network connectivity
4. Verify service URLs in configuration

### ERIS Receipt Failures

1. Check ERIS service availability
2. Review receipt signing key configuration
3. Check network connectivity to ERIS
4. Review retry logic and circuit breaker state

### Degraded Mode

1. Identify which dependency is unavailable
2. Check circuit breaker states
3. Review service health endpoints
4. Check for network issues

