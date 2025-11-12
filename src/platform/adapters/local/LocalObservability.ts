/**
 * LocalObservability
 * 
 * Local file-based implementation of ObservabilityPort.
 * Writes metrics/events to logs/observability.ndjson with monotonic timestamps.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  ObservabilityPort,
  Metric,
  LogEntry,
  TraceSpan,
  MetricQuery,
  MetricQueryResult,
  LogQuery,
  LogQueryResult,
  MetricDataPoint,
} from '../../ports/ObservabilityPort';

interface MetricRecord extends Omit<Metric, 'timestamp'> {
  timestamp: number; // monotonic timestamp
}

interface LogRecord extends Omit<LogEntry, 'timestamp'> {
  timestamp: number; // monotonic timestamp
}

interface TraceRecord extends Omit<TraceSpan, 'startTime' | 'endTime'> {
  startTime: Date;
  endTime: Date;
  timestamp: number; // monotonic timestamp
}

export class LocalObservability implements ObservabilityPort {
  private baseDir: string;
  private metricsFile: string;
  private logsFile: string;
  private tracesFile: string;

  constructor(baseDir: string) {
    this.baseDir = baseDir;
    this.metricsFile = path.join(baseDir, 'logs', 'observability.ndjson');
  }

  async emitMetric(metric: Metric): Promise<void> {
    const record: MetricRecord = {
      ...metric,
      timestamp: this.getMonotonicTime(),
    };
    await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
  }

  async emitMetrics(metrics: Metric[]): Promise<void> {
    const records: MetricRecord[] = metrics.map((metric) => ({
      ...metric,
      timestamp: this.getMonotonicTime(),
    }));

    for (const record of records) {
      await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
    }
  }

  async writeLog(logEntry: LogEntry): Promise<void> {
    const record: LogRecord = {
      ...logEntry,
      timestamp: this.getMonotonicTime(),
    };
    await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
  }

  async writeLogs(logEntries: LogEntry[]): Promise<void> {
    const records: LogRecord[] = logEntries.map((logEntry) => ({
      ...logEntry,
      timestamp: this.getMonotonicTime(),
    }));

    for (const record of records) {
      await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
    }
  }

  async emitSpan(span: TraceSpan): Promise<void> {
    const record: TraceRecord = {
      ...span,
      timestamp: this.getMonotonicTime(),
    };
    await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
  }

  async queryMetrics(query: MetricQuery): Promise<MetricQueryResult> {
    if (!fs.existsSync(this.metricsFile)) {
      return { results: [] };
    }

    const content = fs.readFileSync(this.metricsFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const results: MetricDataPoint[] = [];

    const startTime = query.startTime.getTime();
    const endTime = query.endTime.getTime();

    for (const line of lines) {
      try {
        const record: MetricRecord = JSON.parse(line);
        
        // Filter by metric name
        if (record.name !== query.metricName) {
          continue;
        }

        // Filter by timestamp
        const recordTime = record.timestamp || (record.timestamp as unknown as Date)?.getTime?.() || 0;
        if (recordTime < startTime || recordTime > endTime) {
          continue;
        }

        // Filter by dimensions if specified
        if (query.filter) {
          let matches = true;
          for (const [key, value] of Object.entries(query.filter)) {
            if (record.dimensions?.[key] !== value) {
              matches = false;
              break;
            }
          }
          if (!matches) {
            continue;
          }
        }

        results.push({
          value: record.value,
          timestamp: new Date(recordTime),
          dimensions: record.dimensions,
        });
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    // Apply aggregation if specified
    if (query.aggregation && results.length > 0) {
      const aggregated = this.aggregateMetrics(results, query.aggregation);
      return { results: aggregated };
    }

    return { results };
  }

  async queryLogs(query: LogQuery): Promise<LogQueryResult> {
    if (!fs.existsSync(this.metricsFile)) {
      return { results: [], hasMore: false };
    }

    const content = fs.readFileSync(this.metricsFile, 'utf-8');
    const lines = content.split('\n').filter((line) => line.trim());
    const results: LogEntry[] = [];

    const startTime = query.startTime.getTime();
    const endTime = query.endTime.getTime();
    const maxResults = query.maxResults || 1000;

    for (const line of lines) {
      if (results.length >= maxResults) {
        break;
      }

      try {
        const record: LogRecord = JSON.parse(line);
        
        // Check if it's a log entry (has level and message)
        if (!record.level || !record.message) {
          continue;
        }

        // Filter by level
        if (query.level && record.level !== query.level) {
          continue;
        }

        // Filter by timestamp
        const recordTime = record.timestamp || (record.timestamp as unknown as Date)?.getTime?.() || 0;
        if (recordTime < startTime || recordTime > endTime) {
          continue;
        }

        // Filter by source
        if (query.source && record.source !== query.source) {
          continue;
        }

        // Filter by text
        if (query.textFilter && !record.message.includes(query.textFilter)) {
          continue;
        }

        results.push({
          level: record.level,
          message: record.message,
          timestamp: new Date(recordTime),
          context: record.context,
          source: record.source,
        });
      } catch (error) {
        // Skip invalid lines
        continue;
      }
    }

    return {
      results,
      hasMore: results.length >= maxResults,
    };
  }

  private aggregateMetrics(
    dataPoints: MetricDataPoint[],
    aggregation: 'sum' | 'avg' | 'min' | 'max' | 'count'
  ): MetricDataPoint[] {
    if (dataPoints.length === 0) {
      return [];
    }

    let aggregatedValue: number;

    switch (aggregation) {
      case 'sum':
        aggregatedValue = dataPoints.reduce((sum, dp) => sum + dp.value, 0);
        break;
      case 'avg':
        aggregatedValue = dataPoints.reduce((sum, dp) => sum + dp.value, 0) / dataPoints.length;
        break;
      case 'min':
        aggregatedValue = Math.min(...dataPoints.map((dp) => dp.value));
        break;
      case 'max':
        aggregatedValue = Math.max(...dataPoints.map((dp) => dp.value));
        break;
      case 'count':
        aggregatedValue = dataPoints.length;
        break;
      default:
        aggregatedValue = dataPoints[0].value;
    }

    return [
      {
        value: aggregatedValue,
        timestamp: dataPoints[0].timestamp,
        dimensions: dataPoints[0].dimensions,
      },
    ];
  }

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

