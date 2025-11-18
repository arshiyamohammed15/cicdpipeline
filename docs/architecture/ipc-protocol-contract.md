# Extension ⇄ Edge Agent IPC Protocol Contract

## Overview

This document defines the protocol contract for communication between the VS Code Extension and the Edge Agent. The protocol uses HTTP over localhost for transport, with JSON request/response payloads.

## Transport

- **Protocol**: HTTP/1.1 over localhost
- **Base URL**: TBD (to be configured, default: `http://localhost:8080`)
- **Content-Type**: `application/json`
- **Method**: POST

> **Note**: The HTTP server implementation for Edge Agent is not yet implemented. This document defines the protocol contract that implementations must follow.

## Request Schema

### Endpoint: TBD (e.g., `/api/task/process`)

Process a task and generate a receipt.

> **Note**: The exact endpoint path is to be determined during implementation. The protocol structure defined here must be maintained regardless of the chosen path.

#### Request Body

```json
{
  "task": {
    "id": "string (required)",
    "type": "string (required)",
    "priority": "low" | "medium" | "high" | "critical",
    "data": "object (required)",
    "requirements": {
      "security": "boolean (optional)",
      "performance": "boolean (optional)",
      "compliance": "boolean (optional)"
    },
    "timeout": "number (optional, milliseconds)",
    "retryCount": "number (optional)"
  },
  "repoId": "string (required)"
}
```

#### Request Schema (JSON Schema)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["task", "repoId"],
  "properties": {
    "task": {
      "type": "object",
      "required": ["id", "type", "data"],
      "properties": {
        "id": {
          "type": "string",
          "minLength": 1
        },
        "type": {
          "type": "string",
          "minLength": 1
        },
        "priority": {
          "type": "string",
          "enum": ["low", "medium", "high", "critical"]
        },
        "data": {
          "type": "object"
        },
        "requirements": {
          "type": "object",
          "properties": {
            "security": {
              "type": "boolean"
            },
            "performance": {
              "type": "boolean"
            },
            "compliance": {
              "type": "boolean"
            }
          }
        },
        "timeout": {
          "type": "number",
          "minimum": 0
        },
        "retryCount": {
          "type": "number",
          "minimum": 0
        }
      }
    },
    "repoId": {
      "type": "string",
      "minLength": 1
    }
  }
}
```

#### Example Request

```json
{
  "task": {
    "id": "test-task-001",
    "type": "code_review",
    "priority": "medium",
    "data": {
      "file_path": "src/example.ts",
      "context": "pre-commit"
    },
    "requirements": {
      "security": true,
      "performance": false
    }
  },
  "repoId": "test-repo"
}
```

## Response Schema

### Success Response (200 OK)

```json
{
  "result": "any",
  "receiptPath": "string (absolute file path)"
}
```

#### Success Response Schema (JSON Schema)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["result", "receiptPath"],
  "properties": {
    "result": {},
    "receiptPath": {
      "type": "string",
      "minLength": 1
    }
  }
}
```

#### Example Success Response

```json
{
  "result": {
    "taskId": "test-task-001",
    "success": true,
    "processingTime": 123
  },
  "receiptPath": "C:\\Users\\...\\ide\\receipts\\test-repo\\receipts.jsonl"
}
```

## Error Response Schema

### Error Envelope

All error responses follow a consistent envelope structure:

```json
{
  "error": {
    "code": "string (required)",
    "message": "string (required)",
    "details": "object (optional)"
  }
}
```

#### Error Envelope Schema (JSON Schema)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["error"],
  "properties": {
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": {
          "type": "string",
          "minLength": 1
        },
        "message": {
          "type": "string",
          "minLength": 1
        },
        "details": {
          "type": "object"
        }
      }
    }
  }
}
```

### HTTP Status Codes

- **200 OK**: Request processed successfully
- **400 Bad Request**: Invalid request format or missing required fields
- **404 Not Found**: Endpoint not found
- **500 Internal Server Error**: Edge Agent processing error
- **503 Service Unavailable**: Edge Agent not available or not initialized
- **504 Gateway Timeout**: Request timeout exceeded

### Error Code Values

- `INVALID_REQUEST`: Request body validation failed
- `MISSING_FIELD`: Required field missing in request
- `TASK_PROCESSING_ERROR`: Error during task processing
- `RECEIPT_GENERATION_ERROR`: Error generating receipt
- `POLICY_ERROR`: Policy storage or retrieval error
- `SERVICE_UNAVAILABLE`: Edge Agent service not available
- `TIMEOUT`: Request processing timeout
- `UNKNOWN_ERROR`: Unspecified error

#### Example Error Responses

**400 Bad Request - Invalid Request Format**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Request body validation failed",
    "details": {
      "field": "task.id",
      "reason": "Field is required"
    }
  }
}
```

