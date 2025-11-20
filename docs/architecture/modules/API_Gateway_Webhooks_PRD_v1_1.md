# API Gateway & Webhooks Module — Product Requirements Document (PRD)

**Product:** ZeroUI (Project Aura)  
**Module:** API Gateway & Webhooks  
**Module ID:** M36  
**Document Type:** Product Requirements Document (Implementation-Ready)  
**Version:** v1.2 (validated and fixed)  
**Owner:** Platform / Core Services

---

## 0. Module Identity

```json
{
  "module_id": "M36",
  "name": "API Gateway & Webhooks",
  "version": "1.0.0",
  "description": "Single ingress and egress edge for all HTTP(S) traffic between ZeroUI backends and external systems",
  "supported_events": [
    "api_request_routed",
    "api_request_blocked",
    "webhook_event_scheduled",
    "webhook_event_delivered",
    "webhook_event_failed",
    "webhook_inbound_accepted",
    "webhook_inbound_rejected",
    "webhook_inbound_duplicate"
  ],
  "policy_categories": ["security", "integration", "observability"],
  "api_endpoints": {
    "health": "/gateway/v1/health",
    "metrics": "/gateway/v1/metrics",
    "webhooks": "/v1/tenants/{tenant_id}/webhooks",
    "webhook_receiver": "/v1/webhooks/{integration_id}"
  },
  "performance_requirements": {
    "gateway_routing_ms_max": 50,
    "auth_validation_ms_max": 10,
    "rate_limit_check_ms_max": 5,
    "webhook_delivery_ms_max": 200,
    "max_memory_mb": 4096
  },
  "service_category": "shared-services",
  "service_directory": "src/cloud-services/shared-services/api-gateway-webhooks/"
}
```

---

## 1. Module Summary

### 1.1 Purpose

The **API Gateway & Webhooks Module** is the **single ingress and egress edge** for all HTTP(S) traffic between ZeroUI’s backend (Tenant Cloud + Product Cloud) and the outside world (Edge Agents, tenant systems, 3rd-party services).

It provides:

1. **Synchronous APIs** via an API gateway (REST-style) for:
   - Edge Agent ↔ Core communication.
   - Tenant backend integrations (e.g., CI/CD, ticketing systems) using authenticated APIs.

2. **Asynchronous event delivery** via **webhooks**:
   - ZeroUI → tenant systems (ZeroUI as *webhook producer*).
   - Tenant / third-party systems → ZeroUI (ZeroUI as *webhook consumer*).

The module enforces **authentication, authorization, rate limiting, tenant isolation, observability, and security controls** at the edge, aligned with the rest of the ZeroUI platform.

### 1.2 Scope

- **In-scope**
  - Unified API gateway for all external HTTP(S) traffic into ZeroUI backends.
  - Webhook **delivery service** (producer) with retry, backoff, signing, idempotency metadata.
  - Webhook **receiver** endpoints for tenant/3rd-party events with idempotent handling and signature / token verification.
  - Per-tenant **routing, auth, throttling, logging, metrics** at the edge (integration with existing IAM, Key & Trust, Budgeting/Rate-Limiting, Observability modules).
  - Receipts for privileged decisions (accepted / rejected / rate limited / signature failure / webhook delivery result).

- **Out of Scope (handled by other modules)**
  - Long-term configuration UI (no new dashboards).
  - IAM: identity models, roles, permissions (IAM module).
  - Key & trust lifecycle, KIDs, key rotation (Key & Trust Management).
  - Budget and dynamic rate-limiting policies (Budgeting, Rate-Limiting & Cost Observability module).
  - Deep analytics dashboards (Observability module).

---

## 2. Objectives & Non-Goals

### 2.1 Objectives

| ID  | Objective                                                                                           | Evidence / Success Criteria                                                  |
|-----|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| O1  | Single secure ingress for all external HTTP(S) traffic                                             | All external service URLs terminate at Gateway domains only.                 |
| O2  | Provide reliable webhook delivery (at-least-once, with retries & backoff)                          | ≥99.9% of eligible webhook events eventually delivered or explicitly dead-lettered. |
| O3  | Enforce rate limiting, auth, and tenancy boundaries at the edge                                    | Confirmed by tests & logs: 401/403 for invalid tokens, 429 for limit breach. |
| O4  | Ensure webhook & API security aligned with OWASP API Security Top 10                               | Security review shows coverage for BOLA, auth, injection, etc.               |
| O5  | Emit structured logs, metrics, and JSONL receipts for all privileged edge decisions                | Gateway logs & receipts sampled in pre-prod; queries show correct structure. |

### 2.2 Non-Goals

- Not a full message bus / streaming platform (no Kafka-like semantics).
- Not a full-featured API developer portal.
- Not a scheduler or rule engine (uses signals from other modules if needed).
- Not an ETL or heavy transformation layer; only **lightweight** request/response mediation.

---

## 3. Architectural Context

### 3.1 Placement in ZeroUI Planes

- **Laptop Plane (Edge Agent + VS Code extension)**
  - Edge Agent acts as **HTTP client** to the API Gateway.
  - No direct inbound internet traffic to the laptop.

- **Tenant Cloud Plane**
  - Tenant-facing API gateway endpoints for integration in the tenant’s infrastructure.
  - Optional tenant-local webhooks (if deployed fully in-tenant mode).

- **Product Cloud Plane**
  - Global API Gateway endpoints (multi-tenant).
  - Global webhook producer & consumer services.

- **Shared Services Plane**
  - Central policy registry (GSMD / policy bundles), trust / KID registry, observability backends, receipts/audit subsystem.

All external HTTP flows route:

> Client → API Gateway → Internal service(s)  
> ZeroUI events → Webhook Dispatcher → Tenant endpoints

### 3.2 Dependencies

- **IAM Module**: Token and permission validation (JWTs, API keys, etc.).
- **Key & Trust Management**: TLS cert handling; webhook signing keys and KID references.
- **Budgeting, Rate-Limiting & Cost Observability Module**: Rate limits, quotas, cost signals, retry budgets and other limit policies.
- **Policy / GSMD**: Global settings and policy bundles that define thresholds, limits, feature switches, per-tenant behaviours and deprecations.
- **Observability Module**: Metrics, traces, alerting.
- **Receipts / Audit Module**: JSONL receipts; fsync; optional Ed25519 signing; evidence IDs.

> **No Local Policy Engine Constraint**  
> The API Gateway & Webhooks module **must not** implement its own policy engine or rule DSL. All policy decisions (route enablement, version deprecation, rate limits, retry parameters, data minimisation, etc.) are delegated to GSMD/policy bundles and the Budgeting & Rate-Limiting module.

### 3.3 Policy & Configuration Sourcing

All limits, thresholds, retry policies, maximum body/header sizes, SLA targets and similar parameters mentioned in this PRD are **policy-driven**:

