M10 – Integration Adapters Module (PRD)

**Module ID**: M10 (also known as PM-5 in some documentation)  
**Service Category**: Client Services (company-owned, private data)  
**Implementation Location**: `src/cloud_services/client-services/integration-adapters/`  
**Validation Status**: ✅ **VALIDATED & APPROVED FOR IMPLEMENTATION** (see Section 15.2 and Document Version & Change History for validation details)

1. Summary & Intent

Module: M10 – Integration Adapters (PM-5)
Type: Platform Module
Service Category: Client Services
Planes:

CCP-1 Identity & Trust Plane

CCP-2 Policy & Configuration Plane

CCP-3 Evidence & Audit Plane

CCP-4 Observability & Reliability Plane

CCP-5 Security & Supply Chain Plane

CCP-6 Data & Memory Plane

Intent:
The Integration Adapters module provides a standard, hardened way for ZeroUI to talk to external systems (e.g., source control, CI/CD, issue trackers, chat, observability, knowledge tools) without leaking vendor-specific complexity into the rest of the platform.

It exposes:

A unified adapter contract for all external tools (ports-and-adapters / anti-corruption layer)

A managed lifecycle for connections (auth, webhooks, polling, health, rotation)

Safe, idempotent, observable HTTP/API interactions with external systems (retries, rate limiting, error handling)

All other modules (Signal Ingestion, Detection, MMM, UBI, Alerting, etc.) consume normalised events and actions from M10 and never call third-party APIs directly.



2. Problem Statement

Without a central Integration Adapters module:

Every feature team would implement ad-hoc connectors to GitHub, GitLab, Jira, Slack, CI tools, etc. → duplicated effort, inconsistent error handling, and inconsistent security.

Each integration would decide on its own auth scheme, retries, rate limiting, and logging, risking security gaps and rate-limit bans.

There would be no unified telemetry for integration failures, making incidents hard to diagnose.

External schemas would leak into core modules (e.g., raw GitHub/Slack payloads), increasing coupling and breaking the clean ports-and-adapters architecture.

We need a single Integration Adapters layer that centralises:

Contracts and mapping to canonical schemas

Auth and secret handling (via IAM + KMS modules)

Retry, idempotency, and rate-limiting strategies

Webhook vs polling decisions and infrastructure



3. Goals & Non-Goals

3.1 Goals

Single Integration Fabric:
A unified, tenant-aware integration layer for external tools (SCM, CI/CD, issue tracking, chat, observability, knowledge systems).

Safe, Idempotent API Calls:
All outbound calls implement idempotent patterns where possible (idempotency keys, de-duplication, safe retries).

Event-Driven First, Polling When Needed:
Prefer webhooks for event-driven, near real-time updates; use polling where webhooks are not available or would overload systems.

Security & Privacy by Design:
Auth via standard protocols (OAuth 2.0, API keys where unavoidable) with least privilege scopes; secrets managed by M33 (Key & Trust Management, also known as EPC-11), not by adapters.

Multi-Tenant Isolation & Budgeting:
All integrations are tenant-scoped and subject to budgeting and rate limits defined in M35 (Budgeting, Rate-Limiting & Cost Observability, also known as EPC-13), with strong isolation across tenants.

Developer-Friendly Adapter SDK:
Clear internal SPI + helper libraries so new adapters can be implemented safely by internal teams without re-solving infra concerns.

3.2 Non-Goals

Not a generic iPaaS for arbitrary customer-defined workflows (we support a defined set of integration families).

Not a UI-based integration marketplace (no end-user dashboards; configuration flows are APIs or orchestration driven).

Not an ETL/warehouse sync platform (bulk data sync is out of scope; we handle operational signals and actions only).



4. Scope

4.1 In Scope

Adapter abstraction & registry for external providers (e.g., GitHub, GitLab, Bitbucket, Azure DevOps, Jira, Linear, Slack, MS Teams, email gateways, CI/CD, observability).

Connection lifecycle: create, verify, rotate, disable, delete.

Inbound events:

Webhooks (preferred where supported).

Polling/backfill for providers without webhooks, or as safety net.

Outbound actions:

Creating/updating issues/tickets/comments.

Posting messages to chat.

Attaching links, comments, or annotations to PRs/builds.

Normalisation of provider-specific payloads into canonical SignalEnvelope schemas (per PM-3 / M04 Signal Ingestion & Normalization) consumed by PM-3 and other modules.

