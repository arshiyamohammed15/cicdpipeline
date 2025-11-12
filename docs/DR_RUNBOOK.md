# Disaster Recovery (DR) Runbook

## Overview

This runbook documents how to execute DR drills using the LocalDRPlan implementation. The system provides two core drills: **backup-verify** and **queue-drain**.

## Prerequisites

- LocalDRPlan instance initialized with BackupPort and QueuePort
- Access to the DR plan execution environment
- Sufficient storage for backup operations
- Queue resources available for drain operations

## Drills

### Drill 1: backup-verify

**Purpose**: Verify backup creation and integrity validation.

**Steps**:
1. Create a backup of the specified resource
2. Verify the backup integrity (checksums, file presence)
3. Report verification status

**Configuration**:
```json
{
  "id": "backup-verify-step",
  "name": "Backup and Verify",
  "order": 1,
  "type": "backup",
  "config": {
    "resourceId": "resource-id",
    "resourceType": "resource-type"
  }
}
```

**Evidence to Capture**:
- Backup ID
- Backup creation timestamp
- Backup size (bytes)
- Verification status (`valid`, `invalid`, `corrupted`)
- Verification timestamp
- Checksum values
- Any verification errors

**Expected Outcome**: 
- Backup created successfully
- Verification status: `valid`
- All files present with matching checksums

**Failure Indicators**:
- Backup creation fails
- Verification status: `invalid` or `corrupted`
- Checksum mismatches
- Missing files

### Drill 2: queue-drain

**Purpose**: Drain all messages from a queue (used during failover scenarios).

**Steps**:
1. Receive messages from the specified queue (batch of 10)
2. Delete each received message
3. Repeat until queue is empty
4. Confirm queue is drained

**Configuration**:
```json
{
  "id": "queue-drain-step",
  "name": "Drain Queue",
  "order": 2,
  "type": "validate",
  "config": {
    "queueName": "queue-name"
  }
}
```

**Evidence to Capture**:
- Queue name
- Initial message count (if available)
- Messages processed count
- Drain start timestamp
- Drain completion timestamp
- Drain duration
- Final queue state (should be empty)
- Any errors during drain

**Expected Outcome**:
- All messages successfully drained
- Queue is empty after drain
- No errors during drain operation

**Failure Indicators**:
- Messages remain in queue after drain
- Errors during message deletion
- Queue operations fail

## Running Drills

### Programmatic Execution

```typescript
import { LocalDRPlan } from './src/platform/adapters/local/LocalDRPlan';
import { LocalBackup } from './src/platform/adapters/local/LocalBackup';
import { LocalQueue, LocalDLQ } from './src/platform/adapters/local';

// Initialize adapters
const backup = new LocalBackup(baseDir);
const dlq = new LocalDLQ(baseDir);
const queue = new LocalQueue(baseDir, dlq);
const drPlan = new LocalDRPlan(baseDir, backup, queue);

// Create DR plan with drills
const planId = await drPlan.createPlan({
  name: 'DR Drill Plan',
  primaryRegion: 'us-east-1',
  drRegion: 'us-west-2',
  rpoSeconds: 300,
  rtoSeconds: 600,
  steps: [
    {
      id: 'backup-verify',
      name: 'Backup and Verify',
      order: 1,
      type: 'backup',
      config: {
        resourceId: 'test-resource',
        resourceType: 'test-type',
      },
    },
    {
      id: 'queue-drain',
      name: 'Drain Queue',
      order: 2,
      type: 'validate',
      config: {
        queueName: 'test-queue',
      },
    },
  ],
});

// Test plan (dry run)
const testResult = await drPlan.testPlan(planId);
console.log('Test Status:', testResult.status); // Should be 'passed'

// Execute plan
const executionResult = await drPlan.executePlan(planId);
console.log('Execution Status:', executionResult.status); // Should be 'success'
```

### Evidence Collection

After drill execution, collect the following evidence:

1. **Execution Record**:
   - Execution ID
   - Plan ID
   - Execution status
   - Start/end timestamps
   - Duration
   - Step execution details

2. **Backup Evidence** (for backup-verify):
   - Backup manifest file: `{baseDir}/backups/{backupId}/manifest.json`
   - Verification result: `{baseDir}/backup-manifest.jsonl`
   - Checksum values for all files

3. **Queue Evidence** (for queue-drain):
   - Queue file: `{baseDir}/queues/{queueName}.jsonl`
   - Queue attributes showing message count (should be 0)
   - Execution logs

4. **Execution History**:
   ```typescript
   const history = await drPlan.getExecutionHistory(planId);
   // Contains all execution records with timestamps and status
   ```

## Verification Checklist

### backup-verify Drill
- [ ] Backup created successfully
- [ ] Backup ID recorded
- [ ] Verification status is `valid`
- [ ] All files present in backup
- [ ] Checksums match for all files
- [ ] Backup manifest is valid
- [ ] No errors in execution log

### queue-drain Drill
- [ ] Queue drained completely
- [ ] Message count is 0 after drain
- [ ] All messages deleted successfully
- [ ] No errors during drain
- [ ] Drain completed within timeout
- [ ] Queue file reflects empty state

## Troubleshooting

### backup-verify Failures

**Issue**: Backup creation fails
- Check resource path exists
- Verify sufficient storage space
- Check file permissions

**Issue**: Verification fails
- Check backup directory exists
- Verify file checksums
- Check for file corruption

### queue-drain Failures

**Issue**: Messages remain in queue
- Check visibility timeout settings
- Verify message deletion succeeded
- Check for concurrent consumers

**Issue**: Queue operations fail
- Verify queue file exists
- Check file permissions
- Verify queue adapter is initialized

## Best Practices

1. **Run drills regularly**: Execute drills on a scheduled basis (e.g., monthly)
2. **Document results**: Save execution records and evidence
3. **Review failures**: Investigate and fix any drill failures
4. **Update plans**: Keep DR plans current with infrastructure changes
5. **Test in isolation**: Run drills in test environments first
6. **Monitor RPO/RTO**: Track recovery point and time objectives

## Related Files

- Execution records: `{baseDir}/dr-executions.jsonl`
- Plan definitions: `{baseDir}/dr-plans.jsonl`
- Backup manifests: `{baseDir}/backup-manifest.jsonl`
- Queue files: `{baseDir}/queues/{queueName}.jsonl`

