/**
 * LocalObservability
 *
 * Local file-based implementation of ObservabilityPort.
 * Writes metrics/events to logs/observability.ndjson with monotonic timestamps.
 */
import { ObservabilityPort, Metric, LogEntry, TraceSpan, MetricQuery, MetricQueryResult, LogQuery, LogQueryResult } from '../../ports/ObservabilityPort';
export declare class LocalObservability implements ObservabilityPort {
    private baseDir;
    private metricsFile;
    private logsFile;
    private tracesFile;
    constructor(baseDir: string);
    emitMetric(metric: Metric): Promise<void>;
    emitMetrics(metrics: Metric[]): Promise<void>;
    writeLog(logEntry: LogEntry): Promise<void>;
    writeLogs(logEntries: LogEntry[]): Promise<void>;
    emitSpan(span: TraceSpan): Promise<void>;
    queryMetrics(query: MetricQuery): Promise<MetricQueryResult>;
    queryLogs(query: LogQuery): Promise<LogQueryResult>;
    private aggregateMetrics;
    private appendToJsonl;
    private ensureDirectory;
    private getMonotonicTime;
}
//# sourceMappingURL=LocalObservability.d.ts.map