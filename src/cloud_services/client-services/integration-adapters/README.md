# Integration Adapters Module (M10)

**Module ID**: M10 (PM-5)  
**Service Category**: Client Services  
**Version**: 2.0.0

## Overview

The Integration Adapters Module provides a unified, hardened adapter layer for external system integrations (GitHub, GitLab, Jira, Slack, etc.) with webhook ingestion, polling, outbound actions, and SignalEnvelope normalization.

## Architecture

The module implements a ports-and-adapters (anti-corruption layer) architecture:

- **Base Adapter Interface**: Unified contract for all provider adapters
- **Provider Adapters**: Provider-specific implementations (GitHub, GitLab, Jira, etc.)
- **SignalEnvelope Mapping**: Transforms provider events to canonical PM-3 format
- **Integration Services**: Orchestrates webhooks, polling, and outbound actions
- **External Service Clients**: Integrates with PM-3, M33 (KMS), M35 (Budgeting), ERIS, IAM

## Features

- **Webhook Ingestion**: Signature verification, replay protection, event normalization
- **Polling Support**: Cursor-based polling for providers without webhooks
- **Outbound Actions**: Idempotent action execution with retries and circuit breaking
- **Tenant Isolation**: Strong multi-tenant isolation enforced at all layers
- **Observability**: Metrics, logging, and tracing per FR-12
- **Security**: IAM authentication, KMS secret management, audit logging

## API Endpoints

### Management APIs (Tenant-Facing)

- `POST /v1/integrations/connections` - Create connection
- `GET /v1/integrations/connections` - List connections
- `POST /v1/integrations/connections/{id}/verify` - Verify connection
- `PATCH /v1/integrations/connections/{id}` - Update connection

### Webhook Endpoint

- `POST /v1/integrations/webhooks/{provider_id}/{connection_token}` - Receive webhooks

### Internal APIs

- `POST /internal/integrations/events/normalised` - Accept SignalEnvelope
- `POST /internal/integrations/actions/execute` - Execute NormalisedAction
- `GET /internal/integrations/connections/{id}/health` - Health check

## Configuration

Environment variables:

- `INTEGRATION_ADAPTERS_DATABASE_URL` - Database connection URL
- `PM3_SERVICE_URL` - PM-3 Signal Ingestion service URL
- `KMS_SERVICE_URL` - Key Management Service URL
- `BUDGET_SERVICE_URL` - Budgeting & Rate-Limiting service URL
- `ERIS_SERVICE_URL` - ERIS service URL
- `IAM_SERVICE_URL` - IAM service URL

## Testing

Run all tests:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ -v --cov=. --cov-report=html --cov-fail-under=100
```

Test categories:

- **Unit Tests**: `tests/unit/` - Component-level tests
- **Integration Tests**: `tests/integration/` - End-to-end flow tests
- **Performance Tests**: `tests/performance/` - Latency and throughput tests
- **Security Tests**: `tests/security/` - Security and isolation tests
- **Resilience Tests**: `tests/resilience/` - Fault injection tests

## Implementation Status

✅ Core infrastructure (database models, repositories)  
✅ Pydantic models and domain logic  
✅ Adapter SPI and base infrastructure  
✅ GitHub adapter (webhook, actions)  
✅ Core services (integration service)  
✅ External service integrations (PM-3, KMS, Budget, ERIS, IAM)  
✅ API routes and FastAPI app  
✅ Observability (metrics, tracing, audit logging)  
✅ Circuit breaker and reliability  
✅ Comprehensive test suite (unit, integration, performance, security, resilience)

## References

- **PRD**: `docs/architecture/modules/Integration_Adapters_Module_Patched.md`
- **Validation Report**: `docs/architecture/modules/Integration_Adapters_Module_FINAL_VALIDATION_REPORT.md`
- **Implementation Guide**: `docs/architecture/MODULE_IMPLEMENTATION_GUIDE.md`