**500 Internal Server Error - Processing Error**
```json
{
  "error": {
    "code": "TASK_PROCESSING_ERROR",
    "message": "Failed to process task",
    "details": {
      "taskId": "test-task-001",
      "reason": "Delegation failed"
    }
  }
}
```

**503 Service Unavailable**
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Edge Agent is not available",
    "details": {
      "reason": "Agent not initialized"
    }
  }
}
```

**504 Gateway Timeout**
```json
{
  "error": {
    "code": "TIMEOUT",
    "message": "Request processing timeout",
    "details": {
      "taskId": "test-task-001",
      "timeoutMs": 30000
    }
  }
}
```

## Timeouts

> **Note**: The specific timeout values below are recommended defaults. Implementations should make these configurable. The `task.timeout` field in the request allows per-request timeout specification.

### Client-Side Timeouts

- **Connection Timeout**: 5 seconds (recommended)
- **Request Timeout**: 30 seconds (recommended default)
  - Configurable per request via `task.timeout` field
  - Maximum allowed: 300 seconds (5 minutes, recommended)

### Server-Side Timeouts

- **Processing Timeout**: 30 seconds (recommended default)
  - Respects `task.timeout` if provided and within limits
  - Maximum processing time: 300 seconds (5 minutes, recommended)

### Timeout Behavior

- If client timeout occurs: Client should treat as `TIMEOUT` error
- If server timeout occurs: Server returns `504 Gateway Timeout` with `TIMEOUT` error code
- Partial results are not returned on timeout

## Implementation Notes

### Request Processing Flow

1. Extension sends HTTP POST request to Edge Agent
2. Edge Agent validates request schema
3. Edge Agent calls `processTaskWithReceipt(task, repoId)`
4. Edge Agent processes task through delegation manager
5. Edge Agent validates result
6. Edge Agent generates receipt and stores it
7. Edge Agent returns response with result and receipt path

### Receipt Path

The `receiptPath` in the response is an absolute file system path where the receipt was stored. The receipt is stored in JSONL format (one receipt per line) at:

```
{ZU_ROOT}/ide/receipts/{repoId}/{yyyy}/{mm}/receipts.jsonl
```

Where:
- `{ZU_ROOT}`: Base storage root (from `ZU_ROOT` environment variable)
- `{repoId}`: Repository identifier (kebab-case)
- `{yyyy}`: 4-digit year (UTC) from receipt timestamp
- `{mm}`: 2-digit month (01-12, UTC) from receipt timestamp

The receipt can be read by the Extension using `ReceiptStorageReader`.

### Task Data Field

The `task.data` field is a free-form object that can contain any task-specific data. Common patterns observed:

- `file_path`: File path for file-related tasks
- `context`: Context string (e.g., "pre-commit", "pre-push")
- Custom fields as needed by specific task types

### Minimal Task Structure

For simple tasks, only `id`, `type`, and `data` are required:

```json
{
  "task": {
    "id": "test-task",
    "type": "validation",
    "data": {}
  },
  "repoId": "test-repo"
}
```

## Versioning

- **Protocol Version**: 1.0
- **Compatibility**: Backward compatible changes only
- **Breaking Changes**: Will increment major version

## Security Considerations

- All communication is over localhost (127.0.0.1)
- No authentication required (local process communication)
- Request/response payloads may contain sensitive data (file paths, code context)
- Receipts are signed and stored locally

## References

- Edge Agent: `src/edge-agent/EdgeAgent.ts` - `processTaskWithReceipt()` method
- Task Interface: `src/edge-agent/interfaces/core/DelegationInterface.ts` - `DelegationTask` interface
- Receipt Types: `src/edge-agent/shared/receipt-types.ts` - `DecisionReceipt` interface
- Architecture: `docs/architecture/architecture-vscode-modular-extension.md` - IPC client reference
