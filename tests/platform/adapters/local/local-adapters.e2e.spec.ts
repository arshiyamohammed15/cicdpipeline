/**
 * E2E Tests for Local Adapters
 * 
 * Minimal tests using temp directories to verify all adapters work offline.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import {
  LocalQueue,
  LocalDLQ,
  LocalServerless,
  LocalGpuPool,
  LocalObjectStore,
  LocalBlockStore,
  LocalIngress,
  LocalObservability,
  LocalBackup,
  LocalDRPlan,
} from '../../../../src/platform/adapters/local';

describe('Local Adapters E2E', () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'local-adapters-'));
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('LocalQueue + LocalDLQ', () => {
    it('should send, receive, ack, and nack messages', async () => {
      const dlq = new LocalDLQ(tempDir);
      const queue = new LocalQueue(tempDir, dlq, 3, 5);

      // Send message
      const messageId = await queue.send('test-queue', 'test message');
      expect(messageId).toBeDefined();

      // Receive message
      const messages = await queue.receive('test-queue', 1);
      expect(messages.length).toBe(1);
      expect(messages[0].body).toBe('test message');

      // Ack message
      await queue.ack('test-queue', messages[0].receiptHandle);

      // Verify message deleted
      const afterAck = await queue.receive('test-queue', 1);
      expect(afterAck.length).toBe(0);
    });

    it('should move to DLQ after max retries', async () => {
      const dlq = new LocalDLQ(tempDir);
      const queue = new LocalQueue(tempDir, dlq, 2, 1);

      // Send message
      await queue.send('test-queue', 'test message');

      // Receive and nack until max retries exceeded
      let retries = 0;
      let movedToDLQ = false;
      
      while (retries < 5 && !movedToDLQ) {
        const messages = await queue.receive('test-queue', 1, { waitTimeSeconds: 1 });
        if (messages.length === 0) {
          // Wait for backoff to expire
          await new Promise(resolve => setTimeout(resolve, 2000));
          continue;
        }
        
        const msg = messages[0];
        if (msg.receiveCount && msg.receiveCount >= 2) {
          // This should move to DLQ
          await queue.nack('test-queue', msg.receiptHandle, true);
          movedToDLQ = true;
        } else {
          await queue.nack('test-queue', msg.receiptHandle, true);
          retries++;
          // Wait for backoff
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }

      // Check DLQ
      const dlqMessages = await dlq.receiveFailedMessages('test-queue', 1);
      expect(dlqMessages.length).toBe(1);
    });
  });

  describe('LocalServerless', () => {
    it('should invoke function from registry', async () => {
      const functionsDir = path.join(tempDir, 'functions');
      fs.mkdirSync(functionsDir, { recursive: true });

      // Create a simple function
      const functionCode = `(payload) => { return payload.value * 2; }`;
      fs.writeFileSync(path.join(functionsDir, 'double.js'), functionCode);

      const serverless = new LocalServerless(functionsDir, path.join(tempDir, 'logs.jsonl'));

      const result = await serverless.invoke('double', { value: 5 });
      expect(result.status).toBe('success');
      expect(result.payload).toEqual(10);
    });
  });

  describe('LocalGpuPool', () => {
    it('should allocate and release GPU instances', async () => {
      const pool = new LocalGpuPool(4, ['t4'], 't4', 16, 100);

      const instance = await pool.allocate({
        minGpus: 2,
        gpuType: 't4',
      });

      expect(instance.gpuCount).toBe(2);

      const stats = await pool.getPoolStats();
      expect(stats.allocatedGpus).toBe(2);
      expect(stats.availableGpus).toBe(2);

      await pool.release(instance.id);
      const statsAfter = await pool.getPoolStats();
      expect(statsAfter.availableGpus).toBe(4);
    });
  });

  describe('LocalObjectStore', () => {
    it('should put, get, and delete objects', async () => {
      const store = new LocalObjectStore(tempDir);

      // Put object
      const putResult = await store.put('test-bucket', 'test-key', 'test data');
      expect(putResult.key).toBe('test-key');
      expect(putResult.size).toBeGreaterThan(0);

      // Get object
      const getResult = await store.get('test-bucket', 'test-key');
      expect(getResult.data.toString()).toBe('test data');

      // Delete object
      await store.delete('test-bucket', 'test-key');

      // Verify deleted
      await expect(store.get('test-bucket', 'test-key')).rejects.toThrow();
    });

    it('should list objects with prefix', async () => {
      const store = new LocalObjectStore(tempDir);

      await store.put('test-bucket', 'prefix1/key1', 'data1');
      await store.put('test-bucket', 'prefix1/key2', 'data2');
      await store.put('test-bucket', 'prefix2/key1', 'data3');

      const listResult = await store.list('test-bucket', 'prefix1');
      expect(listResult.keys.length).toBe(2);
      expect(listResult.keys).toContain('prefix1/key1');
      expect(listResult.keys).toContain('prefix1/key2');
    });
  });

  describe('LocalBlockStore', () => {
    it('should create, attach, and delete volumes', async () => {
      const store = new LocalBlockStore(tempDir);

      const volume = await store.createVolume({
        sizeGB: 10,
        volumeType: 'standard',
      });

      expect(volume.sizeGB).toBe(10);
      expect(volume.status).toBe('available');

      const attachment = await store.attachVolume(volume.id, 'instance-1', '/dev/sdf');
      expect(attachment.status).toBe('attached');

      const volumeAfter = await store.getVolume(volume.id);
      expect(volumeAfter.status).toBe('in-use');
      expect(volumeAfter.attachments.length).toBe(1);

      await store.detachVolume(volume.id, 'instance-1');
      const volumeDetached = await store.getVolume(volume.id);
      expect(volumeDetached.status).toBe('available');

      await store.deleteVolume(volume.id);
      await expect(store.getVolume(volume.id)).rejects.toThrow();
    });
  });

  describe('LocalIngress', () => {
    it('should create, list, and delete ingress rules', async () => {
      const ingress = new LocalIngress(tempDir);

      const ruleId = await ingress.createRule({
        host: 'example.com',
        path: '/api',
        target: {
          type: 'service',
          identifier: 'api-service',
          port: 8080,
        },
      });

      expect(ruleId).toBeDefined();

      const rule = await ingress.getRule(ruleId);
      expect(rule.host).toBe('example.com');

      const rules = await ingress.listRules();
      expect(rules.length).toBe(1);

      await ingress.deleteRule(ruleId);
      const rulesAfter = await ingress.listRules();
      expect(rulesAfter.length).toBe(0);
    });
  });

  describe('LocalObservability', () => {
    it('should emit metrics and query them', async () => {
      const observability = new LocalObservability(tempDir);

      await observability.emitMetric({
        name: 'test.metric',
        value: 100,
        unit: 'count',
      });

      const queryResult = await observability.queryMetrics({
        metricName: 'test.metric',
        startTime: new Date(Date.now() - 60000),
        endTime: new Date(),
      });

      expect(queryResult.results.length).toBeGreaterThan(0);
      expect(queryResult.results[0].value).toBe(100);
    });

    it('should write and query logs', async () => {
      const observability = new LocalObservability(tempDir);

      await observability.writeLog({
        level: 'info',
        message: 'Test log message',
        source: 'test-service',
      });

      const queryResult = await observability.queryLogs({
        startTime: new Date(Date.now() - 60000),
        endTime: new Date(),
        level: 'info',
      });

      expect(queryResult.results.length).toBeGreaterThan(0);
      expect(queryResult.results[0].message).toBe('Test log message');
    });
  });

  describe('LocalBackup', () => {
    it('should create, verify, and restore backup', async () => {
      // Create test resource
      const resourceDir = path.join(tempDir, 'resources', 'test-type', 'test-resource');
      fs.mkdirSync(resourceDir, { recursive: true });
      fs.writeFileSync(path.join(resourceDir, 'file1.txt'), 'test content 1');
      fs.writeFileSync(path.join(resourceDir, 'file2.txt'), 'test content 2');

      const backup = new LocalBackup(tempDir);

      const backupResult = await backup.createBackup({
        resourceId: 'test-resource',
        resourceType: 'test-type',
        name: 'test-backup',
      });

      expect(backupResult.status).toBe('completed');
      expect(backupResult.sizeBytes).toBeGreaterThan(0);

      // Verify backup
      const verification = await backup.verifyBackup(backupResult.id);
      expect(verification.status).toBe('valid');

      // Restore backup
      const restoreDir = path.join(tempDir, 'restore');
      fs.mkdirSync(restoreDir, { recursive: true });

      const restoreResult = await backup.restoreBackup(backupResult.id, {
        targetResourceId: 'restored-resource',
        overwrite: true,
      });

      expect(restoreResult.status).toBe('success');
    });
  });

  describe('LocalDRPlan', () => {
    it('should create and execute DR plan with backup-verify and queue-drain drills', async () => {
      // Setup: Create test resource and queue
      const resourceDir = path.join(tempDir, 'resources', 'test-type', 'test-resource');
      fs.mkdirSync(resourceDir, { recursive: true });
      fs.writeFileSync(path.join(resourceDir, 'file.txt'), 'test content');

      const dlq = new LocalDLQ(tempDir);
      const queue = new LocalQueue(tempDir, dlq);
      const backup = new LocalBackup(tempDir);

      // Create backup first
      const backupResult = await backup.createBackup({
        resourceId: 'test-resource',
        resourceType: 'test-type',
      });

      // Add messages to queue
      await queue.send('test-queue', 'message1');
      await queue.send('test-queue', 'message2');

      const drPlan = new LocalDRPlan(tempDir, backup, queue);

      const planId = await drPlan.createPlan({
        name: 'test-plan',
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

      // Verify queue is drained
      const messages = await queue.receive('test-queue', 10);
      expect(messages.length).toBe(0);
    });
  });
});

