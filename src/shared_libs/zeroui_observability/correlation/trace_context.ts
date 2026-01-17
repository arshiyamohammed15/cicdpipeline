/**
 * Trace context utilities for ZeroUI Observability Layer (TypeScript).
 *
 * W3C Trace Context (traceparent, tracestate) implementation for TypeScript.
 * Used by VS Code Extension and Edge Agent.
 */

/**
 * Trace context for distributed tracing.
 *
 * Per W3C Trace Context standard.
 */
export interface TraceContext {
  traceId: string; // 32 hex characters
  spanId: string; // 16 hex characters
  parentSpanId?: string; // 16 hex characters
  traceFlags: string; // 2 hex characters, default "01" (sampled)
  tracestate?: string; // Optional vendor-specific data
}

/**
 * W3C Trace Context format:
 * traceparent: 00-{trace-id}-{parent-id}-{trace-flags}
 */
const TRACEPARENT_PATTERN = /^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/i;

/**
 * Generate new trace ID (32 hex characters).
 */
export function generateTraceId(): string {
  // Generate UUID v4 and convert to hex (remove dashes)
  return crypto.randomUUID().replace(/-/g, "");
}

/**
 * Generate new span ID (16 hex characters).
 */
export function generateSpanId(): string {
  // Generate UUID v4, take first 16 hex characters
  return crypto.randomUUID().replace(/-/g, "").substring(0, 16);
}

/**
 * Parse traceparent header value.
 *
 * @param traceparent - traceparent header string
 * @returns TraceContext or null if invalid
 */
export function parseTraceparent(traceparent: string | null | undefined): TraceContext | null {
  if (!traceparent) {
    return null;
  }

  const match = traceparent.trim().match(TRACEPARENT_PATTERN);
  if (!match) {
    console.warn(`Invalid traceparent format: ${traceparent}`);
    return null;
  }

  const [, version, traceId, parentId, traceFlags] = match;

  // Validate version (currently only 00 is supported)
  if (version !== "00") {
    console.warn(`Unsupported traceparent version: ${version}`);
    return null;
  }

  // Normalize to lowercase
  const normalizedTraceId = traceId.toLowerCase();
  const normalizedParentId = parentId.toLowerCase();
  const normalizedTraceFlags = traceFlags.toLowerCase();

  return {
    traceId: normalizedTraceId,
    spanId: normalizedParentId, // Current span uses parent_id as span_id
    parentSpanId: normalizedParentId !== "0000000000000000" ? normalizedParentId : undefined,
    traceFlags: normalizedTraceFlags,
  };
}

/**
 * Generate traceparent header value.
 *
 * @param traceId - Trace ID (32 hex chars) or undefined to generate new
 * @param parentSpanId - Parent span ID (16 hex chars) or undefined
 * @param traceFlags - Trace flags (2 hex chars), default "01" (sampled)
 * @returns traceparent header string
 */
export function generateTraceparent(
  traceId?: string,
  parentSpanId?: string,
  traceFlags: string = "01"
): string {
  const finalTraceId = traceId || generateTraceId();
  const finalParentSpanId = parentSpanId || "0000000000000000";

  // Normalize
  const normalizedTraceId = finalTraceId.toLowerCase();
  const normalizedParentSpanId = finalParentSpanId.toLowerCase();
  const normalizedTraceFlags = traceFlags.toLowerCase();

  return `00-${normalizedTraceId}-${normalizedParentSpanId}-${normalizedTraceFlags}`;
}

/**
 * Create child trace context.
 *
 * @param parent - Parent trace context
 * @returns New TraceContext with new span_id, current span as parent
 */
export function createChildContext(parent: TraceContext): TraceContext {
  const newSpanId = generateSpanId();
  return {
    traceId: parent.traceId,
    spanId: newSpanId,
    parentSpanId: parent.spanId,
    traceFlags: parent.traceFlags,
    tracestate: parent.tracestate,
  };
}

/**
 * Get trace context from traceparent or create new.
 *
 * @param traceparent - Optional traceparent header
 * @returns TraceContext (from header or newly created)
 */
export function getOrCreateTraceContext(traceparent?: string | null): TraceContext {
  // Try to parse traceparent
  if (traceparent) {
    const ctx = parseTraceparent(traceparent);
    if (ctx) {
      return ctx;
    }
  }

  // Create new trace context
  return {
    traceId: generateTraceId(),
    spanId: generateSpanId(),
    traceFlags: "01", // Sampled
  };
}

/**
 * Convert TraceContext to traceparent header value.
 *
 * @param ctx - Trace context
 * @returns traceparent header string
 */
export function toTraceparent(ctx: TraceContext): string {
  const parentId = ctx.parentSpanId || "0000000000000000";
  return `00-${ctx.traceId}-${parentId}-${ctx.traceFlags}`;
}