Cross-cutting concerns: auth, retries, rate limiting, idempotency, observability, tenant isolation, receipts.

4.2 Out of Scope

Designing every provider's full schema (handled per-provider specs under M34 – Contracts & Schema Registry, also known as EPC-12).

Managing human UX for configuration (we provide backend/API hooks; any optional admin UI sits in Tenant/Product Admin modules).

Bulk historical migrations or BI/analytics ETL.



5. Personas

Platform Integrations Engineer – defines/implements adapters, ensures correctness and performance.

Tenant Admin / DevOps Lead – configures connections between ZeroUI and their internal/external tools.

Feature Module Owners (Detection, MMM, UBI, Alerting, Release Failures, etc.) – rely on M10 for events and actions; never call third-party APIs directly.

Security & Compliance Lead – cares about auth scopes, secret storage, audit trails, and DPIA/compliance evidence.



6. Key Concepts & Definitions

Integration Provider – logical type of integration (e.g., github, gitlab, jira, slack).

Integration Connection – a tenant-specific configuration that authorises ZeroUI to act with a given provider (e.g., Tenant A’s GitHub org).

Adapter – code implementing the provider-specific logic behind a standard adapter interface. Conceptually aligned with the Adapter pattern: bridging incompatible external APIs to a stable internal contract.

Webhook Endpoint – inbound HTTP endpoint receiving provider events.

Poller – background job fetching updates from provider APIs.

SignalEnvelope – canonical event format from PM-3 (M04 Signal Ingestion & Normalization). Adapters transform provider-specific events into SignalEnvelope format for ingestion into PM-3. See Section 10.1 for mapping details.

Normalised Action – canonical "action description" (e.g., "create comment on PR") that adapters translate into provider API calls.

Idempotency Key – token for deduplicating event processing and outbound requests to support safe retries.



7. High-Level Architecture & Data Flow

7.1 Components

Integration Registry Service (IRS)

Stores providers, connection metadata, status, capabilities.

Adapter Runtime

Multi-tenant worker runtime that runs provider-specific adapter logic behind a stable internal interface.

Inbound Gateway

HTTP entrypoints for webhooks; validates signatures, normalises payloads, transforms to SignalEnvelope format, pushes into PM-3.

Polling/Scheduler

Drives adapters that require periodic polling or backfills.

Outbound Action Dispatcher

Accepts normalised actions from MMM/Detection/etc. and routes them to the correct adapter/connection.

Observability & Receipts Hooks

Exports metrics/logs/traces and writes ERIS receipts for integration actions/failures.

7.2 Data Flow (Examples)

Inbound via Webhook

External system invokes ZeroUI webhook URL with signed payload.

Inbound Gateway validates signature, maps to tenant + connection, and passes to Adapter Runtime.

Adapter parses payload, maps to SignalEnvelope (canonical schema per PM-3).

SignalEnvelope is pushed to PM-3 Signal Ingestion; PM-3 emits down-stream events for Detection, MMM, UBI, etc.

Inbound via Polling

Scheduler triggers adapter poll job for a connection (respecting rate/budget limits).

Adapter queries provider API with pagination; deduplicates new events using cursor + idempotency keys.

Each new item is mapped to SignalEnvelope and sent to PM-3.

Outbound Action

MMM or another module emits a Normalised Action (e.g., “post Mentor message to Slack channel X for repo Y”).

Outbound Action Dispatcher looks up the appropriate Integration Connection and routes to adapter.

Adapter translates into provider-specific API requests, applies retries/backoff and idempotency keys.

Outcome (success/failure) is logged, metrics incremented, ERIS receipt written, and optional evidence returned to caller.



8. Functional Requirements (FR)

FR-1: Provider & Adapter Registry

The system MUST maintain a registry of supported providers with:

provider_id (e.g., github, jira),

category (SCM, issue_tracker, chat, ci_cd, observability, knowledge),

capabilities (webhook_supported, polling_supported, outbound_actions_supported),

version and status (alpha/beta/GA/deprecated).

The registry MUST be queryable by other modules (e.g., to show which provider families are available for a tenant).

FR-2: Integration Connections (Tenant Scoped)

For each provider, tenants MUST be able to create IntegrationConnection objects with:

tenant_id, provider_id,

connection name/description,

