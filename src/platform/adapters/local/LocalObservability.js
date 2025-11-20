"use strict";
/**
 * LocalObservability
 *
 * Local file-based implementation of ObservabilityPort.
 * Writes metrics/events to logs/observability.ndjson with monotonic timestamps.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.LocalObservability = void 0;
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class LocalObservability {
    constructor(baseDir) {
        this.baseDir = baseDir;
        this.metricsFile = path.join(baseDir, 'logs', 'observability.ndjson');
        this.logsFile = this.metricsFile;
        this.tracesFile = this.metricsFile;
    }
    async emitMetric(metric) {
        const record = {
            ...metric,
            timestamp: this.getMonotonicTime(),
        };
        await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
    }
    async emitMetrics(metrics) {
        const records = metrics.map((metric) => ({
            ...metric,
            timestamp: this.getMonotonicTime(),
        }));
        for (const record of records) {
            await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
        }
    }
    async writeLog(logEntry) {
        const record = {
            ...logEntry,
            timestamp: this.getMonotonicTime(),
        };
        await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
    }
    async writeLogs(logEntries) {
        const records = logEntries.map((logEntry) => ({
            ...logEntry,
            timestamp: this.getMonotonicTime(),
        }));
        for (const record of records) {
            await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
        }
    }
    async emitSpan(span) {
        const record = {
            ...span,
            timestamp: this.getMonotonicTime(),
        };
        await this.appendToJsonl(this.metricsFile, JSON.stringify(record));
    }
    async queryMetrics(query) {
        if (!fs.existsSync(this.metricsFile)) {
            return { results: [] };
        }
        const content = fs.readFileSync(this.metricsFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const results = [];
        const startTime = query.startTime.getTime();
        const endTime = query.endTime.getTime();
        for (const line of lines) {
            try {
                const record = JSON.parse(line);
                // Filter by metric name
                if (record.name !== query.metricName) {
                    continue;
                }
                // Filter by timestamp
                const recordTime = record.timestamp || record.timestamp?.getTime?.() || 0;
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
            }
            catch (error) {
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
    async queryLogs(query) {
        if (!fs.existsSync(this.metricsFile)) {
            return { results: [], hasMore: false };
        }
        const content = fs.readFileSync(this.metricsFile, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const results = [];
        const startTime = query.startTime.getTime();
        const endTime = query.endTime.getTime();
        const maxResults = query.maxResults || 1000;
        for (const line of lines) {
            if (results.length >= maxResults) {
                break;
            }
            try {
                const record = JSON.parse(line);
                // Check if it's a log entry (has level and message)
                if (!record.level || !record.message) {
                    continue;
                }
                // Filter by level
                if (query.level && record.level !== query.level) {
                    continue;
                }
                // Filter by timestamp
                const recordTime = record.timestamp || record.timestamp?.getTime?.() || 0;
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
            }
            catch (error) {
                // Skip invalid lines
                continue;
            }
        }
        return {
            results,
            hasMore: results.length >= maxResults,
        };
    }
    aggregateMetrics(dataPoints, aggregation) {
        if (dataPoints.length === 0) {
            return [];
        }
        let aggregatedValue;
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
    async appendToJsonl(filePath, jsonContent) {
        await this.ensureDirectory(path.dirname(filePath));
        try {
            await fs.promises.open(filePath, 'ax').then((handle) => handle.close());
        }
        catch (error) {
            const err = error;
            if (err.code !== 'EEXIST') {
                throw err;
            }
        }
        const line = `${jsonContent}\n`;
        const handle = await fs.promises.open(filePath, 'a');
        try {
            await handle.write(line);
            await handle.sync();
        }
        finally {
            await handle.close();
        }
    }
    async ensureDirectory(dirPath) {
        await fs.promises.mkdir(dirPath, { recursive: true });
    }
    getMonotonicTime() {
        return Date.now();
    }
}
exports.LocalObservability = LocalObservability;
//# sourceMappingURL=LocalObservability.js.map