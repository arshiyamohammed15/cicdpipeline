# API Gateway & Webhooks (EPC-6)

Minimal shared-service stub for API Gateway & Webhooks.

- FastAPI app with `/health` and `/webhooks/{provider}` endpoints.
- Stub verification: requires `x-signature` header; otherwise returns HTTP 400.
- On valid request, returns 202-style acceptance with a generated `envelope_id` (UUID4). No external calls are made.