auth config reference (stored via KMS/Key & Trust; not raw secret),

status (pending_verification, active, suspended, error, deleted),

capabilities enabled (webhook, polling, outbound actions),

metadata tags (e.g., default repo organisation).

Creating/activating a connection MUST require a verification step (e.g., test API call or webhook verification depending on provider).

FR-3: Authentication & Authorization

Adapters MUST support secure auth mechanisms per provider, preferring OAuth 2.0 where supported, or scoped API tokens where not.

Auth secrets MUST never be stored in adapter code or configs; they must be retrieved at runtime from M33 (Key & Trust Management, also known as EPC-11) using a reference (KID/secret_id).

The module MUST support token refresh/rotation and surface failures (e.g., expired tokens) via metrics and ERIS receipts.

FR-4: Webhook Ingestion

For providers that support webhooks:

The system MUST provide per-connection webhook endpoints with:

signature verification (HMAC or provider-specific scheme),

replay protection (timestamps + nonce/signature cache),

rate limiting per tenant/connection.

Valid events MUST be mapped to SignalEnvelope format (per PM-3 schema) and forwarded to PM-3.

Invalid or unverifiable webhook calls MUST be rejected with appropriate HTTP status and logged.

FR-5: Polling & Backfill

When webhooks are not available or not suitable (e.g., extremely high-frequency sources), adapters MUST support polling with:

configured intervals per provider/connection,

pagination handling,

cursors/checkpoints to avoid re-reading entire history,

integration with M35 (Budgeting, Rate-Limiting & Cost Observability, also known as EPC-13) for rate/budget limits.

Polling jobs MUST implement idempotency to avoid double-processing events when retries occur.

FR-6: Event Normalisation

All provider-specific payloads MUST be transformed into SignalEnvelope format (canonical schema from PM-3 / M04 Signal Ingestion & Normalization). SignalEnvelope schemas are managed under M34 (Contracts & Schema Registry, also known as EPC-12).

SignalEnvelope MUST include all required fields per PM-3 specification:
- signal_id (globally unique)
- tenant_id
- environment (dev/stage/prod)
- producer_id (set to connection_id for adapter events)
- signal_kind (event, metric, log, trace)
- signal_type (canonical event type, e.g., "pr_opened", "issue_created", "chat_message")
- occurred_at (when event occurred in provider system)
- ingested_at (when adapter received/processed event)
- payload (structured event data)
- schema_version

Additional fields for adapter context:
- payload.provider_metadata.provider_id (provider identifier, e.g., "github", "jira")
- payload.provider_metadata.connection_id (integration connection identifier)
- payload.canonical_keys (issue_key, channel_id, etc. as applicable)
- resource.repository (repository context, e.g., "org/repo")
- resource.branch (branch context)
- resource.pr_id (pull request ID when applicable)
- correlation_id (link to original provider event ID)

Optional raw_payload_ref pointing to a redacted raw store if allowed by Data Governance & Privacy (M22).

FR-7: Outbound Actions

The module MUST accept canonical Normalised Actions describing intent (e.g., create_issue, comment_on_pr, post_chat_message) with provider-agnostic fields.

Adapter-specific logic MUST:

map canonical action → provider calls,

apply idempotency keys where appropriate (e.g., avoid duplicate comments)

handle pagination/multi-step operations as needed.

Outcome (success/failure) MUST be returned along with provider reference (URL/id) and logged for observability + receipts.

FR-8: Error Handling, Retries & Circuit Breaking

Outbound calls MUST:

classify errors (client vs server vs network),

implement exponential backoff with jitter,

avoid retrying clearly invalid requests (4xx except 429/408).

On repeated failures or 429 (rate-limit) responses, adapters MUST:

respect provider rate-limit guidance,

open a per-connection circuit breaker,

push incidents to EPC-4 (Alerting) or EPC-5 (Health & Reliability) as configured.

FR-9: Rate Limiting & Budgeting Integration

All outbound calls and polling jobs MUST integrate with M35 (Budgeting, Rate-Limiting & Cost Observability, also known as EPC-13):

budgets per tenant/provider/connection,

enforcement of limits with error reporting,

metrics for budget exhaustion.

FR-10: Tenant Isolation & Multi-Tenancy

IntegrationConnection MUST be scoped by tenant_id; no cross-tenant connections.

