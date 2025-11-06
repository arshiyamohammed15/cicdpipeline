# Data Classification

This document classifies data types in ZeroUI 2.0 receipts and evidence.

## Data Classification Levels

### Public

**Description**: Data that can be publicly shared

**Examples**:
- Public policy snapshots
- Public metrics (aggregated)
- Public documentation

**Handling**:
- No restrictions on access
- Can be shared publicly
- No encryption required

### Internal

**Description**: Data for internal use only

**Examples**:
- Internal policy snapshots
- Internal metrics
- Development documentation

**Handling**:
- Access restricted to authenticated users
- Should not be shared externally
- Encryption in transit recommended

### Confidential

**Description**: Sensitive data requiring protection

**Examples**:
- Receipts with decision data
- Policy evaluation results
- User-specific metrics

**Handling**:
- Access restricted to authorized users
- Encryption at rest and in transit
- Audit logging required
- Retention policies apply

### Restricted

**Description**: Highly sensitive data with strict controls

**Examples**:
- Evidence packs with code snippets
- Security incident data
- Audit logs with PII

**Handling**:
- Access restricted to security team and admins
- Strong encryption required
- Strict access controls
- Legal hold may apply

## Receipt Data Classification

### Decision Receipt Fields

| Field | Classification | Reason |
|-------|---------------|--------|
| receipt_id | Internal | Unique identifier |
| gate_id | Public | Gate identifier |
| policy_version_ids | Internal | Policy references |
| snapshot_hash | Internal | Policy hash |
| timestamp_utc | Internal | Timestamp |
| timestamp_monotonic_ms | Internal | Monotonic timestamp |
| inputs | Confidential | May contain sensitive data |
| decision.status | Confidential | Decision outcome |
| decision.rationale | Confidential | Decision reasoning |
| decision.badges | Internal | Decision badges |
| evidence_handles | Confidential | Evidence references |
| actor.repo_id | Confidential | Repository identifier |
| actor.machine_fingerprint | Restricted | Device identifier |
| degraded | Internal | System status |
| signature | Internal | Receipt signature |

### Feedback Receipt Fields

| Field | Classification | Reason |
|-------|---------------|--------|
| feedback_id | Internal | Unique identifier |
| decision_receipt_id | Confidential | Links to decision |
| pattern_id | Internal | Feedback pattern |
| choice | Confidential | User feedback |
| tags | Internal | Feedback tags |
| actor.repo_id | Confidential | Repository identifier |
| actor.machine_fingerprint | Restricted | Device identifier |
| timestamp_utc | Internal | Timestamp |
| signature | Internal | Receipt signature |

## Evidence Data Classification

### Evidence Pack Fields

| Field | Classification | Reason |
|-------|---------------|--------|
| evidence_pack_id | Internal | Unique identifier |
| receipt_id | Confidential | Links to receipt |
| gate_id | Internal | Gate identifier |
| created_at | Internal | Timestamp |
| evidence_items | Restricted | May contain code/PII |
| metadata | Confidential | Decision metadata |
| retention | Internal | Retention policy |

### Evidence Item Types

| Type | Classification | Reason |
|------|---------------|--------|
| github_pr | Confidential | Repository access |
| code_diff | Restricted | Contains code |
| test_results | Internal | Test data |
| log_files | Restricted | May contain PII |
| artifacts | Restricted | May contain sensitive data |

## Data Handling Requirements

### Encryption

- **At Rest**: All Confidential and Restricted data encrypted
- **In Transit**: All data encrypted in transit (TLS 1.3+)
- **Keys**: Managed by Key Management Service

### Access Control

- **Public**: No access control
- **Internal**: Authenticated users only
- **Confidential**: Role-based access control
- **Restricted**: Security team and admins only

### Retention

- **Public**: No retention limit
- **Internal**: 1 year retention
- **Confidential**: 7 years retention (compliance)
- **Restricted**: Legal hold may apply

### Redaction

Before sharing Confidential or Restricted data:
- **PII**: Email addresses, names redacted
- **Secrets**: API keys, passwords redacted
- **Code**: Code snippets may be redacted per policy

## Privacy Considerations

### GDPR Compliance

- **Right to Access**: Users can request their data
- **Right to Deletion**: Users can request data deletion
- **Data Minimization**: Only collect necessary data
- **Purpose Limitation**: Use data only for stated purpose

### Data Minimization

Receipts contain:
- **Metadata Only**: No raw code by default
- **Minimal PII**: Only necessary identifiers
- **Aggregated Metrics**: Where possible

### Redaction Points

Redaction occurs at:
1. **Edge Agent**: Before sending to cloud
2. **Client/Tenant Cloud**: Before cross-plane sharing
3. **Product Cloud**: Before learning loop

## Compliance Requirements

### SOC 2

- **Data Classification**: All data classified
- **Access Controls**: Enforced per classification
- **Audit Logging**: All access logged

### GDPR

- **Data Protection**: Personal data protected
- **User Rights**: Access and deletion supported
- **Privacy by Design**: Built into architecture

### HIPAA (if applicable)

- **PHI Protection**: Protected health information encrypted
- **Access Controls**: Strict access controls
- **Audit Trails**: Comprehensive audit logging

## Data Flow Classification

### IDE/Edge Agent → Client/Tenant Cloud

- **Classification**: Confidential
- **Encryption**: Required
- **Redaction**: PII redacted if needed

### Client/Tenant Cloud → Product Cloud

- **Classification**: Internal (redacted)
- **Encryption**: Required
- **Redaction**: Code and PII redacted

### Product Cloud → Learning Loop

- **Classification**: Internal (anonymized)
- **Encryption**: Required
- **Redaction**: All PII and code redacted

## Best Practices

1. **Classify Early**: Classify data at creation
2. **Minimize Collection**: Collect only necessary data
3. **Encrypt Always**: Encrypt Confidential and Restricted data
4. **Audit Access**: Log all access to sensitive data
5. **Regular Review**: Review classifications quarterly

