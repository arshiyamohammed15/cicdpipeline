/**
 * Programmatic tests for DR drills
 * 
 * Tests backup-verify and queue-drain drills return PASS deterministically.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { LocalDRPlan } from '../../../../src/platform/adapters/local/LocalDRPlan';
import { LocalBackup } from '../../../../src/platform/adapters/local/LocalBackup';
import { LocalQueue, LocalDLQ } from '../../../../src/platform/adapters/local';

describe('LocalDRPlan Drills', () => {
  let tempDir: string;
  let backup: LocalBackup;
  let dlq: LocalDLQ;
  let queue: LocalQueue;
  let drPlan: LocalDRPlan;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'dr-drills-'));
    
    // Setup test resource
    const resourceDir = path.join(tempDir, 'resources', 'test-type', 'test-resource');
    fs.mkdirSync(resourceDir, { recursive: true });
    fs.writeFileSync(path.join(resourceDir, 'file1.txt'), 'test content 1');
    fs.writeFileSync(path.join(resourceDir, 'file2.txt'), 'test content 2');

    backup = new LocalBackup(tempDir);
    dlq = new LocalDLQ(tempDir);
    queue = new LocalQueue(tempDir, dlq);
    drPlan = new LocalDRPlan(tempDir, backup, queue);
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('backup-verify drill', () => {
    it('should PASS deterministically when backup is created and verified', async () => {
      const planId = await drPlan.createPlan({
        name: 'Backup Verify Drill',
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
        ],
      });

      // Test plan (dry run)
      const testResult = await drPlan.testPlan(planId);
      expect(testResult.status).toBe('passed');

      // Execute plan
      const executionResult = await drPlan.executePlan(planId);
      expect(executionResult.status).toBe('success');
      expect(executionResult.stepsExecuted.length).toBe(1);
      expect(executionResult.stepsExecuted[0].status).toBe('success');
      expect(executionResult.stepsExecuted[0].stepId).toBe('backup-verify');
    });

    it('should create valid backup with correct checksums', async () => {
      const planId = await drPlan.createPlan({
        name: 'Backup Verify Drill',
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
        ],
      });

      const executionResult = await drPlan.executePlan(planId);
      expect(executionResult.status).toBe('success');

      // Verify backup was created
      const backups = await backup.listBackups({
        resourceId: 'test-resource',
        resourceType: 'test-type',
      });
      expect(backups.length).toBeGreaterThan(0);

      const createdBackup = backups[0];
      expect(createdBackup.status).toBe('completed');

      // Verify backup integrity
      const verification = await backup.verifyBackup(createdBackup.id);
      expect(verification.status).toBe('valid');
    });

    it('should PASS when run multiple times with same inputs', async () => {
      const planId = await drPlan.createPlan({
        name: 'Backup Verify Drill',
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
        ],
      });

      // Run first time
      const result1 = await drPlan.executePlan(planId);
      expect(result1.status).toBe('success');

      // Run second time (should also pass)
      const result2 = await drPlan.executePlan(planId);
      expect(result2.status).toBe('success');

      // Both should have same step count
      expect(result1.stepsExecuted.length).toBe(result2.stepsExecuted.length);
      expect(result1.stepsExecuted[0].stepId).toBe(result2.stepsExecuted[0].stepId);
    });
  });

  describe('queue-drain drill', () => {
    it('should PASS deterministically when queue is drained', async () => {
      // Add messages to queue
      await queue.send('test-queue', 'message1');
      await queue.send('test-queue', 'message2');
      await queue.send('test-queue', 'message3');

      // Verify messages are in queue
      const attributesBefore = await queue.getAttributes('test-queue');
      expect(attributesBefore.approximateMessageCount).toBeGreaterThan(0);

      const planId = await drPlan.createPlan({
        name: 'Queue Drain Drill',
        primaryRegion: 'us-east-1',
        drRegion: 'us-west-2',
        rpoSeconds: 300,
        rtoSeconds: 600,
        steps: [
          {
            id: 'queue-drain',
            name: 'Drain Queue',
            order: 1,
            type: 'validate',
            config: {
              queueName: 'test-queue',
            },
          },
        ],
      });

      // Test plan (dry run)
      const testResult = await drPlan.testPlan(planId);
      expect(testResult.status).toBe('passed');

      // Execute plan
      const executionResult = await drPlan.executePlan(planId);
      expect(executionResult.status).toBe('success');
      expect(executionResult.stepsExecuted.length).toBe(1);
      expect(executionResult.stepsExecuted[0].status).toBe('success');
      expect(executionResult.stepsExecuted[0].stepId).toBe('queue-drain');

      // Verify queue is empty
      const attributesAfter = await queue.getAttributes('test-queue');
      expect(attributesAfter.approximateMessageCount).toBe(0);
    });

    it('should drain all messages regardless of count', async () => {
      // Add varying number of messages
      const messageCounts = [0, 1, 5, 10, 15];
      
      for (const count of messageCounts) {
        // Create new queue for each test
        const queueName = `test-queue-${count}`;
        
        // Add messages
        for (let i = 0; i < count; i++) {
          await queue.send(queueName, `message-${i}`);
        }

        const planId = await drPlan.createPlan({
          name: `Queue Drain Drill ${count}`,
          primaryRegion: 'us-east-1',
          drRegion: 'us-west-2',
          rpoSeconds: 300,
          rtoSeconds: 600,
          steps: [
            {
              id: 'queue-drain',
              name: 'Drain Queue',
              order: 1,
              type: 'validate',
              config: {
                queueName,
              },
            },
          ],
        });

        const executionResult = await drPlan.executePlan(planId);
        expect(executionResult.status).toBe('success');
        expect(executionResult.stepsExecuted[0].status).toBe('success');

        // Verify queue is empty
        const attributes = await queue.getAttributes(queueName);
        expect(attributes.approximateMessageCount).toBe(0);
      }
    });

    it('should PASS when run multiple times with same inputs', async () => {
      // Add messages
      await queue.send('test-queue', 'message1');
      await queue.send('test-queue', 'message2');

      const planId = await drPlan.createPlan({
        name: 'Queue Drain Drill',
        primaryRegion: 'us-east-1',
        drRegion: 'us-west-2',
        rpoSeconds: 300,
        rtoSeconds: 600,
        steps: [
          {
            id: 'queue-drain',
            name: 'Drain Queue',
            order: 1,
            type: 'validate',
            config: {
              queueName: 'test-queue',
            },
          },
        ],
      });

      // Run first time
      const result1 = await drPlan.executePlan(planId);
      expect(result1.status).toBe('success');

      // Add messages again
      await queue.send('test-queue', 'message3');
      await queue.send('test-queue', 'message4');

      // Run second time (should also pass)
      const result2 = await drPlan.executePlan(planId);
      expect(result2.status).toBe('success');

      // Both should have same step count
      expect(result1.stepsExecuted.length).toBe(result2.stepsExecuted.length);
      expect(result1.stepsExecuted[0].stepId).toBe(result2.stepsExecuted[0].stepId);

      // Queue should be empty after both runs
      const attributes = await queue.getAttributes('test-queue');
      expect(attributes.approximateMessageCount).toBe(0);
    });
  });

  describe('Combined drills', () => {
    it('should PASS both drills when executed together', async () => {
      // Setup: Add messages to queue
      await queue.send('test-queue', 'message1');
      await queue.send('test-queue', 'message2');

      const planId = await drPlan.createPlan({
        name: 'Combined DR Drill',
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

      // Test plan
      const testResult = await drPlan.testPlan(planId);
      expect(testResult.status).toBe('passed');

      // Execute plan
      const executionResult = await drPlan.executePlan(planId);
      expect(executionResult.status).toBe('success');
      expect(executionResult.stepsExecuted.length).toBe(2);
      expect(executionResult.stepsExecuted[0].status).toBe('success');
      expect(executionResult.stepsExecuted[1].status).toBe('success');

      // Verify backup was created
      const backups = await backup.listBackups({
        resourceId: 'test-resource',
        resourceType: 'test-type',
      });
      expect(backups.length).toBeGreaterThan(0);

      // Verify queue is empty
      const attributes = await queue.getAttributes('test-queue');
      expect(attributes.approximateMessageCount).toBe(0);
    });
  });
});