Webhook endpoints MUST map to specific tenant connections; events for one tenant MUST never leak into another tenant’s pipelines.

Logging and metrics MUST be tagged with tenant to support isolated views.

FR-11: Versioning & Compatibility

Providers MUST declare supported API versions and adapter version.

When provider APIs change:

adapters MUST support side-by-side operation (old & new) during migration,

changes MUST be reflected in schemas under EPC-12 and captured via ERIS receipts for audit.

FR-12: Observability & Diagnostics

Integration Adapters MUST emit:

metrics: request counts, error rates, latencies, webhooks received, events normalised, actions executed, circuit opens, token refreshes.

structured logs: correlation IDs, tenant, provider, connection, error categories (redacted for secrets/PII).

traces: spans around HTTP calls, serialisation, normalisation.

These MUST feed the CCP-4 Observability & Reliability Plane and EPC-5 – Health & Reliability Monitoring (and, where configured, surface incidents into EPC-4 – Alerting & Notification Service).

See Section 15.1 for implementation structure details.

FR-13: Evidence & Receipts

For sensitive operations (e.g., creating issues, posting MMM messages, configuring connections), adapters MUST emit ERIS receipts with:

tenant_id, connection_id, provider_id,

operation type (e.g., integration.action.github.create_comment),

request metadata (redacted),

result (success/failure, status codes),

correlation IDs (link back to original MMM/Detection/UBI DecisionReceipt).

FR-14: Integration Adapter SDK / SPI

The module MUST provide an internal SDK/SPI for writing adapters that includes:

common HTTP client with retries/backoff, idempotency helpers, and rate-limit awareness,

logging & metrics helpers,

canonical schema helpers,

test harness utilities (mock servers, fixtures).

New adapters MUST be registered with IRS and pass module test suites before being enabled.

FR-15: Security & Privacy Constraints

All network communication MUST use TLS.

Secrets MUST be managed by M33 (Key & Trust Management, also known as EPC-11) only.

Payloads MUST be redacted as per DG&P rules before logging or storing raw payload references.



9. Non-Functional Requirements (NFR)

NFR-1 – Latency:

Per outbound action: p95 ≤ 1s for provider API call (excluding provider latency spikes).

Webhook handling: p95 ≤ 250 ms to ack provider (processing can continue async).

NFR-2 – Throughput & Scale:

Support at least a baseline (to be set by infra PRD) of:

X events/s per tenant per provider family,

Y simultaneous connections per provider.

NFR-3 – Resilience:

No single provider failure should take down core services; adapters degrade gracefully and emit incidents.

NFR-4 – Security:

Compliance with platform-wide auth, secrets, and audit standards; least-privilege provider scopes only.

NFR-5 – Observability:

All critical paths instrumented with metrics/traces; errors are classifiable by type (auth, network, provider, config).

NFR-6 – Testability:

Adapters must be unit-testable with mocked providers; integration tests must run against mock servers or sandbox APIs.



10. Conceptual Data Model (Logical)

10.1 Event Mapping to SignalEnvelope

Provider-specific events MUST be transformed into SignalEnvelope format (per PM-3 / M04 specification). Mapping rules:

- **provider_id** → stored in `payload.provider_metadata.provider_id` (e.g., "github", "jira", "slack")
- **connection_id** → stored in `producer_id` field (adapter acts as producer for PM-3)
- **provider event type** → mapped to canonical `signal_type` (e.g., "github.pull_request.opened" → "pr_opened")
- **provider event timestamp** → `occurred_at`
- **adapter processing time** → `ingested_at`
- **provider event payload** → transformed into `payload` with canonical field names
- **provider event ID** → stored in `correlation_id` or `payload.provider_event_id`
- **canonical entity IDs** (repo_id, branch, issue_key) → stored in:
  - `resource.repository` (for repo context, e.g., "org/repo")
  - `resource.branch` (for branch context)
  - `resource.pr_id` (for pull request ID)
  - `payload.canonical_keys` (for other entity IDs like issue_key, channel_id, etc.)

Example mapping:
- GitHub PR opened event → SignalEnvelope with `signal_type="pr_opened"`, `resource.repository` set, `payload.pr_number`, `payload.title`, etc.
- Jira issue created → SignalEnvelope with `signal_type="issue_created"`, `payload.issue_key`, `payload.summary`, etc.

10.2 Logical Data Model

IntegrationProvider

