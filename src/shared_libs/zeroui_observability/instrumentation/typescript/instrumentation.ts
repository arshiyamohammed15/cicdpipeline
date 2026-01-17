/**
 * TypeScript instrumentation for ZeroUI Observability Layer.
 *
 * Async/non-blocking telemetry emission for VS Code Extension (Tier 1) and Edge Agent (Tier 2).
 * Does not block UI thread.
 */

import { EventType } from '../../contracts/event_types';
import { getOrCreateTraceContext, TraceContext } from '../../correlation/trace_context';

/**
 * Event emitter for ZeroUI Observability Layer.
 *
 * Emits events using Phase 0 contracts (envelope + payload schemas).
 * Applies redaction before emission and propagates trace context.
 * Async/non-blocking - does not block UI thread.
 */
export class EventEmitter {
  private enabled: boolean;
  private component: string;
  private channel: string;
  private version: string;
  private otlpEndpoint: string;

  constructor(
    otlpEndpoint?: string,
    enabled: boolean = true,
    component: string = 'edge_agent',
    channel: string = 'ide',
    version?: string
  ) {
    this.enabled = enabled && this.checkFeatureFlag();
    this.component = component;
    this.channel = channel;
    this.version = version || process.env.COMPONENT_VERSION || 'unknown';
    this.otlpEndpoint = otlpEndpoint || process.env.OTLP_EXPORTER_ENDPOINT || 'http://localhost:4317';
  }

  private checkFeatureFlag(): boolean {
    return (process.env.ZEROUI_OBSV_ENABLED || 'true').toLowerCase() === 'true';
  }

  /**
   * Emit observability event asynchronously (non-blocking).
   *
   * @param eventType Event type
   * @param payload Event payload (must match event type schema)
   * @param severity Event severity (debug, info, warn, error, critical)
   * @param traceCtx Optional trace context (creates new if not provided)
   * @returns Promise resolving to true if event was emitted
   */
  async emitEvent(
    eventType: EventType,
    payload: Record<string, any>,
    severity: string = 'info',
    traceCtx?: TraceContext
  ): Promise<boolean> {
    if (!this.enabled) {
      return false;
    }

    try {
      // Get or create trace context
      const ctx = traceCtx || getOrCreateTraceContext();

      // Apply redaction to payload (basic - full redaction in Phase 0)
      const redactedPayload = this.applyBasicRedaction(payload);
      redactedPayload.redaction_applied = true;

      // Create event envelope
      const event = this.createEnvelope(eventType, redactedPayload, severity, ctx);

      // Emit via OTLP (async, non-blocking)
      await this.emitOtlpLog(event);

      return true;
    } catch (error) {
      console.error(`Failed to emit event ${eventType}:`, error);
      return false;
    }
  }

  private createEnvelope(
    eventType: EventType,
    payload: Record<string, any>,
    severity: string,
    traceCtx: TraceContext
  ): Record<string, any> {
    return {
      event_id: `evt_${crypto.randomUUID().substring(0, 16)}`,
      event_time: new Date().toISOString(),
      event_type: eventType,
      severity: severity,
      source: {
        component: this.component,
        channel: this.channel,
        version: this.version,
      },
      correlation: {
        trace_id: traceCtx.traceId,
        span_id: traceCtx.spanId,
      },
      payload: payload,
    };
  }

  private applyBasicRedaction(payload: Record<string, any>): Record<string, any> {
    // Basic redaction - remove deny-listed fields
    const denyList = ['api_key', 'password', 'secret', 'raw_input', 'raw_output', 'raw_message'];
    const redacted = { ...payload };
    for (const field of denyList) {
      if (field in redacted) {
        delete redacted[field];
      }
    }
    return redacted;
  }

  private async emitOtlpLog(event: Record<string, any>): Promise<void> {
    // Emit via OTLP HTTP endpoint (async, non-blocking)
    // Use fetch with fire-and-forget pattern to avoid blocking UI
    fetch(this.otlpEndpoint + '/v1/logs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resourceLogs: [
          {
            resource: {
              attributes: [
                { key: 'service.name', value: { stringValue: this.component } },
                { key: 'service.version', value: { stringValue: this.version } },
                { key: 'zeroui.channel', value: { stringValue: this.channel } },
              ],
            },
            scopeLogs: [
              {
                scope: { name: 'zeroui.observability' },
                logRecords: [
                  {
                    timeUnixNano: Date.now() * 1000000,
                    severityNumber: this.getSeverityNumber(event.severity),
                    severityText: event.severity,
                    body: { stringValue: JSON.stringify(event) },
                    attributes: [
                      { key: 'event.id', value: { stringValue: event.event_id } },
                      { key: 'event.type', value: { stringValue: event.event_type } },
                      { key: 'trace_id', value: { stringValue: event.correlation.trace_id } },
                      { key: 'span_id', value: { stringValue: event.correlation.span_id } },
                    ],
                  },
                ],
              },
            ],
          },
        ],
      }),
    }).catch((error) => {
      // Silently fail to avoid blocking UI
      console.debug('OTLP emission failed (non-blocking):', error);
    });
  }

  private getSeverityNumber(severity: string): number {
    const severityMap: Record<string, number> = {
      debug: 5,
      info: 9,
      warn: 13,
      error: 17,
      critical: 21,
    };
    return severityMap[severity] || 9;
  }

  /**
   * Emit perf.sample.v1 event.
   */
  async emitPerfSample(
    operation: string,
    latencyMs: number,
    traceCtx?: TraceContext,
    extra?: Record<string, any>
  ): Promise<boolean> {
    const payload = {
      operation: operation,
      latency_ms: latencyMs,
      component: this.component,
      channel: this.channel,
      ...extra,
    };
    return await this.emitEvent(EventType.PERF_SAMPLE, payload, 'info', traceCtx);
  }

  /**
   * Emit error.captured.v1 event.
   */
  async emitErrorCaptured(
    errorClass: string,
    errorCode: string,
    stage: string,
    traceCtx?: TraceContext,
    extra?: Record<string, any>
  ): Promise<boolean> {
    // Compute fingerprints (basic - full implementation in Phase 0)
    const message = extra?.message || '';
    const messageFingerprint = message
      ? await this.computeFingerprint(message)
      : '';

    const payload = {
      error_class: errorClass,
      error_code: errorCode,
      stage: stage,
      message_fingerprint: messageFingerprint,
      input_fingerprint: extra?.input_fingerprint || '',
      output_fingerprint: extra?.output_fingerprint || '',
      internal_state_fingerprint: extra?.internal_state_fingerprint || '',
      component: this.component,
      channel: this.channel,
      ...Object.fromEntries(
        Object.entries(extra || {}).filter(([k]) => k !== 'message')
      ),
    };
    return await this.emitEvent(EventType.ERROR_CAPTURED, payload, 'error', traceCtx);
  }

  private async computeFingerprint(content: string): Promise<string> {
    // SHA-256 fingerprint (basic implementation)
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  }
}

// Global event emitter instance
let eventEmitter: EventEmitter | null = null;

/**
 * Get global event emitter instance (singleton).
 */
export function getEventEmitter(): EventEmitter {
  if (!eventEmitter) {
    eventEmitter = new EventEmitter();
  }
  return eventEmitter;
}
