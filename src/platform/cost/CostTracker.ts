/**
 * CostTracker
 *
 * Emits metrics/events and tracks costs based on duration * tier multiplier.
 * Writes to metrics.ndjson (append-only, deterministic).
 */

import * as fs from 'fs';
import * as path from 'path';
import { ObservabilityPort } from '../ports/ObservabilityPort';
import { InfraConfig, loadInfraConfig } from '../../../config/InfraConfig';

/**
 * Cost tier multipliers based on cost profiles
 */
const COST_TIER_MULTIPLIERS: Record<string, number> = {
  'light': 1.0,
  'ai-inference': 10.0,
  'batch': 0.5,
  'serverless': 1.0,
  'gpu-queue': 10.0,
  'batch-queue': 0.5,
};

/**
 * Cost metric record
 */
interface CostMetricRecord {
  name: string;
  value: number;
  unit: string;
  timestamp: number;
  dimensions: {
    operation: string;
    tier?: string;
    duration_ms?: number;
    cost?: number;
  };
  type: 'counter' | 'histogram' | 'gauge';
}

export class CostTracker {
  private observability: ObservabilityPort;
  private metricsFile: string;
  private envName: string;
  private infraConfig: InfraConfig | null = null;

  constructor(observability: ObservabilityPort, baseDir: string, envName: string = 'development') {
    this.observability = observability;
    this.metricsFile = path.join(baseDir, 'metrics.ndjson');
    this.envName = envName;
    this.loadInfraConfig();
  }

  /**
   * Emit serverless.invoke metric and cost
   */
  async trackServerlessInvoke(durationMs: number, tier: string = 'light'): Promise<void> {
    const cost = this.calculateCost(durationMs, tier);

    await this.emitCounter('serverless.invoke', {
      operation: 'invoke',
      tier,
      duration_ms: durationMs,
      cost,
    });

    await this.emitHistogram('serverless.invoke.duration', durationMs, {
      operation: 'invoke',
      tier,
    });

    await this.emitCostMetric('serverless.invoke', durationMs, tier, cost);
  }

  /**
   * Emit gpu.submit metric and cost
   */
  async trackGpuSubmit(durationMs: number, tier: string = 'ai-inference'): Promise<void> {
    const cost = this.calculateCost(durationMs, tier);

    await this.emitCounter('gpu.submit', {
      operation: 'submit',
      tier,
      duration_ms: durationMs,
      cost,
    });

    await this.emitHistogram('gpu.submit.duration', durationMs, {
      operation: 'submit',
      tier,
    });

    await this.emitCostMetric('gpu.submit', durationMs, tier, cost);
  }

  /**
   * Emit queue.enqueue metric
   */
  async trackQueueEnqueue(queueName: string): Promise<void> {
    await this.emitCounter('queue.enqueue', {
      operation: 'enqueue',
      queue_name: queueName,
    });
  }

  /**
   * Emit queue.ack metric
   */
  async trackQueueAck(queueName: string): Promise<void> {
    await this.emitCounter('queue.ack', {
      operation: 'ack',
      queue_name: queueName,
    });
  }

  /**
   * Emit queue.nack metric
   */
  async trackQueueNack(queueName: string): Promise<void> {
    await this.emitCounter('queue.nack', {
      operation: 'nack',
      queue_name: queueName,
    });
  }

  /**
   * Emit queue.retry metric
   */
  async trackQueueRetry(queueName: string): Promise<void> {
    await this.emitCounter('queue.retry', {
      operation: 'retry',
      queue_name: queueName,
    });
  }

  /**
   * Emit queue.dlq metric
   */
  async trackQueueDlq(queueName: string): Promise<void> {
    await this.emitCounter('queue.dlq', {
      operation: 'dlq',
      queue_name: queueName,
    });
  }

  /**
   * Emit backup.snapshot metric and cost
   */
  async trackBackupSnapshot(durationMs: number, sizeBytes: number): Promise<void> {
    const cost = this.calculateCost(durationMs, 'batch');

    await this.emitCounter('backup.snapshot', {
      operation: 'snapshot',
      duration_ms: durationMs,
      size_bytes: sizeBytes,
      cost,
    });

    await this.emitHistogram('backup.snapshot.duration', durationMs, {
      operation: 'snapshot',
    });

    await this.emitHistogram('backup.snapshot.size', sizeBytes, {
      operation: 'snapshot',
    });

    await this.emitCostMetric('backup.snapshot', durationMs, 'batch', cost);
  }

  /**
   * Emit backup.verify metric and cost
   */
  async trackBackupVerify(durationMs: number): Promise<void> {
    const cost = this.calculateCost(durationMs, 'batch');

    await this.emitCounter('backup.verify', {
      operation: 'verify',
      duration_ms: durationMs,
      cost,
    });

    await this.emitHistogram('backup.verify.duration', durationMs, {
      operation: 'verify',
    });

    await this.emitCostMetric('backup.verify', durationMs, 'batch', cost);
  }

  /**
   * Calculate cost: duration (ms) * tier multiplier
   */
  private calculateCost(durationMs: number, tier: string): number {
    const multiplier = COST_TIER_MULTIPLIERS[tier] || 1.0;
    // Cost = duration in seconds * multiplier
    const durationSeconds = durationMs / 1000;
    return durationSeconds * multiplier;
  }

  /**
   * Emit counter metric
   */
  private async emitCounter(name: string, dimensions: Record<string, unknown>): Promise<void> {
    await this.observability.emitMetric({
      name,
      value: 1,
      unit: 'count',
      type: 'counter',
      dimensions: dimensions as Record<string, string>,
      timestamp: new Date(),
    });
  }

  /**
   * Emit histogram metric
   */
  private async emitHistogram(name: string, value: number, dimensions: Record<string, unknown>): Promise<void> {
    await this.observability.emitMetric({
      name,
      value,
      unit: 'ms',
      type: 'histogram',
      dimensions: dimensions as Record<string, string>,
      timestamp: new Date(),
    });
  }

  /**
   * Emit cost metric to metrics.ndjson
   */
  private async emitCostMetric(operation: string, durationMs: number, tier: string, cost: number): Promise<void> {
    const record: CostMetricRecord = {
      name: `${operation}.cost`,
      value: cost,
      unit: 'cost_units',
      timestamp: this.getMonotonicTime(),
      dimensions: {
        operation,
        tier,
        duration_ms: durationMs,
        cost,
      },
      type: 'gauge',
    };

    await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
  }

  /**
   * Load infra config for cost calculations
   */
  private loadInfraConfig(): void {
    try {
      const result = loadInfraConfig(this.envName);
      this.infraConfig = result.config;
    } catch (error) {
      // Use defaults if config cannot be loaded
      this.infraConfig = null;
    }
  }

  /**
   * Append to JSONL file (append-only)
   */
  private async appendToJsonl(filePath: string, jsonContent: string): Promise<void> {
    await this.ensureDirectory(path.dirname(filePath));

    try {
      await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err.code !== 'EEXIST') {
        throw err;
      }
    }

    const line = `${jsonContent}\n`;
    const handle = await fs.promises.open(filePath, 'a');
    try {
      await handle.write(line);
      await handle.sync();
    } finally {
      await handle.close();
    }
  }

  private async ensureDirectory(dirPath: string): Promise<void> {
    await fs.promises.mkdir(dirPath, { recursive: true });
  }

  private getMonotonicTime(): number {
    return Date.now();
  }
}