provider_id (PK)

category (enum)

name

status (alpha/beta/GA/deprecated)

capabilities (flags: webhook, polling, outbound_actions)

api_version (string)

IntegrationConnection

connection_id (PK)

tenant_id

provider_id

display_name

auth_ref (ref into KMS)

status

enabled_capabilities

created_at, updated_at, last_verified_at

WebhookRegistration

registration_id

connection_id

public_url

secret_ref (signing secret)

events_subscribed

status

PollingCursor

cursor_id

connection_id

cursor_position (e.g., last event id/timestamp)

last_polled_at

AdapterEvent (raw)

event_id

connection_id

provider_event_type

received_at

raw_payload_ref

SignalEnvelope (per PM-3 / M04 specification)

See Section 10.1 for mapping from provider events to SignalEnvelope. The SignalEnvelope structure is defined by PM-3 and includes:
- signal_id, tenant_id, environment, producer_id, signal_kind, signal_type
- occurred_at, ingested_at
- trace_id, span_id, correlation_id
- resource (with repository, branch, pr_id, etc. - see Resource model in PM-3)
- payload (structured event data with provider_metadata and canonical_keys)
- schema_version, sequence_no

AdapterEvent (raw, for internal tracking)

event_id

connection_id

provider_event_type

received_at

raw_payload_ref (reference to redacted raw payload if stored)

NormalisedAction

action_id

tenant_id

provider_id

connection_id

canonical_type (e.g., post_chat_message)

target (channel, issue_key, pr_id)

payload (structured)

idempotency_key (required for safe retries)

correlation_id (link back to MMM/Detection/UBI DecisionReceipt)

created_at



11. APIs & Integration Contracts (Logical)

All schemas are to be materialised under M34 (Contracts & Schema Registry, also known as EPC-12).

**OpenAPI Specification**: See `contracts/integration_adaptors/openapi/openapi_integration_adaptors.yaml` for complete API specification.

