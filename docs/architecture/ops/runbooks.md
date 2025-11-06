# Incident Runbooks

This document contains runbooks for the top 3 most critical incidents in the ZeroUI system.

## Runbook 1: Receipt Not Written

### Symptoms

- Edge Agent processes task but receipt is not written to disk
- Receipt file missing in `{ZU_ROOT}/ide/receipts/`
- Audit trail incomplete
- VS Code Extension shows no receipt data

### Impact

- **Severity**: Critical
- **Affected**: Audit trail, compliance, debugging
- **User Impact**: Cannot track decisions, no evidence

### Diagnosis

1. **Check Receipt Storage Service**
   ```bash
   # Check if receipt storage service is running
   ps aux | grep ReceiptStorageService
   
   # Check storage path exists and is writable
   ls -la {ZU_ROOT}/ide/receipts/
   ```

2. **Check Disk Space**
   ```bash
   df -h {ZU_ROOT}/ide/receipts/
   ```

3. **Check File Permissions**
   ```bash
   ls -la {ZU_ROOT}/ide/receipts/
   # Should be writable by Edge Agent process
   ```

4. **Check Logs**
   ```bash
   # Check Edge Agent logs for errors
   tail -f {ZU_ROOT}/ide/logs/edge-agent.log | grep -i receipt
   ```

### Resolution

#### Step 1: Immediate Fix

```bash
# 1. Check if storage path exists
mkdir -p {ZU_ROOT}/ide/receipts/

# 2. Fix permissions if needed
chmod 755 {ZU_ROOT}/ide/receipts/

# 3. Restart Edge Agent
systemctl restart edge-agent
# OR
./scripts/restart-edge-agent.sh
```

#### Step 2: Verify Fix

```bash
# Trigger a test receipt
zeroui test-receipt

# Verify receipt was written
ls -la {ZU_ROOT}/ide/receipts/ | tail -5

# Check receipt content
cat {ZU_ROOT}/ide/receipts/receipt_*.jsonl | tail -1
```

#### Step 3: Root Cause Analysis

- **Disk Full**: Free up disk space, increase quota
- **Permission Issue**: Fix file permissions, check SELinux/AppArmor
- **Storage Service Crash**: Check service logs, restart service
- **Path Resolution Issue**: Verify ZU_ROOT environment variable

### Prevention

- **Monitoring**: Alert on receipt write failures
- **Health Checks**: Regular health checks on receipt storage
- **Disk Space Monitoring**: Alert when disk space < 10%
- **Automated Testing**: Test receipt writing in CI/CD

### Escalation

- **Level 1**: On-call engineer (immediate)
- **Level 2**: Team lead (if not resolved in 15 minutes)
- **Level 3**: Engineering manager (if not resolved in 1 hour)

---

## Runbook 2: Gate Blocks All PRs

### Symptoms

- All pull requests are blocked by gates
- No PRs can be merged
- High rate of hard_block decisions
- Users unable to proceed with work

### Impact

- **Severity**: Critical
- **Affected**: All developers, CI/CD pipeline
- **User Impact**: Development blocked, productivity loss

### Diagnosis

1. **Check Gate Tables**
   ```bash
   # Verify gate tables are accessible
   ls -la docs/architecture/gate_tables/
   
   # Check gate table CSV format
   head -5 docs/architecture/gate_tables/gate_pr_size.csv
   ```

2. **Check Policy Snapshot**
   ```bash
   # Check current policy snapshot
   curl https://policy-registry.example.com/api/v1/policies/current
   
   # Verify policy snapshot signature
   zeroui policy verify --snapshot-id SNAP.INIT.policy_snapshot.v1
   ```

3. **Check Gate Decision Logic**
   ```bash
   # Test gate decision with sample input
   zeroui gate test --gate-id gate_pr_size --input '{"pr_lines_changed": 100}'
   ```

4. **Check Metrics**
   ```bash
   # Check decision metrics
   curl https://observability.example.com/api/v1/metrics/policy_decisions
   # Look for 100% hard_block rate
   ```

### Resolution

#### Step 1: Immediate Mitigation

```bash
# Option A: Disable problematic gate temporarily
zeroui gate disable --gate-id gate_pr_size --reason "emergency_disable"

# Option B: Lower gate thresholds
zeroui gate update --gate-id gate_pr_size --threshold pr_lines_changed:5000

# Option C: Enable override mode
zeroui policy override --mode warn --duration 2h
```

#### Step 2: Root Cause Analysis

