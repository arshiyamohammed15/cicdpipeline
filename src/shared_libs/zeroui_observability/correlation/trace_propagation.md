# ZeroUI Observability Layer - Trace Context Propagation

## Overview

This document defines the trace context propagation contract for ZeroUI Observability Layer, ensuring end-to-end correlation across IDE → Edge Agent → Backend → CI boundaries.

**Standard**: W3C Trace Context (traceparent, tracestate)  
**Version**: Trace Context Level 1  
**Last Updated**: 2026-01-17

## W3C Trace Context Standard

ZeroUI uses **W3C Trace Context** for distributed tracing correlation:

- **traceparent**: Required header for trace correlation
- **tracestate**: Optional header for vendor-specific trace data

### traceparent Format

```
traceparent: 00-{trace-id}-{parent-id}-{trace-flags}
```

Where:
- `00`: Version (currently 00)
- `trace-id`: 32 hex characters (16 bytes)
- `parent-id`: 16 hex characters (8 bytes)
- `trace-flags`: 2 hex characters (1 byte, flags)

Example:
```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

### tracestate Format

```
tracestate: key1=value1,key2=value2
```

- Key-value pairs separated by commas
- Vendor-specific data
- Optional

## Propagation Rules

### IDE → Edge Agent

**Protocol**: HTTP/HTTPS or Message Queue

**Headers**:
- `traceparent`: Required
- `tracestate`: Optional

**Behavior**:
- IDE generates new trace_id if not present
- Edge Agent extracts traceparent, creates new span_id
- Edge Agent propagates traceparent to Backend

### Edge Agent → Backend

**Protocol**: HTTP/HTTPS

**Headers**:
- `traceparent`: Required
- `tracestate`: Optional

**Behavior**:
- Edge Agent propagates traceparent unchanged
- Backend extracts trace_id, creates new span_id
- Backend propagates traceparent to downstream services

### Backend → CI

**Protocol**: HTTP/HTTPS or Message Queue

**Headers**:
- `traceparent`: Required
- `tracestate`: Optional

**Behavior**:
- Backend propagates traceparent unchanged
- CI extracts trace_id, creates new span_id
- CI includes trace_id in logs and events

## Required Correlation Fields

All events and logs MUST include:

### Required
- `trace_id`: 32-character hex string (from traceparent)

### Optional
- `span_id`: 16-character hex string (current span)
- `parent_span_id`: 16-character hex string (parent span)
- `request_id`: Request identifier (for request correlation)
- `session_id`: Session identifier (for user session correlation)

## Log Correlation

Logs MUST include trace context where supported:

### Structured Logs
```json
{
  "timestamp": "2026-01-17T10:00:00Z",
  "level": "INFO",
  "message": "Processing request",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "component": "edge_agent"
}
```

### OpenTelemetry Logs
- Use `TraceId` and `SpanId` attributes per OpenTelemetry Logs spec
- Correlate logs to traces using trace_id

## Event Correlation

All observability events MUST include correlation fields:

```json
{
  "event_id": "evt_123",
  "event_time": "2026-01-17T10:00:00Z",
  "event_type": "error.captured.v1",
  "correlation": {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "span_id": "00f067aa0ba902b7",
    "request_id": "req_456",
    "session_id": "sess_789"
  }
}
```

## Implementation

### Python (Backend Services)

Use `trace_context.py` utilities:
- `parse_traceparent()`: Parse traceparent header
- `generate_traceparent()`: Generate traceparent header
- `TraceContext`: Context manager for span creation

### TypeScript (IDE Extension, Edge Agent)

Use `trace_context.ts` utilities:
- `parseTraceparent()`: Parse traceparent header
- `generateTraceparent()`: Generate traceparent header
- `TraceContext`: Class for trace context management

## Integration with CCCS OTCS

The observability layer integrates with CCCS OTCS (`src/shared_libs/cccs/observability/service.py`) for:
- Trace ID generation
- Span ID generation
- Context management

## Examples

### HTTP Request Propagation

**Request from IDE to Edge Agent**:
```http
POST /api/process HTTP/1.1
Host: edge-agent.local
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

**Request from Edge Agent to Backend**:
```http
POST /api/backend/process HTTP/1.1
Host: backend.zeroui.com
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

### Message Queue Propagation

**Message Headers**:
```json
{
  "headers": {
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    "tracestate": "zeroui=tenant-123"
  },
  "body": {...}
}
```

## References

- W3C Trace Context: https://www.w3.org/TR/trace-context/
- W3C Trace Context Level 2: https://www.w3.org/TR/trace-context-2/
- OpenTelemetry Logs Spec: https://opentelemetry.io/docs/specs/otel/logs/
- CCCS OTCS: `src/shared_libs/cccs/observability/service.py`
