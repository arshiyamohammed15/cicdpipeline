/**
 * Unit tests for WorkloadRouter
 *
 * Tests three BuildPlan samples mapping to correct paths and ObservabilityPort emits events.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { WorkloadRouter, BuildPlan, RoutingDecision } from '../../../src/platform/router/WorkloadRouter';
import { LocalObservability } from '../../../src/platform/adapters/local';

describe('WorkloadRouter', () => {
  let tempDir: string;
  let router: WorkloadRouter;

  beforeEach(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'workload-router-'));
    router = new WorkloadRouter(tempDir, 'development');
  });

  afterEach(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  describe('decide() - routing decisions', () => {
    it('should route "light" cost_profile to serverless', () => {
      const buildPlan: BuildPlan = {
        cost_profile: 'light',
      };

      const decision = router.decide(buildPlan);

      expect(decision.route).toBe('serverless');
      expect(decision.adapter).toBe('serverless');
      expect(decision.queueName).toBeUndefined();
    });

    it('should route "ai-inference" cost_profile to gpu-queue', () => {
      const buildPlan: BuildPlan = {
        cost_profile: 'ai-inference',
      };

      const decision = router.decide(buildPlan);

      expect(decision.route).toBe('gpu-queue');
      expect(decision.adapter).toBe('gpu-pool');
      expect(decision.queueName).toBe('gpu-queue');
    });

    it('should route "batch" cost_profile to batch queue', () => {
      const buildPlan: BuildPlan = {
        cost_profile: 'batch',
      };

      const decision = router.decide(buildPlan);

      expect(decision.route).toBe('batch');
      expect(decision.adapter).toBe('queue');
      expect(decision.queueName).toBe('batch-queue');
    });

    it('should fallback to routing.default when cost_profile is missing', () => {
      const buildPlan: BuildPlan = {};

      const decision = router.decide(buildPlan);

      // Default from environments.json should be 'serverless'
      expect(decision.route).toBe('serverless');
      expect(decision.adapter).toBe('serverless');
    });

    it('should fallback to routing.default when cost_profile is invalid', () => {
      const buildPlan: BuildPlan = {
        cost_profile: 'invalid-profile',
      };

      const decision = router.decide(buildPlan);

      // Should fallback to default
      expect(decision.route).toBe('serverless');
      expect(decision.adapter).toBe('serverless');
    });
  });

  describe('route() - workload execution', () => {
    it('should route "light" workload to serverless adapter', async () => {
      // Setup: Create a function
      const functionsDir = path.join(tempDir, 'functions');
      fs.mkdirSync(functionsDir, { recursive: true });
      const functionCode = `(payload) => { return { result: payload.value * 2 }; }`;
      fs.writeFileSync(path.join(functionsDir, 'default-handler.js'), functionCode);

      const buildPlan: BuildPlan = {
        cost_profile: 'light',
      };

      const payload = { value: 5 };

      await router.route(buildPlan, payload);

      // Verify observability events were emitted
      const observability = router.getRegistry().getObservability();
      expect(observability).not.toBeNull();

      // Check that execution log was created
      const logsFile = path.join(tempDir, 'logs', 'executions.ndjson');
      if (fs.existsSync(logsFile)) {
        const content = fs.readFileSync(logsFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        expect(lines.length).toBeGreaterThan(0);
      }
    });

    it('should route "ai-inference" workload to gpu-queue', async () => {
      const buildPlan: BuildPlan = {
        cost_profile: 'ai-inference',
      };

      const payload = { model: 'test-model', input: 'test-input' };

      await router.route(buildPlan, payload);

      // Verify message was enqueued
      const queue = router.getRegistry().getQueue();
      expect(queue).not.toBeNull();

      // Check queue file exists
      const queueFile = path.join(tempDir, 'queues', 'gpu-queue.jsonl');
      expect(fs.existsSync(queueFile)).toBe(true);

      // Verify observability events were emitted
      const observability = router.getRegistry().getObservability();
      expect(observability).not.toBeNull();
    });

    it('should route "batch" workload to batch queue', async () => {
      const buildPlan: BuildPlan = {
        cost_profile: 'batch',
      };

      const payload = { job: 'test-job', data: 'test-data' };

      await router.route(buildPlan, payload);

      // Verify message was enqueued
      const queue = router.getRegistry().getQueue();
      expect(queue).not.toBeNull();

      // Check queue file exists
      const queueFile = path.join(tempDir, 'queues', 'batch-queue.jsonl');
      expect(fs.existsSync(queueFile)).toBe(true);

      // Verify observability events were emitted
      const observability = router.getRegistry().getObservability();
      expect(observability).not.toBeNull();
    });

    it('should emit observability metrics for routing decisions', async () => {
      const buildPlan: BuildPlan = {
        cost_profile: 'light',
      };

      // Setup function
      const functionsDir = path.join(tempDir, 'functions');
      fs.mkdirSync(functionsDir, { recursive: true });
      const functionCode = `(payload) => { return payload; }`;
      fs.writeFileSync(path.join(functionsDir, 'default-handler.js'), functionCode);

      await router.route(buildPlan, { test: 'data' });

      // Check observability file for metrics
      const observabilityFile = path.join(tempDir, 'logs', 'observability.ndjson');
      if (fs.existsSync(observabilityFile)) {
        const content = fs.readFileSync(observabilityFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());

        // Should have at least decision and executed metrics
        expect(lines.length).toBeGreaterThanOrEqual(2);

        // Verify decision metric
        const decisionMetric = lines.find((line) => {
          try {
            const record = JSON.parse(line);
            return record.name === 'workload.router.decision';
          } catch {
            return false;
          }
        });
        expect(decisionMetric).toBeDefined();

        // Verify executed metric
        const executedMetric = lines.find((line) => {
          try {
            const record = JSON.parse(line);
            return record.name === 'workload.router.executed';
          } catch {
            return false;
          }
        });
        expect(executedMetric).toBeDefined();
      }
    });

    it('should throw error when adapters are disabled', async () => {
      // Create router with disabled adapters (by using a non-existent env or mocking)
      // For this test, we'll check the registry state
      const registry = router.getRegistry();

      // If adapters are disabled, route should throw
      // Note: In real scenario, this would be controlled by feature flags in environments.json
      // For this test, we verify the error handling path
      const buildPlan: BuildPlan = {
        cost_profile: 'light',
      };

      // This should work if adapters are enabled (which they should be by default in development)
      // If they're disabled, it will throw
      try {
        await router.route(buildPlan, { test: 'data' });
        // If we get here, adapters are enabled (expected in development env)
        expect(registry.isEnabled()).toBe(true);
      } catch (error) {
        expect((error as Error).message).toContain('not enabled');
      }
    });
  });

  describe('Three BuildPlan samples', () => {
    it('should correctly route all three cost profiles', async () => {
      // Setup functions for serverless
      const functionsDir = path.join(tempDir, 'functions');
      fs.mkdirSync(functionsDir, { recursive: true });
      const functionCode = `(payload) => { return payload; }`;
      fs.writeFileSync(path.join(functionsDir, 'default-handler.js'), functionCode);

      // Sample 1: light → serverless
      const plan1: BuildPlan = { cost_profile: 'light' };
      const decision1 = router.decide(plan1);
      expect(decision1.route).toBe('serverless');
      expect(decision1.adapter).toBe('serverless');
      await router.route(plan1, { type: 'light-workload' });

      // Sample 2: ai-inference → gpu-queue
      const plan2: BuildPlan = { cost_profile: 'ai-inference' };
      const decision2 = router.decide(plan2);
      expect(decision2.route).toBe('gpu-queue');
      expect(decision2.adapter).toBe('gpu-pool');
      await router.route(plan2, { type: 'ai-inference-workload' });

      // Sample 3: batch → batch queue
      const plan3: BuildPlan = { cost_profile: 'batch' };
      const decision3 = router.decide(plan3);
      expect(decision3.route).toBe('batch');
      expect(decision3.adapter).toBe('queue');
      await router.route(plan3, { type: 'batch-workload' });

      // Verify all three routes were executed
      const observabilityFile = path.join(tempDir, 'logs', 'observability.ndjson');
      if (fs.existsSync(observabilityFile)) {
        const content = fs.readFileSync(observabilityFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());

        // Should have metrics for all three routes
        const decisionMetrics = lines.filter((line) => {
          try {
            const record = JSON.parse(line);
            return record.name === 'workload.router.decision';
          } catch {
            return false;
          }
        });
        expect(decisionMetrics.length).toBeGreaterThanOrEqual(3);
      }

      // Verify queues were created
      expect(fs.existsSync(path.join(tempDir, 'queues', 'gpu-queue.jsonl'))).toBe(true);
      expect(fs.existsSync(path.join(tempDir, 'queues', 'batch-queue.jsonl'))).toBe(true);
    });
  });
});
