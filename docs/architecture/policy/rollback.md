# Policy Rollback Process

This document describes how to roll back a bad policy snapshot to a previous version.

## Rollback Scenarios

### Scenario 1: Policy Causes False Positives

**Symptoms**:
- High rate of false positive gate blocks
- User complaints about incorrect decisions
- Metrics show abnormal rejection rates

**Action**:
1. Identify the problematic policy snapshot (via KID and version)
2. Verify the issue (check receipts and metrics)
3. Roll back to previous known-good snapshot
4. Notify affected users

### Scenario 2: Policy Causes Security Vulnerability

**Symptoms**:
- Security scan detects vulnerability
- Policy allows unsafe operations
- Audit trail shows security violations

**Action**:
1. **Immediate**: Revoke current policy snapshot via CRL
2. Roll back to last known-secure snapshot
3. Investigate root cause
4. Deploy fixed policy after verification

### Scenario 3: Policy Causes System Instability

**Symptoms**:
- High error rates in policy evaluation
- Performance degradation
- System crashes or timeouts

**Action**:
1. **Emergency Rollback**: Immediately roll back to stable snapshot
2. Disable problematic policy module if needed
3. Investigate and fix
4. Re-deploy after testing

## Rollback Process

### Step 1: Identify Current Policy

```bash
# Check current policy snapshot
curl https://policy-registry.example.com/api/v1/policies/current

# Response includes:
# - snapshot_id
# - version
# - kid
# - effective_from
```

### Step 2: Identify Target Rollback Snapshot

```bash
# List available snapshots
curl https://policy-registry.example.com/api/v1/policies/history

# Select target snapshot (previous known-good version)
# Verify target snapshot signature and hash
```

### Step 3: Revoke Current Snapshot

```bash
# Revoke current snapshot via CRL
curl -X POST https://policy-registry.example.com/api/v1/trust/crl/revoke \
  -H "Content-Type: application/json" \
  -d '{
    "kid": "KID:zero-ui-product:ed25519:2025-01",
    "snapshot_id": "SNAP.INIT.policy_snapshot.v1",
    "reason": "rollback",
    "revoked_at": "2025-01-27T12:00:00Z"
  }'
```

### Step 4: Activate Target Snapshot

```bash
# Activate target snapshot
curl -X POST https://policy-registry.example.com/api/v1/policies/activate \
  -H "Content-Type: application/json" \
  -d '{
    "snapshot_id": "SNAP.INIT.policy_snapshot.v0",
    "effective_from": "2025-01-27T12:00:00Z"
  }'
```

### Step 5: Distribute Rollback

```bash
# Policy Registry automatically distributes to:
# 1. Client/Tenant Cloud (updates cache)
# 2. IDE/Edge Agent (fetches on next policy check)
```

### Step 6: Verify Rollback

```bash
# Verify new policy is active
curl https://policy-registry.example.com/api/v1/policies/current

# Check client caches updated
curl https://client.example.com/api/v1/policy/current

# Monitor metrics for stabilization
```

## Rollback CLI

### Using ZeroUI CLI

```bash
# Rollback to previous version
zeroui policy rollback --to-version v0

# Rollback to specific snapshot
zeroui policy rollback --snapshot-id SNAP.INIT.policy_snapshot.v0

# Rollback with reason
zeroui policy rollback --to-version v0 --reason "false_positives"
```

### Using Policy Registry API

```bash
# Full rollback workflow
./scripts/rollback_policy.sh \
  --current SNAP.INIT.policy_snapshot.v1 \
  --target SNAP.INIT.policy_snapshot.v0 \
  --reason "false_positives"
```

## Rollback Verification

### Checklist

- [ ] Current snapshot revoked in CRL
- [ ] Target snapshot activated
- [ ] Target snapshot signature verified
- [ ] Target snapshot hash verified
- [ ] Policy Registry updated
- [ ] Client caches invalidated
- [ ] IDE/Edge Agent notified
- [ ] Metrics show rollback successful
- [ ] Users notified (if applicable)

### Verification Commands

```bash
# Check CRL for revoked snapshot
curl https://policy-registry.example.com/api/v1/trust/crl

# Check current active snapshot
curl https://policy-registry.example.com/api/v1/policies/current

# Check client cache status
curl https://client.example.com/api/v1/policy/status

# Check metrics
curl https://observability.example.com/api/v1/metrics/policy_decisions
```

## Rollback Impact

### Immediate Impact

- **Policy Decisions**: New decisions use rolled-back policy
- **Cached Policies**: Client caches invalidated, fetch new policy
- **Active Evaluations**: In-flight evaluations may use old policy (acceptable)

### Delayed Impact

- **IDE/Edge Agent**: Fetches new policy on next check (within 5 minutes)
- **Metrics**: Rollback reflected in metrics within 1 hour
- **Audit Trail**: Rollback logged in audit ledger

## Rollback Recovery

### If Rollback Fails

1. **Check Policy Registry**: Verify registry is accessible
2. **Check CRL**: Verify CRL update succeeded
3. **Check Client Caches**: Manually invalidate if needed
4. **Emergency Override**: Use emergency override if critical

### Emergency Override

```bash
# Emergency override (bypass normal rollback)
zeroui policy emergency-override \
  --snapshot-id SNAP.INIT.policy_snapshot.v0 \
  --authoriser admin \
  --reason "critical_rollback"
```

## Post-Rollback Actions

### Investigation

1. **Root Cause Analysis**: Why did policy fail?
2. **Fix Development**: Develop fix for problematic policy
3. **Testing**: Test fix thoroughly before re-deployment
4. **Documentation**: Document issue and resolution

### Re-Deployment

1. **Fix Verification**: Verify fix addresses root cause
2. **Staged Rollout**: Deploy fix in stages (dev → staging → prod)
3. **Monitoring**: Monitor metrics during rollout
4. **Full Deployment**: Deploy to all environments after verification

## Rollback History

All rollbacks are logged in:
- **Audit Ledger**: Immutable record of all rollbacks
- **Policy Registry**: Rollback history in policy metadata
- **Metrics**: Rollback events in observability system

## Access Control

### Who Can Rollback

- **Policy Administrators**: Full rollback access
- **Security Team**: Emergency rollback access
- **On-Call Engineers**: Rollback access during incidents

### Rollback Authorization

```json
{
  "required_roles": ["policy_admin", "security_team"],
  "dual_approval": true,
  "audit_logging": true
}
```

## Best Practices

1. **Test Before Deploy**: Always test policies in staging first
2. **Staged Rollout**: Use staged rollout for new policies
3. **Monitor Metrics**: Monitor metrics after policy changes
4. **Keep History**: Maintain policy snapshot history
5. **Document Rollbacks**: Document all rollbacks with reasons