- Concrete values **must** be obtained from:
  - ZeroUI **Global Settings / GSMD** and/or
  - The **Budgeting & Rate-Limiting** module, and
  - Environment configuration / defaults, following the standard platform precedence (policy → env → defaults).
- These values **must not** be hard-coded inside this module’s implementation.

### 3.4 Receipts & Audit Integration

All receipts emitted by this module:

- **Must** conform to the global **ZeroUI DecisionReceipt schema** (see `gsmd/schema/receipt.schema.json` and `src/edge-agent/shared/receipt-types.ts`).
- **Must** use correct field structure:
  - **`gate_id`**: Operation type identifier (see §4.1.5, §4.2.6, §4.3.5 for values)
  - **`evaluation_point`**: `"pre-deploy"` for gateway decisions, `"post-deploy"` for webhook deliveries
  - **`inputs`**: Request/event data (including `request_id`, `tenant_id`, `event_id`, etc.)
  - **`decision.status`**: `"pass"` | `"warn"` | `"soft_block"` | `"hard_block"`
  - **`decision.rationale`**: Human-readable reason codes
  - **`result`**: Decision outcomes (see receipt examples in §4.1.5, §4.2.6, §4.3.5)
  - **`snapshot_hash`**: SHA-256 hash (format: `sha256:hex`) - maps to `policy_snapshot_hash` in GSMD
  - **`actor.repo_id`**: Repository identifier
  - **`evidence_handles`**: Optional array (see §12 for usage)
- **Must** be written via the shared **Receipts subsystem**:
  - Append-only JSONL files,
  - fsync semantics,
  - Optional Ed25519 signing according to global receipts configuration.
- This module **must not** introduce new receipt sinks or formats; it only calls the shared receipts API.

---

## 4. Functional Requirements

### 4.1 F1 — Unified API Gateway (Ingress)

**Goal:** Provide a unified gateway for external HTTP APIs with routing, auth, rate limiting, and logging.

#### 4.1.1 Routing & Versioning

- Gateway must support:
  - Path-based routing, e.g., `/v1/tenants/{tenant_id}/...`, `/v1/agents/...`.
  - Header-based routing for internal services if needed (`X-ZeroUI-Service`).
  - API versioning via URL prefix (`/v1`, `/v2`) and deprecation flags.

**Key Behaviour**

- If path matches no route → return `404` (structured JSON error).
- If version is deprecated and disabled by policy (from GSMD) → return `410 Gone`.

#### 4.1.2 Authentication & Authorization

- Every **protected** endpoint must:
  - Validate credentials using IAM module (JWTs, API keys).
  - Enforce **least privilege** (scopes/roles per path + verb) as defined in policy.
- Anonymous endpoints (health, callbacks explicitly marked public) must be explicitly whitelisted in policy.

#### 4.1.3 Rate Limiting & Throttling

- Per-tenant, per-client rate limiting enforced at the gateway:
  - Gateway must request and apply rate-limit decisions (allow / deny / slow) from the **Budgeting & Rate-Limiting** module, using the limits defined in GSMD/policy.
- On limit breach → return `429 Too Many Requests` with structured JSON body and retry-after hint (if provided by policy).

The gateway **must not** embed hard-coded rate-limit numbers; all limits come from policy / GSMD / Budgeting.

#### 4.1.4 Request / Response Normalisation

- Normalise incoming HTTP:
  - Enforce max header size, body size and timeouts from policy/GSMD (no hard-coded values).
  - Enforce allowed content-types (e.g., JSON only, unless configured by policy).
- Strip sensitive headers before forwarding (e.g., internal auth headers).
- Add standard ZeroUI headers:
  - `X-ZeroUI-Request-Id`
  - `X-ZeroUI-Tenant-Id`
  - `X-ZeroUI-Edge-Version` (when Edge Agent is caller).

#### 4.1.5 Logging & Receipts

- For each request:
  - Write **gateway access log** entry (method, path, tenant, status, latency, auth result).
- For privileged decisions (auth fail, rate limited, blocked, WAF block), emit **DecisionReceipts** via the shared Receipts subsystem conforming to the global DecisionReceipt schema:
  - **`gate_id`**: Operation type identifier (e.g., `"api-gateway-auth"`, `"api-gateway-rate-limit"`, `"api-gateway-routing"`, `"api-gateway-waf"`)
  - **`evaluation_point`**: `"pre-deploy"` (gateway decisions occur before request processing)
  - **`inputs`**: Contains `request_id`, `tenant_id`, `endpoint`, `method`, `client_ip`, `user_agent`
  - **`decision.status`**: `"pass"` | `"warn"` | `"soft_block"` | `"hard_block"`
  - **`decision.rationale`**: Human-readable reason code (e.g., `"auth_missing_or_invalid"`, `"rate_limit_exceeded"`, `"waf_security_filter_blocked"`, `"tenant_mismatch"`)
  - **`result`**: Contains `allowed` (boolean), `http_status` (integer), `retry_after` (seconds, if applicable), `policy_applied` (policy ID)
  - **`policy_version_ids`**: Array of policy version IDs used in decision
  - **`snapshot_hash`**: SHA-256 hash of policy snapshot (format: `sha256:hex`)
  - **`actor.repo_id`**: Repository identifier (if available)
  - **`evidence_handles`**: Optional array of evidence handles for security blocks (WAF logs, signature failures)
  - All other required fields from the global DecisionReceipt schema

The gateway must not write ad-hoc receipts; it always uses the shared DecisionReceipt API.

---

### 4.2 F2 — Webhook Producer (ZeroUI → Tenant Systems)

ZeroUI emits outbound events (e.g., policy decisions, gate outcomes, alerts) to tenant-defined HTTP endpoints.

#### 4.2.1 Subscription Model

- **Webhook subscription** is a config object with:
  - `subscription_id`
  - `tenant_id`
  - `endpoint_url` (HTTPS only unless policy allows exceptions)
  - `event_types[]`
  - `secret` (for HMAC signature, held as secret/KID reference via Key & Trust)
  - `status` (active / paused)
  - `delivery_mode` (sync/async — default async)
- Subscriptions are stored in tenant config (no UI; configured via policy/config repository or admin API if allowed).

#### 4.2.2 Event Construction

Every webhook delivery must include:

- `event_id` (UUID, globally unique)
- `event_type` (e.g., `zeroUI.policy.decision`)
- `occurred_at` (UTC timestamp)
- `tenant_id`
- `data` (event payload, JSON)
- `delivery_attempt` (integer; incremented on retries)

Payload is designed to be **idempotent** on consumer side using `event_id`.

#### 4.2.3 Signing & Security

- For each delivery, compute HMAC (e.g., SHA-256) over payload using `secret` and include header, e.g.:

  - `X-ZeroUI-Signature: scheme=v1,signature=<hex>`