**Error Response Schema**: All error responses follow standard format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "timestamp": "ISO8601"
  }
}
```

**Authentication**: All endpoints require IAM token validation via M21 (Identity & Access Management, also known as EPC-1).

11.1 Management APIs (Tenant-Facing / Admin-Facing)

POST /v1/integrations/connections

Create a new IntegrationConnection (tenant scoped).

GET /v1/integrations/connections

List connections for tenant.

POST /v1/integrations/connections/{id}/verify

Trigger verification (test API or webhook handshake).

PATCH /v1/integrations/connections/{id}

Update status, capabilities, metadata.

11.2 Webhook Endpoint

POST /v1/integrations/webhooks/{provider_id}/{connection_token}

Receives provider webhooks, verifies signature, and pushes into adapter pipeline.

11.3 Internal Event & Action APIs

POST /internal/integrations/events/normalised

Accepts SignalEnvelope events from adapters (for forwarding to PM-3).

POST /internal/integrations/actions/execute

Accepts NormalisedActions and routes them to providers.

11.4 Health & Diagnostics

GET /internal/integrations/connections/{id}/health

Returns last successful call, error counts, rate-limit state.



12. Interactions with Other Modules

**Module Code Mappings**:
- PM-3 → M04 (Signal Ingestion & Normalization)
- PM-4 → M05 (Detection Engine Core)
- M01 (MMM Engine)
- EPC-9 (User Behaviour Intelligence / UBI)
- EPC-11 → M33 (Key & Trust Management)
- EPC-13 → M35 (Budgeting, Rate-Limiting & Cost Observability)
- EPC-3 → M23 (Configuration & Policy Management)
- EPC-4 (Alerting & Notification Service)
- EPC-5 (Health & Reliability Monitoring)
- EPC-12 → M34 (Contracts & Schema Registry)

**M04 (PM-3) – Signal Ingestion & Normalization**:

Receives SignalEnvelope events from adapters as canonical inputs. Adapters transform provider events into SignalEnvelope format per PM-3 specification.

**M05 (PM-4) – Detection Engine Core**:

Consumes signals triggered by external events (PRs, tickets, messages) via PM-3; generates NormalisedActions to be executed by adapters.

**M01 – MMM Engine**:

Consumes signals from PM-3; generates NormalisedActions (e.g., post Mentor messages) to be executed by adapters.

**EPC-9 – User Behaviour Intelligence (UBI)**:

Consumes signals from PM-3; may generate actions via MMM or Detection Engine.

**M33 (EPC-11) – Key & Trust Management**:

Provides secret material for auth (tokens, signing secrets). Adapters retrieve secrets at runtime using KID/secret_id references.

**M35 (EPC-13) – Budgeting, Rate-Limiting & Cost Observability**:

Enforces budgets and rate limits on adapter calls. Adapters check budgets before making outbound API calls and respect rate limits.

**EPC-4 – Alerting & Notification Service**:

Receives incidents when integrations degrade or fail. Adapters push incidents for circuit breaker opens, repeated failures, rate limit exhaustion.

**EPC-5 – Health & Reliability Monitoring**:

Receives health metrics and incidents from adapters. Adapters report connection health, error rates, latency metrics.

**M23 (EPC-3) – Configuration & Policy Management**:

Stores adapter-level configs (polling intervals, retry policies, allowed providers). Adapters read configuration at runtime.



13. Test Strategy & Representative Test Cases

13.1 Categories

Unit Tests (UT-IA-xx) – adapter mapping, normalisation, error classification, retry decisions.

Integration Tests (IT-IA-xx) – interactions with mock provider servers and internal modules (PM-3/M04, M33/EPC-11, M35/EPC-13).

Performance Tests (PT-IA-xx) – throughput and latency under load.

Security Tests (SEC-IA-xx) – auth, secrets, injection, tenant isolation.

Resilience/Fault Injection Tests (RF-IA-xx) – provider outages, timeouts, 429 storms, malformed payloads.

13.2 Representative Tests (Non-Exhaustive)

UT-IA-01 – Webhook Signature Verification

Given: inbound webhook with correct signature and timestamp

When: request hits /v1/integrations/webhooks/...

Then: signature is validated, mapped to a connection, and payload is passed to adapter.

UT-IA-02 – Webhook Replay Protection

Given: same webhook id/timestamp delivered twice

Then: second attempt is recognised as duplicate and ignored (idempotent behaviour).

UT-IA-03 – Normalisation for SCM Event

Given: provider-specific PR event payload

Then: adapter produces a SignalEnvelope with canonical PR keys and expected fields (signal_type="pr_opened", resource.repository set, etc.).

UT-IA-04 – Outbound Action Idempotency

Given: NormalisedAction with idempotency key

When: transient HTTP errors trigger retries

Then: provider receives only one logical action (e.g., single comment), and internal state reflects single success.

IT-IA-01 – OAuth Connection Verification

Simulate OAuth 2.0 flow using mock auth server and provider.

After creating connection and verifying, connection status becomes active.

IT-IA-02 – Webhook → PM-3 Pipeline

Simulated provider webhook → Inbound Gateway → Adapter → SignalEnvelope → PM-3.

Assert that PM-3 receives SignalEnvelope with correct tenant/provider/connection mapping (tenant_id, producer_id=connection_id, payload.provider_metadata.provider_id, etc.).

IT-IA-03 – Outbound Mentor Message to Chat

MMM emits post_chat_message action.

Adapter posts to mock chat server.

Assert chat server receives message; ERIS receipt logged with correct correlation ids.

PT-IA-01 – High Webhook Volume

Pump events at target RPS into webhook endpoints.

Verify p95 latency and drop/error rates meet NFR-1 & NFR-2.

SEC-IA-01 – Secret Leakage

Ensure logs never contain access tokens or raw secrets (scan logs for token patterns).

SEC-IA-02 – Tenant Isolation

Simulate webhooks and actions for tenants A & B.

Confirm no cross-tenant visibility or processing.

RF-IA-01 – Provider Outage

Mock provider returns 5xx for sustained period.

Verify retries/backoff happen; circuit breaker trips; EPC-4/EPC-5 receive incident; no unbounded retries.

RF-IA-02 – Rate Limit Storm (429)

Mock provider returns consecutive 429 with Retry-After.

Confirm backoff obeys Retry-After and budgets; metrics reflect rate-limit events; incident generated.



14. Risks & Mitigations

R-1 Provider API Drift

Risk: API or webhook formats change breaking adapters.

Mitigation: registry + versioning; schemas in M34 (EPC-12); contract tests against provider sandboxes.

R-2 Hidden Costs & Rate Limits

Risk: aggressive polling/requests exceed provider limits and pricing.

Mitigation: budgets in M35 (EPC-13); dynamic polling intervals; monitoring of rate-limit errors.

R-3 Security Misconfigurations

Risk: over-privileged scopes or leaked tokens.

Mitigation: least-privilege tokens, secret store only, regular token rotation tests, security scanning for secrets.

R-4 Data Privacy & PII Leakage

Risk: raw payloads may contain PII.

Mitigation: DG&P-driven redaction; minimal raw storage; careful logging.

R-5 Vendor Lock-In

Risk: core logic depending too tightly on a particular vendor’s semantics.

Mitigation: strict normalisation and canonical schemas; adapter pattern boundary.



15. Implementation Notes & Phasing (High-Level)

Phase 1 – Core Abstractions & Registry

Implement IntegrationProvider + IntegrationConnection models and registry APIs.

Implement Adapter SPI and common HTTP client with retries/backoff and metrics.

Phase 2 – Webhook Ingress & Normalisation

Build Inbound Gateway + signature verification + basic adapters for 1–2 SCM providers.

Integrate with PM-3 for SignalEnvelope events. Transform provider events to SignalEnvelope format per PM-3 specification.

Phase 3 – Outbound Actions & Receipts

Implement NormalisedAction execution pipeline.

Integrate ERIS receipts for actions.

Phase 4 – Polling & Backfill

Implement scheduler, PollingCursor, and at least one polled adapter (e.g., issue tracker without webhooks).

Phase 5 – Rate Limits, Budgets & Advanced Observability

Wire into M35 (EPC-13 budgets) and EPC-4/EPC-5 for detailed metrics and health.

Phase 6 – Adapter SDK & New Providers

Stabilise SDK and onboard additional provider families (chat, CI/CD, observability, knowledge).

15.1 Implementation Structure

The module SHALL be implemented following the standard ZeroUI module structure:

**Service Location**: `src/cloud_services/client-services/integration-adapters/`

**Standard File Structure**:
```
integration-adapters/
├── __init__.py
├── main.py                 # FastAPI app entrypoint
├── routes.py               # API routes (HTTP concerns only)
├── services.py             # Business logic (ALL logic here)
├── models.py               # Pydantic domain models
├── dependencies.py         # Mock clients for shared services
├── service_registry.py     # Service registry for DI
├── middleware.py           # Optional: Custom middleware
├── config.py               # Configuration management
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy ORM models
│   ├── repositories.py     # Repository pattern
│   ├── connection.py       # DB session management
│   └── migrations/         # Alembic migrations
├── adapters/               # Provider-specific adapter implementations
│   ├── __init__.py
│   ├── base.py            # Base adapter interface/SPI
│   ├── github/            # GitHub adapter
│   ├── gitlab/            # GitLab adapter
│   ├── jira/              # Jira adapter
│   └── [other providers]
├── integrations/          # External service clients
│   ├── pm3_client.py     # PM-3 Signal Ingestion client
│   ├── iam_client.py     # M21 IAM client
│   ├── kms_client.py     # M33 KMS client
│   ├── budget_client.py  # M35 Budgeting client
│   └── eris_client.py    # ERIS receipt client
├── observability/
│   ├── metrics.py         # Prometheus metrics
│   ├── tracing.py         # OpenTelemetry tracing
│   └── audit.py           # Audit logging
├── reliability/
│   └── circuit_breaker.py # Circuit breaker patterns
└── requirements.txt       # Python dependencies
```

**Database Schema** (SQLAlchemy ORM models):

All tables MUST include:
- UUID primary keys (using GUID type decorator for PostgreSQL/SQLite compatibility)
- tenant_id (indexed, required for all tenant-scoped tables)
- created_at, updated_at (timestamps with timezone)
- JSONB (PostgreSQL) or JSON (SQLite) for flexible metadata

**Key Tables**:
- `integration_providers` - Provider registry
- `integration_connections` - Tenant-scoped connections (indexed on tenant_id, provider_id)
- `webhook_registrations` - Webhook endpoint registrations
- `polling_cursors` - Polling state per connection
- `adapter_events` - Raw event tracking (optional, for audit)
- `normalised_actions` - Outbound action queue

**Reference**: See `docs/architecture/MODULE_IMPLEMENTATION_GUIDE.md` for detailed implementation patterns.

15.2 Implementation Readiness & Next Steps

The module has been validated and is ready for implementation. See `Integration_Adapters_Module_FINAL_VALIDATION_REPORT.md` for complete validation details.

**Implementation Confidence**: **HIGH**

**Rationale**:
- ✅ All critical validation issues resolved
- ✅ All high-priority issues resolved
- ✅ Architecture alignment verified
- ✅ Module integration verified
- ✅ Data model alignment verified
- ✅ Implementation patterns defined
- ✅ No blocking issues identified

**Recommended Implementation Sequence**:

1. **Create Service Directory**: `src/cloud_services/client-services/integration-adapters/`
2. **Implement Core Structure**: Follow Section 15.1 file structure
3. **Implement Database Models**: Per Section 15.1 database schema (UUID primary keys, tenant_id indexed, timestamps, JSONB/JSON)
4. **Implement Adapter SPI**: Base adapter interface per FR-14 (Section 8)
5. **Implement SignalEnvelope Mapping**: Per Section 10.1 mapping rules (use `payload.provider_metadata` and existing Resource fields)
6. **Integrate with PM-3 (M04)**: Use PM-3 client to forward SignalEnvelope events
7. **Integrate with M33 (KMS)**: Retrieve secrets at runtime using KID/secret_id references
8. **Integrate with M35 (Budgeting)**: Check budgets before API calls, respect rate limits
9. **Implement Observability**: Metrics, logging, tracing per FR-12 (Section 8)
10. **Implement Tests**: Per Section 13 test strategy (unit, integration, performance, security, resilience)

**Key Implementation Notes**:
- SignalEnvelope mapping MUST use `payload.provider_metadata.provider_id` (not `resource.metadata` which does not exist)
- Connection ID maps to `producer_id` field (adapter acts as producer for PM-3)
- Canonical entity IDs use existing Resource fields (`resource.repository`, `resource.branch`, `resource.pr_id`) or `payload.canonical_keys`
- All database tables MUST include UUID primary keys, tenant_id (indexed), created_at, updated_at, and JSONB/JSON for metadata
- All API endpoints MUST use `/v1/` prefix and require IAM token validation via M21

---

## Document Version & Change History

**Version**: 2.0 (Post-Validation Update)  
**Last Updated**: 2025-01-XX  
**Status**: ✅ Ready for Implementation

### Changes from Previous Version

This PRD has been updated based on comprehensive triple validation (see `Integration_Adapters_Module_TRIPLE_VALIDATION_REPORT.md` and `Integration_Adapters_Module_FINAL_VALIDATION_REPORT.md`):

1. **Module ID Standardization**: Updated to use M10 as primary identifier (PM-5 retained as alternative reference)
2. **Data Model Alignment**: Replaced all "NormalisedEvent" references with "SignalEnvelope" (PM-3 canonical format)
3. **Module Code Mappings**: Added explicit mappings table (EPC-XX → MXX) in Section 12
4. **Service Category**: Explicitly specified as Client Services with implementation location
5. **SignalEnvelope Mapping**: Added Section 10.1 with detailed mapping rules from provider events to SignalEnvelope
6. **NormalisedAction Enhancement**: Added `idempotency_key` and `correlation_id` fields
7. **Module References**: Updated all EPC-11 references to include M33, EPC-13 to include M35
8. **Module Separation**: Clarified PM-4, MMM (M01), and UBI (EPC-9) as separate modules
9. **Implementation Structure**: Added Section 15.1 with standard file structure and database schema patterns
10. **API Contracts**: Added OpenAPI spec reference and error response schema
11. **Database Schema**: Added explicit database model section with table definitions
12. **Resource Model Usage**: Corrected to use `payload.provider_metadata` and existing Resource fields (repository, branch, pr_id) instead of non-existent `resource.metadata`
13. **Implementation Guidance**: Added Section 15.2 with implementation readiness confirmation, next steps, and key implementation notes

### Validation Status

✅ All critical issues from validation report addressed  
✅ All high-priority issues from validation report addressed  
✅ All medium-priority enhancements from validation report addressed  
✅ Final validation complete - all issues resolved (see `Integration_Adapters_Module_FINAL_VALIDATION_REPORT.md`)

**Validation Results**: 0 critical issues, 0 high-priority issues, 0 medium-priority issues, 0 low-priority issues

**This PRD is now the single source of truth for Integration Adapters Module (M10) implementation and is approved for immediate implementation.**

