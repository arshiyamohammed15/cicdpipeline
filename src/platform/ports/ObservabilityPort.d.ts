/**
 * ObservabilityPort
 *
 * Cloud-agnostic interface for observability operations (metrics, logs, traces).
 * Implemented by local adapters for monitoring and observability.
 *
 * @interface ObservabilityPort
 */
export interface ObservabilityPort {
    /**
     * Emit a metric.
     *
     * @param metric - Metric to emit
     * @returns Promise resolving when metric is emitted
     */
    emitMetric(metric: Metric): Promise<void>;
    /**
     * Emit multiple metrics in batch.
     *
     * @param metrics - Array of metrics to emit
     * @returns Promise resolving when metrics are emitted
     */
    emitMetrics(metrics: Metric[]): Promise<void>;
    /**
     * Write a log entry.
     *
     * @param logEntry - Log entry to write
     * @returns Promise resolving when log is written
     */
    writeLog(logEntry: LogEntry): Promise<void>;
    /**
     * Write multiple log entries in batch.
     *
     * @param logEntries - Array of log entries to write
     * @returns Promise resolving when logs are written
     */
    writeLogs(logEntries: LogEntry[]): Promise<void>;
    /**
     * Emit a trace span.
     *
     * @param span - Trace span to emit
     * @returns Promise resolving when span is emitted
     */
    emitSpan(span: TraceSpan): Promise<void>;
    /**
     * Query metrics.
     *
     * @param query - Metric query
     * @returns Promise resolving to query results
     */
    queryMetrics(query: MetricQuery): Promise<MetricQueryResult>;
    /**
     * Query logs.
     *
     * @param query - Log query
     * @returns Promise resolving to query results
     */
    queryLogs(query: LogQuery): Promise<LogQueryResult>;
}
/**
 * Represents a metric to be emitted.
 */
export interface Metric {
    /** Metric name */
    name: string;
    /** Metric value */
    value: number;
    /** Metric unit */
    unit?: string;
    /** Metric timestamp */
    timestamp?: Date;
    /** Metric dimensions/tags */
    dimensions?: Record<string, string>;
    /** Metric type */
    type?: 'counter' | 'gauge' | 'histogram' | 'summary';
}
/**
 * Represents a log entry to be written.
 */
export interface LogEntry {
    /** Log level */
    level: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
    /** Log message */
    message: string;
    /** Log timestamp */
    timestamp?: Date;
    /** Log context/metadata */
    context?: Record<string, unknown>;
    /** Source/service name */
    source?: string;
}
/**
 * Represents a trace span to be emitted.
 */
export interface TraceSpan {
    /** Span name/operation */
    name: string;
    /** Trace ID */
    traceId: string;
    /** Span ID */
    spanId: string;
    /** Parent span ID (if any) */
    parentSpanId?: string;
    /** Span start time */
    startTime: Date;
    /** Span end time */
    endTime: Date;
    /** Span duration (milliseconds) */
    duration?: number;
    /** Span status */
    status?: 'ok' | 'error';
    /** Span attributes/tags */
    attributes?: Record<string, string | number | boolean>;
}
/**
 * Query for metrics.
 */
export interface MetricQuery {
    /** Metric name to query */
    metricName: string;
    /** Start time for query */
    startTime: Date;
    /** End time for query */
    endTime: Date;
    /** Aggregation function */
    aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
    /** Group by dimensions */
    groupBy?: string[];
    /** Filter by dimensions */
    filter?: Record<string, string>;
}
/**
 * Result of a metric query.
 */
export interface MetricQueryResult {
    /** Query results */
    results: MetricDataPoint[];
    /** Query metadata */
    metadata?: Record<string, unknown>;
}
/**
 * Represents a metric data point.
 */
export interface MetricDataPoint {
    /** Metric value */
    value: number;
    /** Timestamp */
    timestamp: Date;
    /** Dimensions/tags */
    dimensions?: Record<string, string>;
}
/**
 * Query for logs.
 */
export interface LogQuery {
    /** Log level filter */
    level?: 'debug' | 'info' | 'warn' | 'error' | 'fatal';
    /** Start time for query */
    startTime: Date;
    /** End time for query */
    endTime: Date;
    /** Text search filter */
    textFilter?: string;
    /** Source/service filter */
    source?: string;
    /** Maximum number of results */
    maxResults?: number;
}
/**
 * Result of a log query.
 */
export interface LogQueryResult {
    /** Query results */
    results: LogEntry[];
    /** Continuation token for pagination */
    continuationToken?: string;
    /** Whether more results are available */
    hasMore: boolean;
}
//# sourceMappingURL=ObservabilityPort.d.ts.map