- Only HTTPS endpoints allowed by default; insecure endpoints can be explicitly allowed only by policy.
- Webhook secrets are managed through the **Key & Trust** subsystem (secret/KID references), not stored in plain-text application config.

#### 4.2.4 Delivery Semantics & Retries

- Delivery is **at-least-once**:
  - On non-2xx response or timeout → enqueue retry with **exponential backoff**.
  - The **maximum retry window, maximum number of attempts, and backoff schedule** are defined in policy/GSMD (for example, a default “up to 24 hours with exponential backoff” may be specified in GSMD), and **must not** be hard-coded.
- Gateway must:
  - Avoid duplicate concurrent deliveries for the same `event_id` to the same subscription.
  - Ensure no single failing endpoint blocks other tenants.

#### 4.2.5 Response Handling

- For each attempt, capture:
  - HTTP status, response time, error type (timeout, DNS, TLS).
  - Store in delivery log (per-event history).

- If consumer responds with explicit “unsubscribe” pattern (if supported by contract and policy), gateway can mark subscription as `paused`.

#### 4.2.6 Receipts

- Emit DecisionReceipts via the shared Receipts subsystem for webhook delivery operations, conforming to the global DecisionReceipt schema:
  - **`gate_id`**: `"webhook-producer"` for all webhook producer receipts
  - **`evaluation_point`**: `"post-deploy"` (webhook events occur after deployment/processing)
  - **`inputs`**: Contains `event_id`, `subscription_id`, `tenant_id`, `endpoint_url`, `event_type`, `delivery_attempt`
  - **`decision.status`**: 
    - `"pass"` for successful delivery
    - `"warn"` for retryable failures
    - `"soft_block"` for temporary failures (will retry)
    - `"hard_block"` for permanent failures (dead-lettered)
  - **`decision.rationale`**: Reason code (e.g., `"webhook_delivery_success"`, `"webhook_delivery_failed_timeout"`, `"webhook_delivery_failed_http_error"`, `"webhook_delivery_exhausted_retries"`)
  - **`result`**: Contains `delivery_status` (`"delivered"` | `"failed"` | `"dead_lettered"`), `http_status` (if available), `response_time_ms`, `attempts`, `next_retry_at` (if applicable), `dlq_location` (if dead-lettered)
  - **`policy_version_ids`**: Array of policy version IDs used for retry/backoff decisions
  - **`snapshot_hash`**: SHA-256 hash of policy snapshot
  - **`actor.repo_id`**: Repository identifier (if available)
  - **`evidence_handles`**: Optional array of evidence handles (delivery logs, error responses)

---

### 4.3 F3 — Webhook Receiver (ZeroUI as Consumer)

ZeroUI accepts inbound webhooks from tenant / 3rd-party services (optional integration path).

#### 4.3.1 Endpoint Model

- Multi-tenant endpoints:
  - `/v1/webhooks/{integration_id}`

`integration_id` corresponds to a configuration that includes:

- Allowed source IP ranges / domains (optional).
- Shared secret / signature scheme.
- Expected `event_types[]`.
- Whether to synchronously or asynchronously forward internally.

Configuration is stored in policy/GSMD or tenant config; no hard-coded endpoints beyond the templated path.

#### 4.3.2 Authentication & Verification

- For each inbound request:
  - Validate signature according to integration’s scheme.
  - Optionally validate source IP / mTLS if configured.
  - On verification failure → respond `401/403` and do **not** enqueue event.

#### 4.3.3 Idempotency & Ordering

- Expect at-least-once, possibly out-of-order deliveries from providers.
- Use provider’s `event_id` or `id` as idempotency key:
  - Maintain short-term idempotency store (per integration) to drop duplicates.
- Do not rely on order; downstream consumers must handle reordering.

#### 4.3.4 Processing Model

- **Fast acknowledgment:** Receiver must quickly validate and persist event to internal queue, then return `2xx` to provider; heavy processing happens asynchronously.
- Internal pipeline:
  - Validate schema & auth.
  - Persist to durable queue.
  - Downstream modules pull and process.

All internal queue types, capacities, and retention windows are policy/GSMD controlled.

#### 4.3.5 Receipts

