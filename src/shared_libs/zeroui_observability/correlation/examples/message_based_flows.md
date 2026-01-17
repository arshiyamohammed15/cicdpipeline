# Message-Based Flow Examples for Trace Context Propagation

## Example 1: Async Message Queue

**Producer (Edge Agent) sends message**:

```json
{
  "headers": {
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    "tracestate": "zeroui=edge-agent",
    "message_id": "msg_123",
    "timestamp": "2026-01-17T10:00:00Z"
  },
  "body": {
    "event_type": "error.captured.v1",
    "payload": {
      "error_class": "architecture",
      "error_code": "ERR_001",
      ...
    }
  }
}
```

**Consumer (Backend) receives message and creates child span**:

```json
{
  "headers": {
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    "tracestate": "zeroui=backend",
    "message_id": "msg_123",
    "consumer_span_id": "a1b2c3d4e5f6g7h8"
  },
  "body": {
    "event_type": "error.captured.v1",
    "payload": {...}
  }
}
```

## Example 2: Event Bus Propagation

**Event emitted with trace context**:

```json
{
  "event_id": "evt_789",
  "event_time": "2026-01-17T10:00:00Z",
  "event_type": "perf.sample.v1",
  "correlation": {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "span_id": "00f067aa0ba902b7",
    "request_id": "req_123"
  },
  "payload": {
    "operation": "decision",
    "latency_ms": 150,
    ...
  }
}
```

**Event consumer processes with same trace_id**:

```json
{
  "event_id": "evt_790",
  "event_time": "2026-01-17T10:00:01Z",
  "event_type": "evaluation.result.v1",
  "correlation": {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "span_id": "a1b2c3d4e5f6g7h8",
    "parent_span_id": "00f067aa0ba902b7",
    "request_id": "req_123"
  },
  "payload": {...}
}
```

## Example 3: Batch Processing

**Batch job with trace context**:

```json
{
  "batch_id": "batch_456",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "items": [
    {
      "item_id": "item_1",
      "span_id": "a1b2c3d4e5f6g7h8",
      "data": {...}
    },
    {
      "item_id": "item_2",
      "span_id": "b2c3d4e5f6g7h8i9",
      "data": {...}
    }
  ]
}
```
