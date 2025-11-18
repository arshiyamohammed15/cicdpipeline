/**
 * Deterministic tests for CostTracker
 *
 * Tests event counts and cost totals.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { CostTracker } from '../../../src/platform/cost/CostTracker';
import { CostReporter, CostSummary } from '../../../src/platform/cost/CostReporter';
import { LocalObservability } from '../../../src/platform/adapters/local/LocalObservability';

describe('CostTracker', () => {
  let tempDir: string;
  let observability: LocalObservability;
  let costTracker: CostTracker;
  let costReporter: CostReporter;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cost-tracker-'));
    observability = new LocalObservability(tempDir);
    costTracker = new CostTracker(observability, tempDir, 'development');
    costReporter = new CostReporter(tempDir);
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('Event counts', () => {
    it('should emit correct count for serverless.invoke', async () => {
      await costTracker.trackServerlessInvoke(100, 'light');
      await costTracker.trackServerlessInvoke(200, 'light');
      await costTracker.trackServerlessInvoke(150, 'light');

      const summary = costReporter.generateSummary(100);
      const serverlessOp = summary.operations.find((op) => op.operation === 'serverless.invoke');

      expect(serverlessOp).toBeDefined();
      expect(serverlessOp!.count).toBe(3);
    });

    it('should emit correct count for gpu.submit', async () => {
      await costTracker.trackGpuSubmit(500, 'ai-inference');
      await costTracker.trackGpuSubmit(600, 'ai-inference');

      const summary = costReporter.generateSummary(100);
      const gpuOp = summary.operations.find((op) => op.operation === 'gpu.submit');

      expect(gpuOp).toBeDefined();
      expect(gpuOp!.count).toBe(2);
    });

    it('should emit correct counts for queue operations', async () => {
      await costTracker.trackQueueEnqueue('test-queue');
      await costTracker.trackQueueEnqueue('test-queue');
      await costTracker.trackQueueAck('test-queue');
      await costTracker.trackQueueNack('test-queue');
      await costTracker.trackQueueRetry('test-queue');
      await costTracker.trackQueueDlq('test-queue');

      // Check observability file for counters
      const observabilityFile = path.join(tempDir, 'logs', 'observability.ndjson');
      if (fs.existsSync(observabilityFile)) {
        const content = fs.readFileSync(observabilityFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());

        const enqueueCount = lines.filter((line) => {
          try {
            const record = JSON.parse(line);
            return record.name === 'queue.enqueue';
          } catch {
            return false;
          }
        }).length;

        const ackCount = lines.filter((line) => {
          try {
            const record = JSON.parse(line);
            return record.name === 'queue.ack';
          } catch {
            return false;
          }
        }).length;

        expect(enqueueCount).toBe(2);
        expect(ackCount).toBe(1);
      }
    });

    it('should emit correct counts for backup operations', async () => {
      await costTracker.trackBackupSnapshot(1000, 1024 * 1024);
      await costTracker.trackBackupSnapshot(2000, 2048 * 1024);
      await costTracker.trackBackupVerify(500);

      const summary = costReporter.generateSummary(100);
      const snapshotOp = summary.operations.find((op) => op.operation === 'backup.snapshot');
      const verifyOp = summary.operations.find((op) => op.operation === 'backup.verify');

      expect(snapshotOp).toBeDefined();
      expect(snapshotOp!.count).toBe(2);
      expect(verifyOp).toBeDefined();
      expect(verifyOp!.count).toBe(1);
    });
  });

  describe('Cost totals', () => {
    it('should calculate correct cost for serverless.invoke (light tier)', async () => {
      // Light tier multiplier = 1.0
      // Cost = duration (seconds) * multiplier
      await costTracker.trackServerlessInvoke(1000, 'light'); // 1 second * 1.0 = 1.0
      await costTracker.trackServerlessInvoke(2000, 'light'); // 2 seconds * 1.0 = 2.0

      const summary = costReporter.generateSummary(100);
      const serverlessOp = summary.operations.find((op) => op.operation === 'serverless.invoke');

      expect(serverlessOp).toBeDefined();
      expect(serverlessOp!.totalCost).toBeCloseTo(3.0, 2); // 1.0 + 2.0
    });

    it('should calculate correct cost for gpu.submit (ai-inference tier)', async () => {
      // AI-inference tier multiplier = 10.0
      // Cost = duration (seconds) * multiplier
      await costTracker.trackGpuSubmit(1000, 'ai-inference'); // 1 second * 10.0 = 10.0
      await costTracker.trackGpuSubmit(500, 'ai-inference'); // 0.5 seconds * 10.0 = 5.0

      const summary = costReporter.generateSummary(100);
      const gpuOp = summary.operations.find((op) => op.operation === 'gpu.submit');

      expect(gpuOp).toBeDefined();
      expect(gpuOp!.totalCost).toBeCloseTo(15.0, 2); // 10.0 + 5.0
    });

    it('should calculate correct cost for backup.snapshot (batch tier)', async () => {
      // Batch tier multiplier = 0.5
      // Cost = duration (seconds) * multiplier
      await costTracker.trackBackupSnapshot(2000, 1024 * 1024); // 2 seconds * 0.5 = 1.0
      await costTracker.trackBackupSnapshot(4000, 2048 * 1024); // 4 seconds * 0.5 = 2.0

      const summary = costReporter.generateSummary(100);
      const snapshotOp = summary.operations.find((op) => op.operation === 'backup.snapshot');

      expect(snapshotOp).toBeDefined();
      expect(snapshotOp!.totalCost).toBeCloseTo(3.0, 2); // 1.0 + 2.0
    });

    it('should calculate correct total cost across all operations', async () => {
      await costTracker.trackServerlessInvoke(1000, 'light'); // 1.0
      await costTracker.trackGpuSubmit(1000, 'ai-inference'); // 10.0
      await costTracker.trackBackupSnapshot(2000, 1024 * 1024); // 1.0
      await costTracker.trackBackupVerify(1000); // 0.5

      const summary = costReporter.generateSummary(100);

      expect(summary.totalCost).toBeCloseTo(12.5, 2); // 1.0 + 10.0 + 1.0 + 0.5
      expect(summary.totalOperations).toBe(4);
    });

    it('should aggregate costs by tier correctly', async () => {
      await costTracker.trackServerlessInvoke(1000, 'light'); // 1.0
      await costTracker.trackServerlessInvoke(2000, 'light'); // 2.0
      await costTracker.trackGpuSubmit(1000, 'ai-inference'); // 10.0
      await costTracker.trackGpuSubmit(500, 'ai-inference'); // 5.0
      await costTracker.trackBackupSnapshot(2000, 1024 * 1024); // 1.0

      const summary = costReporter.generateSummary(100);

      expect(summary.byTier['light']).toBeDefined();
      expect(summary.byTier['light'].totalCost).toBeCloseTo(3.0, 2); // 1.0 + 2.0
      expect(summary.byTier['light'].count).toBe(2);

      expect(summary.byTier['ai-inference']).toBeDefined();
      expect(summary.byTier['ai-inference'].totalCost).toBeCloseTo(15.0, 2); // 10.0 + 5.0
      expect(summary.byTier['ai-inference'].count).toBe(2);

      expect(summary.byTier['batch']).toBeDefined();
      expect(summary.byTier['batch'].totalCost).toBeCloseTo(1.0, 2);
      expect(summary.byTier['batch'].count).toBe(1);
    });
  });

  describe('CostReporter', () => {
    it('should generate summary from last N entries', async () => {
      // Generate more than N entries
      for (let i = 0; i < 150; i++) {
        await costTracker.trackServerlessInvoke(100, 'light');
      }

      const summary = costReporter.generateSummary(100);

      // Should only include last 100 entries
      expect(summary.totalOperations).toBe(100);
    });

    it('should return empty summary when no metrics exist', () => {
      const summary = costReporter.generateSummary(100);

      expect(summary.totalCost).toBe(0);
      expect(summary.totalOperations).toBe(0);
      expect(summary.operations).toEqual([]);
      expect(summary.byTier).toEqual({});
    });

    it('should produce valid JSON summary', async () => {
      await costTracker.trackServerlessInvoke(1000, 'light');
      await costTracker.trackGpuSubmit(1000, 'ai-inference');

      const json = costReporter.getSummaryJson(100);
      const summary: CostSummary = JSON.parse(json);

      expect(summary.totalCost).toBeGreaterThan(0);
      expect(summary.totalOperations).toBe(2);
      expect(Array.isArray(summary.operations)).toBe(true);
      expect(typeof summary.byTier).toBe('object');
      expect(typeof summary.timestamp).toBe('number');
    });

    it('should calculate average costs correctly', async () => {
      await costTracker.trackServerlessInvoke(1000, 'light'); // 1.0
      await costTracker.trackServerlessInvoke(2000, 'light'); // 2.0
      await costTracker.trackServerlessInvoke(3000, 'light'); // 3.0

      const summary = costReporter.generateSummary(100);
      const serverlessOp = summary.operations.find((op) => op.operation === 'serverless.invoke');

      expect(serverlessOp).toBeDefined();
      expect(serverlessOp!.averageCost).toBeCloseTo(2.0, 2); // (1.0 + 2.0 + 3.0) / 3
      expect(serverlessOp!.averageDurationMs).toBeCloseTo(2000, 0); // (1000 + 2000 + 3000) / 3
    });
  });

  describe('Deterministic behavior', () => {
    it('should produce same cost totals for same inputs', async () => {
      await costTracker.trackServerlessInvoke(1000, 'light');
      await costTracker.trackGpuSubmit(1000, 'ai-inference');
      await costTracker.trackBackupSnapshot(2000, 1024 * 1024);

      const summary1 = costReporter.generateSummary(100);
      const totalCost1 = summary1.totalCost;

      // Use a separate directory for the second run to avoid appending
      const tempDir2 = fs.mkdtempSync(path.join(os.tmpdir(), 'cost-tracker-2-'));
      const observability2 = new LocalObservability(tempDir2);
      const costTracker2 = new CostTracker(observability2, tempDir2, 'development');
      const costReporter2 = new CostReporter(tempDir2);

      // Replay same operations
      await costTracker2.trackServerlessInvoke(1000, 'light');
      await costTracker2.trackGpuSubmit(1000, 'ai-inference');
      await costTracker2.trackBackupSnapshot(2000, 1024 * 1024);

      const summary2 = costReporter2.generateSummary(100);
      const totalCost2 = summary2.totalCost;

      // Should produce same totals (within floating point precision)
      expect(totalCost1).toBeCloseTo(totalCost2, 2);

      // Cleanup
      if (fs.existsSync(tempDir2)) {
        fs.rmSync(tempDir2, { recursive: true, force: true });
      }
    });
  });
});
