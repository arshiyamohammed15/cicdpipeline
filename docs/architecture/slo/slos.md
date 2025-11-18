# Service Level Objectives (SLOs)

This document defines SLO targets for each service and surface in the ZeroUI architecture.

## SLO Definition Format

Each SLO is defined with:
- **Service/Surface**: The component being measured
- **Metric**: What is being measured
- **Target**: The target value
- **Window**: The time window for measurement
- **Error Budget**: Maximum acceptable failures

## VS Code Extension (Presentation Layer)

### Activation Time
- **Metric**: Extension activation latency
- **Target**: < 50ms (cold start)
- **Window**: 1 hour
- **Error Budget**: 5% of activations can exceed target

### Status Pill Render
- **Metric**: Status pill initial render time
- **Target**: ≤ 50ms
- **Window**: 1 hour
- **Error Budget**: 5% of renders can exceed target

### Command Handler Response
- **Metric**: Command handler return time (non-blocking)
- **Target**: < 10ms (return control immediately)
- **Window**: 1 hour
- **Error Budget**: 1% of commands can exceed target

## Edge Agent (Delegation Layer)

### Task Delegation Latency
- **Metric**: Time from task receipt to delegation result
- **Target**: < 100ms (local processing)
- **Window**: 1 hour
- **Error Budget**: 5% of delegations can exceed target

### Receipt Generation
- **Metric**: Receipt generation and fsync time
- **Target**: < 50ms (including fsync)
- **Window**: 1 hour
- **Error Budget**: 1% of receipts can exceed target (critical for audit)

### Policy Snapshot Verification
- **Metric**: Policy snapshot signature verification time
- **Target**: < 20ms
- **Window**: 1 hour
- **Error Budget**: 1% of verifications can exceed target

## Cloud Services (Business Logic Layer)

### API Response Time
- **Metric**: API endpoint response time (p50)
- **Target**: < 200ms
- **Window**: 1 hour
- **Error Budget**: 5% of requests can exceed target

### API Availability
- **Metric**: API endpoint availability
- **Target**: 99.9% uptime
- **Window**: 30 days
- **Error Budget**: 0.1% downtime (43.2 minutes per month)

### Policy Snapshot Distribution
- **Metric**: Time from snapshot creation to client availability
- **Target**: < 5 minutes
- **Window**: 1 hour
- **Error Budget**: 5% of distributions can exceed target

## Shared Services Plane

### Policy Registry Availability
- **Metric**: Policy Registry API availability
- **Target**: 99.95% uptime
- **Window**: 30 days
- **Error Budget**: 0.05% downtime (21.6 minutes per month)

### Audit Ledger Write
- **Metric**: Audit ledger append latency
- **Target**: < 100ms (including fsync)
- **Window**: 1 hour
- **Error Budget**: 0.1% of writes can exceed target (critical for audit)

### Trust Store Key Lookup
- **Metric**: Public key lookup time
- **Target**: < 10ms (cached)
- **Window**: 1 hour
- **Error Budget**: 1% of lookups can exceed target

## Observability Mesh

### Metrics Collection
- **Metric**: Metrics collection overhead
- **Target**: < 1% CPU overhead
- **Window**: 1 hour
- **Error Budget**: 5% of time can exceed target

### Trace Sampling
- **Metric**: Trace sampling rate
- **Target**: 1% of requests sampled
- **Window**: 1 hour
- **Error Budget**: ±0.5% variance acceptable

## Error Budget Calculation

Error budgets are calculated as:
```
Error Budget = (1 - Target) × Window × Requests
```

Example for 99.9% availability over 30 days:
```
Error Budget = (1 - 0.999) × 30 days × 24 hours × 60 minutes
             = 0.001 × 43,200 minutes
             = 43.2 minutes
```

## SLO Violation Response

When SLO is violated:

1. **Alert**: Immediate alert to on-call engineer
2. **Investigation**: Root cause analysis within 1 hour
3. **Mitigation**: Fix or workaround within 4 hours
4. **Post-Mortem**: Document within 1 week if error budget exhausted

## Review and Update

SLOs are reviewed:
- **Quarterly**: Review targets and error budgets
- **After Incidents**: Adjust based on learnings
- **On Scale Changes**: Re-evaluate when traffic patterns change