- Emit DecisionReceipts via the shared Receipts subsystem for webhook receiver operations, conforming to the global DecisionReceipt schema:
  - **`gate_id`**: `"webhook-receiver"` for all webhook receiver receipts
  - **`evaluation_point`**: `"pre-deploy"` (validation occurs before event processing)
  - **`inputs`**: Contains `event_id` (provider's event ID), `integration_id`, `tenant_id`, `endpoint_path`, `source_ip`, `event_type`
  - **`decision.status`**: 
    - `"pass"` for accepted events
    - `"warn"` for duplicate events (accepted but not reprocessed)
    - `"soft_block"` for temporary rejections (may retry)
    - `"hard_block"` for permanent rejections (invalid signature, unauthorized)
  - **`decision.rationale`**: Reason code (e.g., `"webhook_inbound_accepted"`, `"webhook_inbound_duplicate"`, `"webhook_inbound_rejected_invalid_signature"`, `"webhook_inbound_rejected_unauthorized"`, `"webhook_inbound_rejected_schema_mismatch"`)
  - **`result`**: Contains `accepted` (boolean), `forwarded` (boolean), `duplicate` (boolean), `rejection_reason` (if rejected), `internal_queue_id` (if accepted)
  - **`policy_version_ids`**: Array of policy version IDs used for validation
  - **`snapshot_hash`**: SHA-256 hash of policy snapshot
  - **`actor.repo_id`**: Repository identifier (if available)
  - **`evidence_handles`**: Optional array of evidence handles (signature verification logs, schema validation errors)

---

### 4.4 F4 — Tenant & Route Management

- All routes must be **tenant-aware**:
  - Tenant determined from token claims, API key mapping, or path space.
- Gateway must prevent cross-tenant data leaks (BOLA/BFLA protection).
- Tenant routing rules are defined in policy/GSMD; the gateway does not assume tenant mappings beyond what policy provides.

---

### 4.5 F5 — Security & OWASP Alignment

- Enforce OWASP API Security Top 10 controls:
  - BOLA (object-level checks).
  - Excessive data exposure (only necessary fields exposed).
  - Lack of rate limiting (integration with rate-limiting module).
  - Broken auth and authz (strict IAM integration).
  - Injection protections via centralized validation and WAF integration.
- Integrate with WAF or equivalent protections where possible (SQLi/XSS filters).
- Security thresholds (e.g., maximum sizes, WAF modes) are configured via policy/GSMD, not hard-coded.

---

### 4.6 F6 — Observability

Gateway must emit:

- **Metrics**
  - Request count, latency (p50/p90/p99), error rate per route and tenant.
  - Rate-limit events, auth failures, webhook delivery success/failure counts.
- **Logs**
  - Structured JSON logs with request-id, tenant-id, auth outcome, decision reason.
- **Traces**
  - Propagate correlation headers to downstream services (e.g., `X-Request-Id`).

All metric names and sampling policies are aligned with the platform observability standards; configuration is policy-driven where applicable.

---

## 5. Data & API Contracts (High-Level)

> Note: This PRD defines the **shape** of critical objects and endpoints. Full OpenAPI specs are generated from these definitions and reviewed.

### 5.1 Key Data Structures

#### 5.1.1 WebhookSubscription (tenant config)

```json
{
  "subscription_id": "ws_123",
  "tenant_id": "t_abc",
  "endpoint_url": "https://example.com/webhooks/zeroui",
  "event_types": ["zeroUI.policy.decision", "zeroUI.gate.outcome"],
  "secret": "KID_OR_SECRET_REF",
  "status": "active",
  "delivery_mode": "async",
  "created_at": "2025-11-19T12:34:56Z",
  "updated_at": "2025-11-19T12:34:56Z"
}
```

#### 5.1.2 WebhookEvent (outbound payload)

```json
{
  "event_id": "wev_123",
  "event_type": "zeroUI.policy.decision",
  "occurred_at": "2025-11-19T12:34:56Z",
  "tenant_id": "t_abc",
  "data": {
    "decision_id": "dec_789",
    "gate_id": "gate_release_risk",
    "decision": "soft_block"
  },
  "delivery_attempt": 1
}
```

#### 5.1.3 InboundWebhookEnvelope

```json
{
  "event_id": "provider_456",
  "event_type": "build.completed",
  "occurred_at": "2025-11-19T12:34:56Z",
  "tenant_ref": "t_abc",
  "data": {
    "...": "provider-specific JSON"
  }
}
```

### 5.2 Representative API Endpoints

#### 5.2.1 Create Webhook Subscription (Tenant Admin)

- **Method:** `POST /v1/tenants/{tenant_id}/webhooks`
- **Auth:** Tenant admin token (IAM).
- **Body:** `WebhookSubscription` (without `subscription_id`, timestamps).
- **Responses:**
  - `201 Created` + created subscription.
  - `400 Bad Request` for invalid URL / event types.
  - `401/403` for auth/permission issues.

#### 5.2.2 List Webhook Subscriptions

- **Method:** `GET /v1/tenants/{tenant_id}/webhooks`
- **Response:** Array of `WebhookSubscription`.

#### 5.2.3 Pause / Resume Subscription

- **Method:** `PATCH /v1/tenants/{tenant_id}/webhooks/{subscription_id}`
- **Body:** `{ "status": "paused" | "active" }`

#### 5.2.4 Webhook Receiver Endpoint (Generic)

- **Method:** `POST /v1/webhooks/{integration_id}`
- **Auth:** Signature header (integration-specific).
- **Response:**
  - `2xx` for accepted.
  - `401/403` for signature/permission issues.
  - `4xx` for schema issues.

### 5.3 Error Response Schema

All non-2xx responses from the API Gateway must conform to the following error response schema:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {
      "request_id": "string",
      "tenant_id": "string",
      "endpoint": "string",
      "timestamp": "string"
    },
    "retryable": boolean
  }
}
```

**Error Codes:**
- `INVALID_REQUEST` - Schema violations, invalid parameters (400)
- `UNAUTHENTICATED` - Missing/invalid credentials (401)
- `UNAUTHORIZED` - Insufficient permissions (403)
- `NOT_FOUND` - Route not found (404)
- `GONE` - API version deprecated (410)
- `RATE_LIMITED` - Rate limit exceeded (429)
- `INTERNAL_ERROR` - Unexpected gateway error (500)
- `SERVICE_UNAVAILABLE` - Upstream service unavailable (503)

### 5.4 OpenAPI 3.0.3 Specifications

#### 5.4.1 Gateway Routes

```yaml
openapi: 3.0.3
info:
  title: ZeroUI API Gateway
  version: 1.0.0
  description: Unified API gateway for all external HTTP(S) traffic

servers:
  - url: https://api.zeroui.com/v1
    description: Production gateway

paths:
  /tenants/{tenant_id}/resources:
    get:
      operationId: getTenantResources
      summary: Get tenant resources
      parameters:
        - name: tenant_id
          in: path
          required: true
          schema:
            type: string
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
        '401':
          $ref: '#/components/responses/Unauthenticated'
        '403':
          $ref: '#/components/responses/Unauthorized'
        '429':
          $ref: '#/components/responses/RateLimited'

  /agents/{agent_id}/status:
    get:
      operationId: getAgentStatus
      summary: Get edge agent status
      parameters:
        - name: agent_id
          in: path
          required: true
          schema:
            type: string
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Success
        '401':
          $ref: '#/components/responses/Unauthenticated'
        '429':
          $ref: '#/components/responses/RateLimited'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  responses:
    Unauthenticated:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    Unauthorized:
      description: Insufficient permissions
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    RateLimited:
      description: Rate limit exceeded
      headers:
        Retry-After:
          schema:
            type: integer
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

  schemas:
    ErrorResponse:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
          properties:
            code:
              type: string
              enum:
                - INVALID_REQUEST
                - UNAUTHENTICATED
                - UNAUTHORIZED
                - NOT_FOUND
                - GONE
                - RATE_LIMITED
                - INTERNAL_ERROR
                - SERVICE_UNAVAILABLE
            message:
              type: string
            details:
              type: object
              additionalProperties: true
            retryable:
              type: boolean
```

#### 5.4.2 Webhook Subscription Management

```yaml
openapi: 3.0.3
info:
  title: ZeroUI Webhook Subscription API
  version: 1.0.0

paths:
  /v1/tenants/{tenant_id}/webhooks:
    post:
      operationId: createWebhookSubscription
      summary: Create webhook subscription
      parameters:
        - name: tenant_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/WebhookSubscriptionCreate'
      security:
        - bearerAuth: []
      responses:
        '201':
          description: Subscription created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WebhookSubscription'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthenticated'
        '403':
          $ref: '#/components/responses/Unauthorized'

    get:
      operationId: listWebhookSubscriptions
      summary: List webhook subscriptions
      parameters:
        - name: tenant_id
          in: path
          required: true
          schema:
            type: string
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/WebhookSubscription'

  /v1/tenants/{tenant_id}/webhooks/{subscription_id}:
    patch:
      operationId: updateWebhookSubscription
      summary: Update webhook subscription
      parameters:
        - name: tenant_id
          in: path
          required: true
        - name: subscription_id
          in: path
          required: true
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  enum: [active, paused]
      security:
        - bearerAuth: []
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/WebhookSubscription'
        '400':
          $ref: '#/components/responses/BadRequest'
        '404':
          $ref: '#/components/responses/NotFound'