- **Gate Table Corruption**: Restore from backup, verify CSV format
- **Policy Snapshot Issue**: Roll back to previous policy (see rollback.md)
- **Threshold Misconfiguration**: Check gate table thresholds
- **Bug in Decision Logic**: Check gate decision code, review recent changes

#### Step 3: Permanent Fix

```bash
# Fix gate table
# 1. Restore correct gate table CSV
cp docs/architecture/gate_tables/gate_pr_size.csv.backup \
   docs/architecture/gate_tables/gate_pr_size.csv

# 2. Verify gate table
zeroui gate validate --gate-id gate_pr_size

# 3. Re-enable gate
zeroui gate enable --gate-id gate_pr_size
```

### Prevention

- **Gate Table Validation**: Validate CSV format in CI/CD
- **Staged Rollout**: Test gate changes in staging first
- **Monitoring**: Alert on high block rates
- **Canary Testing**: Test gate changes on subset of users

### Escalation

- **Level 1**: On-call engineer (immediate)
- **Level 2**: Team lead (if not resolved in 15 minutes)
- **Level 3**: Engineering manager (if not resolved in 30 minutes)
- **Level 4**: CTO (if development completely blocked)

---

## Runbook 3: Policy Fetch Fails

### Symptoms

- Edge Agent cannot fetch policy snapshot from Policy Registry
- Policy cache is stale or empty
- Policy verification fails
- Gate decisions cannot be made

### Impact

- **Severity**: Critical
- **Affected**: All gate decisions, policy enforcement
- **User Impact**: Cannot proceed with development work

### Diagnosis

1. **Check Policy Registry Availability**
   ```bash
   # Check Policy Registry health
   curl https://policy-registry.example.com/health
   
   # Check Policy Registry API
   curl https://policy-registry.example.com/api/v1/policies/current
   ```

2. **Check Network Connectivity**
   ```bash
   # Test connectivity from Edge Agent
   ping policy-registry.example.com
   
   # Test HTTPS connectivity
   curl -v https://policy-registry.example.com/api/v1/policies/current
   ```

3. **Check Policy Cache**
   ```bash
   # Check cached policy
   ls -la {ZU_ROOT}/ide/policy/
   
   # Check cache age
   stat {ZU_ROOT}/ide/policy/policy_snapshot_v1.json
   ```

4. **Check Authentication**
   ```bash
   # Check authentication token
   cat {ZU_ROOT}/ide/config/auth_token
   
   # Test authentication
   curl -H "Authorization: Bearer $(cat {ZU_ROOT}/ide/config/auth_token)" \
        https://policy-registry.example.com/api/v1/policies/current
   ```

### Resolution

#### Step 1: Immediate Mitigation

```bash
# Option A: Use cached policy (if available and recent)
# Edge Agent should fall back to cached policy automatically

# Option B: Manual policy fetch
zeroui policy fetch --force

# Option C: Use local policy file (emergency)
cp docs/architecture/policy/policy_snapshot_v1.json \
   {ZU_ROOT}/ide/policy/policy_snapshot_v1.json
```

#### Step 2: Root Cause Analysis

- **Policy Registry Down**: Check Policy Registry status, restart if needed
- **Network Issue**: Check network connectivity, firewall rules
- **Authentication Failure**: Renew authentication token
- **Cache Corruption**: Clear cache and re-fetch

#### Step 3: Permanent Fix

```bash
# Fix Policy Registry (if down)
systemctl restart policy-registry

# Fix authentication
zeroui auth refresh

# Clear and re-fetch policy
rm -rf {ZU_ROOT}/ide/policy/*
zeroui policy fetch --force

# Verify policy
zeroui policy verify --snapshot-id SNAP.INIT.policy_snapshot.v1
```

### Prevention

- **Health Monitoring**: Monitor Policy Registry availability
- **Cache Management**: Implement cache expiration and refresh
- **Fallback Mechanism**: Use cached policy if fetch fails
- **Retry Logic**: Implement exponential backoff for policy fetch

### Escalation

- **Level 1**: On-call engineer (immediate)
- **Level 2**: Team lead (if not resolved in 15 minutes)
- **Level 3**: Engineering manager (if not resolved in 1 hour)

---

## General Incident Response

### Communication

- **Status Page**: Update status page with incident details
- **Slack**: Post in #incidents channel
- **Email**: Notify affected users if widespread

### Post-Incident

- **Post-Mortem**: Conduct within 1 week
- **Action Items**: Document and track fixes
- **Runbook Updates**: Update runbooks based on learnings

### Metrics to Track

- **MTTR**: Mean Time To Resolution
- **Incident Frequency**: Number of incidents per month
- **False Positive Rate**: Incidents that were false alarms

