# HTTP Header Examples for Trace Context Propagation

## Example 1: IDE → Edge Agent

**Request from VS Code Extension to Edge Agent**:

```http
POST /api/process HTTP/1.1
Host: localhost:8080
Content-Type: application/json
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: zeroui=ide-extension

{
  "request_id": "req_123",
  "data": {...}
}
```

**Response from Edge Agent**:

```http
HTTP/1.1 200 OK
Content-Type: application/json
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

{
  "response_id": "resp_456",
  "result": {...}
}
```

## Example 2: Edge Agent → Backend

**Request from Edge Agent to Backend**:

```http
POST /api/backend/process HTTP/1.1
Host: backend.zeroui.com
Content-Type: application/json
Authorization: Bearer token_xyz
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: zeroui=edge-agent,tenant=tenant-123

{
  "request_id": "req_123",
  "data": {...}
}
```

**Response from Backend**:

```http
HTTP/1.1 200 OK
Content-Type: application/json
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

{
  "response_id": "resp_456",
  "result": {...}
}
```

## Example 3: Backend → CI

**Request from Backend to CI Service**:

```http
POST /api/ci/validate HTTP/1.1
Host: ci.zeroui.com
Content-Type: application/json
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: zeroui=backend,tenant=tenant-123

{
  "request_id": "req_123",
  "data": {...}
}
```

## Example 4: Message Queue Propagation

**Message with trace context in headers**:

```json
{
  "headers": {
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    "tracestate": "zeroui=backend,tenant=tenant-123",
    "content-type": "application/json"
  },
  "body": {
    "event_type": "error.captured.v1",
    "payload": {...}
  }
}
```

## Example 5: New Trace (No Parent)

**First request in trace (IDE generates new trace)**:

```http
POST /api/process HTTP/1.1
Host: edge-agent.local
Content-Type: application/json

{
  "request_id": "req_123",
  "data": {...}
}
```

**Edge Agent generates traceparent and includes in response**:

```http
HTTP/1.1 200 OK
Content-Type: application/json
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

{
  "response_id": "resp_456",
  "result": {...}
}
```