components:
  schemas:
    WebhookSubscriptionCreate:
      type: object
      required: [endpoint_url, event_types]
      properties:
        endpoint_url:
          type: string
          format: uri
        event_types:
          type: array
          items:
            type: string
        secret:
          type: string
          description: KID reference or secret identifier
        delivery_mode:
          type: string
          enum: [sync, async]
          default: async

    WebhookSubscription:
      type: object
      required: [subscription_id, tenant_id, endpoint_url, event_types, status]
      properties:
        subscription_id:
          type: string
        tenant_id:
          type: string
        endpoint_url:
          type: string
          format: uri
        event_types:
          type: array
          items:
            type: string
        secret:
          type: string
          description: KID reference (never raw secret)
        status:
          type: string
          enum: [active, paused]
        delivery_mode:
          type: string
          enum: [sync, async]
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
```

#### 5.4.3 Webhook Receiver Endpoint

```yaml
openapi: 3.0.3
info:
  title: ZeroUI Webhook Receiver API
  version: 1.0.0

paths:
  /v1/webhooks/{integration_id}:
    post:
      operationId: receiveWebhook
      summary: Receive inbound webhook
      parameters:
        - name: integration_id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/InboundWebhookEnvelope'
      security:
        - signatureAuth: []
      responses:
        '200':
          description: Webhook accepted
          content:
            application/json:
              schema:
                type: object
                properties:
                  accepted:
                    type: boolean
                  event_id:
                    type: string
        '204':
          description: Webhook accepted (duplicate, no processing)
        '401':
          $ref: '#/components/responses/Unauthenticated'
        '403':
          $ref: '#/components/responses/Unauthorized'
        '400':
          $ref: '#/components/responses/BadRequest'

components:
  securitySchemes:
    signatureAuth:
      type: http
      scheme: signature
      description: Integration-specific signature scheme (HMAC, etc.)

  schemas:
    InboundWebhookEnvelope:
      type: object
      required: [event_id, event_type, occurred_at, data]
      properties:
        event_id:
          type: string
        event_type:
          type: string
        occurred_at:
          type: string
          format: date-time
        tenant_ref:
          type: string
        data:
          type: object
          additionalProperties: true
```

---

## 6. Privacy, Trust & Data Minimization

- Gateway must not log secrets or full payloads containing PII by default; only:
  - Truncated payloads (configurable via policy/GSMD).
  - Metadata (event_id, event_type, tenant, status, timing).
- Webhook `secret` stored via Key & Trust Management (as KID reference, not raw secret where possible).
- Tenants may configure **data minimization** policies for outbound payloads (e.g., mask certain fields before sending) via GSMD/policy.

---

## 7. Performance & Reliability Requirements

- Gateway must:
  - Accept and route requests within **p95 latency targets** defined in policy/GSMD for each environment. These targets **must not** be hard-coded.
  - Enforce timeouts on upstream backends using policy-defined values.
  - Gracefully degrade under load:
    - Prefer rate-limiting (429) over timeouts when overloaded, guided by Budgeting & Rate-Limiting policies.
- Webhook dispatcher:
  - Must be able to resume cleanly after restart (in-flight queue durable).
  - Must not lose events once acknowledged by internal producers (at-least-once semantics).
  - Queue capacities and back-pressure thresholds are defined in policy/GSMD, not hard-coded.

---

## 8. Rollout & Migration

- Implement in phases:
  1. **Shadow mode**: Gateway mirrors traffic but doesn’t enforce blocking decisions; only logs and receipts.
  2. **Warn mode**: Start returning warnings in headers while logging blocked-would-be decisions.
  3. **Enforce mode**: Enable hard blocking based on policy.

- Existing direct service endpoints (if any) must be progressively deprecated behind the gateway, with deprecation status driven by policy/GSMD.

---

## 9. GSMD Module Structure

The API Gateway & Webhooks module (M36) requires the following GSMD module structure:

### 9.1 GSMD Module Directory Structure

```
gsmd/gsmd/modules/M36/
├── receipts_schema/
│   └── v1/
│       └── snapshot.json
├── messages/
│   └── v1/
│       └── snapshot.json
└── gate_rules/
    └── v1/
        └── snapshot.json
