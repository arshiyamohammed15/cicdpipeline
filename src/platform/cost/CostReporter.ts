/**
 * CostReporter
 *
 * Aggregates last N entries from metrics.ndjson to produce a JSON cost summary.
 */

import * as fs from 'fs';
import * as path from 'path';

/**
 * Cost metric record (matches CostTracker format)
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

/**
 * Cost summary by operation
 */
export interface OperationCostSummary {
  operation: string;
  count: number;
  totalCost: number;
  totalDurationMs: number;
  averageCost: number;
  averageDurationMs: number;
}

/**
 * Overall cost summary
 */
export interface CostSummary {
  totalCost: number;
  totalOperations: number;
  operations: OperationCostSummary[];
  byTier: Record<string, { count: number; totalCost: number }>;
  timestamp: number;
}

export class CostReporter {
  private metricsFile: string;

  constructor(baseDir: string) {
    this.metricsFile = path.join(baseDir, 'metrics.ndjson');
  }

  /**
   * Generate cost summary from last N entries
   */
  generateSummary(lastN: number = 100): CostSummary {
    if (!fs.existsSync(this.metricsFile)) {
      return {
        totalCost: 0,
        totalOperations: 0,
        operations: [],
        byTier: {},
        timestamp: Date.now(),
      };
    }

    const content = fs.readFileSync(this.metricsFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());

    // Get last N entries
    const recentLines = lines.slice(-lastN);
    const records: CostMetricRecord[] = [];

    for (const line of recentLines) {
      try {
        const record: CostMetricRecord = JSON.parse(line);
        // Only include cost metrics
        if (record.name.endsWith('.cost') && record.dimensions.cost !== undefined) {
          records.push(record);
        }
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    // Aggregate by operation
    const operationMap = new Map<string, {
      count: number;
      totalCost: number;
      totalDurationMs: number;
    }>();

    const tierMap = new Map<string, {
      count: number;
      totalCost: number;
    }>();

    let totalCost = 0;
    let totalOperations = 0;

    for (const record of records) {
      const operation = record.dimensions.operation;
      const cost = record.dimensions.cost || 0;
      const durationMs = record.dimensions.duration_ms || 0;
      const tier = record.dimensions.tier || 'unknown';

      totalCost += cost;
      totalOperations += 1;

      // Aggregate by operation
      if (!operationMap.has(operation)) {
        operationMap.set(operation, {
          count: 0,
          totalCost: 0,
          totalDurationMs: 0,
        });
      }

      const opData = operationMap.get(operation)!;
      opData.count += 1;
      opData.totalCost += cost;
      opData.totalDurationMs += durationMs;

      // Aggregate by tier
      if (!tierMap.has(tier)) {
        tierMap.set(tier, {
          count: 0,
          totalCost: 0,
        });
      }

      const tierData = tierMap.get(tier)!;
      tierData.count += 1;
      tierData.totalCost += cost;
    }

    // Build operation summaries
    const operations: OperationCostSummary[] = [];
    for (const [operation, data] of operationMap.entries()) {
      operations.push({
        operation,
        count: data.count,
        totalCost: data.totalCost,
        totalDurationMs: data.totalDurationMs,
        averageCost: data.count > 0 ? data.totalCost / data.count : 0,
        averageDurationMs: data.count > 0 ? data.totalDurationMs / data.count : 0,
      });
    }

    // Sort by total cost descending
    operations.sort((a, b) => b.totalCost - a.totalCost);

    // Build tier summary
    const byTier: Record<string, { count: number; totalCost: number }> = {};
    for (const [tier, data] of tierMap.entries()) {
      byTier[tier] = {
        count: data.count,
        totalCost: data.totalCost,
      };
    }

    return {
      totalCost,
      totalOperations,
      operations,
      byTier,
      timestamp: Date.now(),
    };
  }

  /**
   * Get cost summary as JSON string
   */
  getSummaryJson(lastN: number = 100): string {
    const summary = this.generateSummary(lastN);
    return JSON.stringify(summary, null, 2);
  }
}