```

### 9.2 Receipts Schema Snapshot

**Location:** `gsmd/gsmd/modules/M36/receipts_schema/v1/snapshot.json`

```json
{
  "snapshot_id": "SNAP.M36.receipts_schema.v1",
  "module_id": "M36",
  "slug": "receipts_schema",
  "version": {
    "major": 1
  },
  "schema_version": "1.0.0",
  "policy_version_ids": ["POL-INIT"],
  "snapshot_hash": "sha256:PLACEHOLDER",
  "signature": "base64:PLACEHOLDER",
  "kid": "KID:zero-ui-product:ed25519:2025-01",
  "effective_from": "2025-01-XXT00:00:00Z",
  "deprecates": [],
  "evaluation_points": ["pre-deploy", "post-deploy"],
  "receipts": {
    "required": [
      "receipt_id",
      "gate_id",
      "evaluation_point",
      "policy_version_ids",
      "snapshot_hash",
      "timestamp_utc",
      "timestamp_monotonic_ms",
      "inputs",
      "decision",
      "result",
      "actor",
      "signature"
    ],
    "optional": [
      "evidence_handles",
      "degraded"
    ]
  },
  "gate_ids": [
    "api-gateway-auth",
    "api-gateway-rate-limit",
    "api-gateway-routing",
    "api-gateway-waf",
    "webhook-producer",
    "webhook-receiver"
  ]
}
```

### 9.3 Messages Snapshot

**Location:** `gsmd/gsmd/modules/M36/messages/v1/snapshot.json`

```json
{
  "snapshot_id": "SNAP.M36.messages.v1",
  "module_id": "M36",
  "slug": "messages",
  "version": {
    "major": 1
  },
  "schema_version": "1.0.0",
  "policy_version_ids": ["POL-INIT"],
  "snapshot_hash": "sha256:PLACEHOLDER",
  "signature": "base64:PLACEHOLDER",
  "kid": "KID:zero-ui-product:ed25519:2025-01",
  "effective_from": "2025-01-XXT00:00:00Z",
  "deprecates": [],
  "messages": {
    "problems": [
      "gateway.auth.failed",
      "gateway.rate_limit.exceeded",
      "gateway.routing.not_found",
      "gateway.waf.blocked",
      "webhook.delivery.failed",
      "webhook.receiver.invalid_signature",
      "webhook.receiver.duplicate"
    ],
    "status_pill": {
      "pass": "gateway.ok",
      "warn": "gateway.warn",
      "soft_block": "gateway.soft",
      "hard_block": "gateway.hard"
    },
    "cards": [
      "gateway.request.details",
      "gateway.webhook.subscription",
      "gateway.webhook.delivery"
    ]
  }
}
```

### 9.4 Field Name Mapping

**Note:** The DecisionReceipt schema uses `snapshot_hash` in TypeScript implementations, but GSMD schemas use `policy_snapshot_hash`. The mapping is:
- **TypeScript/Implementation:** `snapshot_hash` (string, format: `sha256:hex`)
- **GSMD Schema:** `policy_snapshot_hash` (string, format: `sha256:hex`)
- **Mapping:** Implementation must map `snapshot_hash` → `policy_snapshot_hash` when writing to GSMD format, and vice versa when reading.

**Request ID vs Receipt ID:**
- **`request_id`**: HTTP request identifier, included in `X-ZeroUI-Request-Id` header and stored in `inputs.request_id` of receipts
- **`receipt_id`**: Unique receipt identifier (UUID), top-level field in DecisionReceipt schema
- **Relationship:** Multiple receipts may reference the same `request_id` (e.g., auth receipt and rate-limit receipt for same request)

**Tenant ID Placement:**
- **`tenant_id`**: Stored in `inputs.tenant_id`, not as top-level field
- **`actor.repo_id`**: Repository identifier, separate from tenant_id
- **`actor_id`**: Optional user/service identity (if needed for audit)

---

## 10. Test Plan & Test Case Implementation Details

This section makes the module **Definition-of-Ready** for implementation: test types, coverage, and representative test cases.

### 10.1 Test Types

1. **Unit Tests**
   - Routing logic, signature computation/verification, backoff schedule (based on policy parameters), rate-limit decision handling.
2. **Contract / API Tests**
   - Validate endpoints against OpenAPI; verify status codes, JSON shapes.
3. **Integration Tests**
   - Full flow: client → gateway → backend; ZeroUI → webhook receiver; provider → ZeroUI receiver.
4. **Security Tests**
   - Auth bypass attempts, malformed tokens, signature replay, OWASP API Top 10 checks.
5. **Reliability / Webhook tests**
   - Retry & idempotency behaviour; duplicate deliveries; out-of-order events.
6. **Performance / Load Tests**
   - Gateway throughput & tail latency under realistic load; webhook dispatcher resilience using policy-driven thresholds.
7. **Observability / Receipts Tests**
   - Metrics, logs, and DecisionReceipts presence and correctness.

---

### 10.2 Representative Test Cases

### 10.3 Test Policy Fixtures

Test fixtures are GSMD policy bundles that provide configuration values for testing. All test fixtures must be stored in the test harness and loaded before test execution.

#### 10.3.1 Rate Limiting Policy Fixture

**Location:** `tests/fixtures/policies/rate_limiting_test.json`

```json
{
  "policy_id": "POL-RATE-LIMIT-TEST",
  "policy_type": "rate_limiting",
  "version": "1.0.0",
  "scope": {
    "tenant_id": "test_tenant_abc",
    "environment": "test"
  },
  "definition": {
    "rate_limits": {
      "api_requests": {
        "limit": 10,
        "window": "PT1M",
        "unit": "requests"
      },
      "webhook_deliveries": {
        "limit": 100,
        "window": "PT1H",
        "unit": "deliveries"
      }
    },
    "retry_after_header": true,
    "retry_after_seconds": 60
  }
}
```

#### 10.3.2 Webhook Retry/Backoff Policy Fixture

**Location:** `tests/fixtures/policies/webhook_retry_test.json`

```json
{
  "policy_id": "POL-WEBHOOK-RETRY-TEST",
  "policy_type": "webhook_delivery",
  "version": "1.0.0",
  "scope": {
    "tenant_id": "test_tenant_abc",
    "environment": "test"
  },
  "definition": {
    "retry_policy": {
      "max_attempts": 5,
      "max_retry_window": "PT24H",
      "backoff_schedule": {
        "initial_delay": "PT1S",
        "max_delay": "PT5M",
        "multiplier": 2.0,
        "jitter": true
      }
    },
    "dead_letter_queue": {
      "enabled": true,
      "location": "test_dlq"
    }
  }
}
```

#### 10.3.3 Gateway Timeout Policy Fixture

**Location:** `tests/fixtures/policies/gateway_timeout_test.json`

```json
{
  "policy_id": "POL-GATEWAY-TIMEOUT-TEST",
  "policy_type": "gateway_configuration",
  "version": "1.0.0",
  "scope": {
    "environment": "test"
  },
  "definition": {
    "timeouts": {
      "upstream_backend": "PT30S",
      "webhook_delivery": "PT10S",
      "auth_validation": "PT5S"
    },
    "max_request_size": 10485760,
    "max_header_size": 8192
  }
}
```

#### 10.3.4 Routing Policy Fixture

**Location:** `tests/fixtures/policies/routing_test.json`

```json
{
  "policy_id": "POL-ROUTING-TEST",
  "policy_type": "routing",
  "version": "1.0.0",
  "scope": {
    "environment": "test"
  },
  "definition": {
    "routes": [
      {
        "path": "/v1/tenants/{tenant_id}/resources",
        "methods": ["GET", "POST"],
        "backend_service": "test-backend",
        "auth_required": true,
        "rate_limit_policy": "POL-RATE-LIMIT-TEST"
      },
      {
        "path": "/v1/agents/{agent_id}/status",
        "methods": ["GET"],
        "backend_service": "test-backend",
        "auth_required": true
      }
    ],
    "api_versions": {
      "v1": {
        "status": "active",
        "deprecated": false
      }
    }
  }
}
```

#### 10.3.5 Webhook Subscription Test Fixture

**Location:** `tests/fixtures/webhooks/test_subscription.json`

```json
{
  "subscription_id": "ws_test_123",
  "tenant_id": "test_tenant_abc",
  "endpoint_url": "https://test-server.example.com/webhooks/zeroui",
  "event_types": ["zeroUI.policy.decision", "zeroUI.gate.outcome"],
  "secret": "KID:test:webhook:secret:2025-01",
  "status": "active",
  "delivery_mode": "async"
}
```

#### 10.2 Representative Test Cases

#### 10.2.1 API Gateway – Auth & Routing

**TC-API-001 — Valid Authenticated Request Routed Successfully**

- **Type:** Integration
- **Preconditions:**
  - Valid tenant token for `tenant_id = t_abc`.
  - Route `/v1/tenants/t_abc/resources` exists and backend stub returns 200.
  - Policy/GSMD contains appropriate routing and auth scopes.
- **Steps:**
  1. Send `GET /v1/tenants/t_abc/resources` with valid `Authorization` header.
- **Expected:**
  - Response `200`.
  - `X-ZeroUI-Request-Id` present.
  - Gateway access log contains entry with `status=200` and correct tenant.
  - No receipts with `gate_id = "api-gateway-auth"` and `decision.status = "hard_block"` or `decision.status = "soft_block"`.
- **Automation Notes:** Use HTTP client + log/receipt query; ensure configuration values (timeouts, limits) come from test policy fixtures (see §9.3 for fixture structure).

---

**TC-API-002 — Missing / Invalid Token Rejected**

- **Type:** Integration
- **Steps:**
  1. Call same endpoint as TC-API-001 with no `Authorization` header.
  2. Call with syntactically invalid token.
- **Expected:**
  - Response `401` / `403` with structured JSON error (see §5.3 for error response schema).
  - DecisionReceipt emitted with:
    - `gate_id = "api-gateway-auth"`
    - `evaluation_point = "pre-deploy"`
    - `decision.status = "hard_block"`
    - `decision.rationale = "auth_missing_or_invalid"`
    - `inputs.request_id` present
    - `inputs.tenant_id` present (if determinable)
    - `result.allowed = false`
    - `result.http_status = 401` or `403`
  - Metrics increment for auth failures.

---

**TC-API-003 — Rate Limit Enforcement**

- **Type:** Integration / Load
- **Preconditions:** Policy/GSMD sets low rate limit for test client (e.g., N requests per minute).
- **Steps:**
  1. Send N+M requests within the rate-limit interval.
- **Expected:**
  - First N succeed (2xx/expected responses).
  - Remaining return `429` with retry hint (if policy provides).
  - DecisionReceipts with:
    - `gate_id = "api-gateway-rate-limit"`
    - `evaluation_point = "pre-deploy"`
    - `decision.status = "hard_block"`
    - `decision.rationale = "rate_limit_exceeded"`
    - `result.allowed = false`
    - `result.http_status = 429`
    - `result.retry_after` present (if policy provides)
  - Metrics show increased `429` count.

---

#### 10.2.2 Webhook Producer – Delivery & Retries

**TC-WHP-001 — Successful Webhook Delivery**

- **Type:** Integration
- **Preconditions:**
  - Webhook subscription configured for `tenant_id=t_abc` pointing to test HTTP server.
  - Test server responds `200 OK`.
  - Policy/GSMD configured with default retry/backoff profile.
- **Steps:**
  1. Trigger event that generates webhook (e.g., simulated gate decision).
- **Expected:**
  - Webhook received at test server with:
    - Valid JSON body (matching `WebhookEvent` structure).
    - Non-empty `event_id` and `event_type`.
    - `delivery_attempt=1`.
    - Valid `X-ZeroUI-Signature` header (verifiable with shared secret/KID).
  - Dispatcher marks event as delivered.
  - DecisionReceipt persisted with:
    - `gate_id = "webhook-producer"`
    - `evaluation_point = "post-deploy"`
    - `decision.status = "pass"`
    - `decision.rationale = "webhook_delivery_success"`
    - `inputs.event_id` matches webhook event_id
    - `inputs.subscription_id` present
    - `result.delivery_status = "delivered"`
    - `result.http_status = 200`

---

**TC-WHP-002 — Retry on Non-2xx Response**

- **Type:** Integration
- **Preconditions:**
  - Same subscription, test server initially returns `500` for first K attempts, then `200`, with K determined by test policy.
  - Policy/GSMD defines backoff schedule and maximum attempts for the test tenant.
- **Steps:**
  1. Trigger one webhook event.
- **Expected:**
  - Dispatcher retries with exponential backoff according to policy parameters.
  - Test server logs multiple deliveries with **same `event_id`** and incrementing `delivery_attempt`.
  - Final status is success; no further retries.
  - DecisionReceipts logged for each attempt with:
    - `gate_id = "webhook-producer"`
    - `evaluation_point = "post-deploy"`
    - `inputs.delivery_attempt` incrementing
    - `decision.status = "warn"` or `"soft_block"` for retries, `"pass"` for final success
    - `decision.rationale` indicating retry reason or success
    - `result.delivery_status` reflecting attempt outcome
  - Final receipt marks success with `decision.status = "pass"` and `result.delivery_status = "delivered"`.

---

**TC-WHP-003 — Dead-Letter on Exhausted Retries**

- **Type:** Integration
- **Preconditions:** Endpoint always returns `500` or times out; policy/GSMD limits attempts/TTL.
- **Expected:**
  - Dispatcher retries until maximum attempts / TTL from policy is reached.
  - Event is moved to dead-letter store.
  - Final DecisionReceipt includes:
    - `gate_id = "webhook-producer"`
    - `evaluation_point = "post-deploy"`
    - `decision.status = "hard_block"`
    - `decision.rationale = "webhook_delivery_exhausted_retries"`
    - `result.delivery_status = "dead_lettered"`
    - `result.attempts` = maximum attempts from policy
    - `result.dlq_location` present
    - `result.last_error` present

---

#### 10.2.3 Webhook Producer – Signing & Security

**TC-WHP-004 — Signature Verification Positive**

- **Type:** Unit + Integration
- **Preconditions:** Known secret managed via Key & Trust (test KID).
- **Steps:**
  1. Capture outbound webhook payload.
  2. Recompute HMAC using secret.
- **Expected:**
  - Signature in `X-ZeroUI-Signature` header matches computed HMAC.

---

**TC-WHP-005 — Tampered Payload Detected by Consumer**

- **Type:** Integration
- **Steps:**
  1. Receive webhook at test consumer.
  2. Modify payload.
  3. Attempt to verify signature at consumer.
- **Expected:**
  - Verification fails; consumer stub rejects message (logged as such in tests).

---

#### 10.2.4 Webhook Receiver – Idempotency & Duplicates

**TC-WHR-001 — Accept First Delivery, Ignore Duplicate**

- **Type:** Integration
- **Preconditions:** Inbound integration configured, idempotency store enabled with policy-defined retention.
- **Steps:**
  1. Send webhook with `event_id=E123` and valid signature.
  2. Send same payload again (duplicate).
- **Expected:**
  - First request:
    - Response `2xx`.
    - Event stored and forwarded internally.
    - DecisionReceipt with:
      - `gate_id = "webhook-receiver"`
      - `evaluation_point = "pre-deploy"`
      - `decision.status = "pass"`
      - `decision.rationale = "webhook_inbound_accepted"`
      - `result.accepted = true`
      - `result.duplicate = false`
      - `result.forwarded = true`
  - Second request:
    - Response `2xx` (or `204`) to provider.
    - No duplicate internal processing.
    - DecisionReceipt with:
      - `gate_id = "webhook-receiver"`
      - `evaluation_point = "pre-deploy"`
      - `decision.status = "warn"`
      - `decision.rationale = "webhook_inbound_duplicate"`
      - `result.accepted = true`
      - `result.duplicate = true`
      - `result.forwarded = false`

---

**TC-WHR-002 — Reject Webhook with Invalid Signature**

- **Type:** Integration
- **Steps:**
  1. Send webhook with correct shape but incorrect signature.
- **Expected:**
  - Response `401/403`.
  - No internal event created.
  - DecisionReceipt with:
    - `gate_id = "webhook-receiver"`
    - `evaluation_point = "pre-deploy"`
    - `decision.status = "hard_block"`
    - `decision.rationale = "webhook_inbound_rejected_invalid_signature"`
    - `result.accepted = false`
    - `result.rejection_reason = "invalid_signature"`

---

#### 10.2.5 Security & OWASP Alignment

**TC-SEC-001 — BOLA Protection**

- **Type:** Integration / Security
- **Scenario:** Attempt to access another tenant’s resources.
- **Steps:**
  1. Authenticated token for `tenant_id=t_abc`.
  2. Call `/v1/tenants/t_xyz/resources` (where `t_xyz != t_abc`).
- **Expected:**
  - Response `403` (or `404` without leaking existence).
  - DecisionReceipt with:
    - `gate_id = "api-gateway-auth"` or `"api-gateway-routing"`
    - `evaluation_point = "pre-deploy"`
    - `decision.status = "hard_block"`
    - `decision.rationale = "authorization_tenant_mismatch"`
    - `result.allowed = false`
    - `result.http_status = 403`

---

**TC-SEC-002 — Injection Attempt Blocked**

- **Type:** Security test
- **Steps:**
  1. Send request with payload containing injection payload (e.g., basic SQLi string) to a path.
- **Expected:**
  - WAF/gateway rejects or sanitizes according to configured security policy.
  - Response is safe; no internal error leakage.
  - DecisionReceipt with:
    - `gate_id = "api-gateway-waf"`
    - `evaluation_point = "pre-deploy"`
    - `decision.status = "hard_block"`
    - `decision.rationale = "waf_security_filter_blocked"`
    - `result.allowed = false`
    - `result.http_status = 400` or `403`
    - `evidence_handles` may contain WAF log references

---

#### 10.2.6 Observability & Receipts

**TC-OBS-001 — Metrics Emitted for Requests**

- **Type:** Integration
- **Steps:**
  1. Send N successful requests and M failed (auth / rate limit) using policy fixtures.
- **Expected:**
  - Metrics show N successes and M failures.
  - Rate-limit metrics reflect `429` count.
  - Logs and receipts correlate via `inputs.request_id` (receipts) and `X-ZeroUI-Request-Id` (logs).

---

**TC-REC-001 — Receipt Structure Conformance**

- **Type:** Unit / Integration
- **Steps:**
  1. Trigger:
     - An auth failure,
     - A rate limit block,
     - A webhook delivered,
     - A webhook failed,
     - An inbound webhook rejected and a duplicate.
  2. Collect the corresponding receipts from the shared Receipts subsystem.
- **Expected:**
  - Each receipt:
    - Conforms to the global **DecisionReceipt JSON Schema** used across ZeroUI (see `gsmd/schema/receipt.schema.json`).
    - Contains all required fields: `receipt_id`, `gate_id`, `evaluation_point`, `policy_version_ids`, `snapshot_hash` (mapped from `policy_snapshot_hash` in GSMD), `inputs` (containing `request_id` or `event_id`, `tenant_id`), `decision` (with `status`, `rationale`), `result`, `actor` (with `repo_id`), `signature`.
    - Uses correct `gate_id` values: `"api-gateway-auth"`, `"api-gateway-rate-limit"`, `"api-gateway-routing"`, `"api-gateway-waf"`, `"webhook-producer"`, `"webhook-receiver"`.
    - Uses correct `evaluation_point` values: `"pre-deploy"` for gateway decisions, `"post-deploy"` for webhook deliveries.
  - When signing is enabled in the environment:
    - Each receipt's signature verifies successfully using the platform's standard receipt verification tooling.
  - Receipts are present in the append-only JSONL store (no alternative formats).

---

## 11. Definition of Ready (DoR) Checklist — API Gateway & Webhooks

This module is ready for implementation when:

1. **OpenAPI specs** for:
   - Gateway public routes.
   - Webhook subscription management APIs.
   - Webhook receiver endpoints.
   are generated from this PRD and reviewed.

2. **Policy artifacts** exist for:
   - Route registry and auth scopes.
   - Tenant rate limits and webhook retry parameters.
   - Gateway size/time limits, security filters, and performance SLAs.

3. **Receipts schema integration** is confirmed:
   - All receipts conform to the global DecisionReceipt JSON Schema (`gsmd/schema/receipt.schema.json`).
   - Receipts use correct `gate_id` values: `"api-gateway-auth"`, `"api-gateway-rate-limit"`, `"api-gateway-routing"`, `"api-gateway-waf"`, `"webhook-producer"`, `"webhook-receiver"`.
   - Receipts include required `evaluation_point` values: `"pre-deploy"` for gateway decisions, `"post-deploy"` for webhook deliveries.
   - Receipts use `inputs` for request/event data, `result` for decision outcomes, and `decision.rationale` for reason codes.
   - The Receipts subsystem is configured and accessible from this module.

4. **Test harness** scaffolding:
   - Integration test environment for gateway + stubbed backends.
   - Webhook consumer stub to validate outbound delivery and signatures.
   - Inbound webhook generator for duplicates and invalid signatures.
   - Policy fixtures (GSMD bundles) for test tenants (see §10.3 for fixture structure), so that all limits and retries are policy-driven.

5. **Security review** confirms:
   - Alignment with OWASP API Security Top 10 for this module.
   - No hard-coded thresholds or secrets.
   - No local policy engine in this module.

Once these conditions are satisfied and the test cases in §10.2 are automated and passing, this PRD is **fully aligned** with the rest of the ZeroUI project and is **ready for implementation** without requiring the team to invent behaviour.

---

## 12. Evidence Handles Pattern

Evidence handles are optional arrays of evidence references included in receipts for security and audit purposes.

### 12.1 When to Use Evidence Handles

Evidence handles should be included in receipts for:
- **WAF blocks**: References to WAF log entries, blocked request details
- **Signature failures**: References to signature verification logs, failed signature details
- **Security violations**: References to security audit logs, violation details
- **Delivery failures**: References to webhook delivery logs, error responses (for webhook producer receipts)

### 12.2 Evidence Handle Structure

```typescript
interface EvidenceHandle {
  url: string;              // URL or path to evidence
  type: string;             // Evidence type (e.g., "waf_log", "signature_verification", "delivery_log")
  description: string;      // Human-readable description
  expires_at?: string;      // Optional expiration (ISO 8601)
}
```

### 12.3 Example Evidence Handles

**WAF Block Receipt:**
```json
{
  "evidence_handles": [
    {
      "url": "waf://logs/2025/01/15/block_abc123",
      "type": "waf_log",
      "description": "WAF block log entry for SQL injection attempt",
      "expires_at": "2026-01-15T00:00:00Z"
    }
  ]
}
```

**Webhook Delivery Failure Receipt:**
```json
{
  "evidence_handles": [
    {
      "url": "webhook://deliveries/event_xyz789/attempt_3",
      "type": "delivery_log",
      "description": "Webhook delivery attempt log with error response",
      "expires_at": "2026-01-15T00:00:00Z"
    }
  ]
}
```
