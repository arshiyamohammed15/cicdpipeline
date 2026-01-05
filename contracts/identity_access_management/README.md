# Identity & Access Management contracts (identity_access_management)

This folder contains **OpenAPI**, **JSON Schemas**, and **example JSONs** for the module named **Identity & Access Management** (slug: `identity_access_management`, module ID: M21).

## Module Information

- **Module ID**: M21
- **Module Name**: Identity & Access Governance
- **Version**: 1.1.0
- **Description**: Authentication and authorization gatekeeper for ZeroUI ecosystem

## API Endpoints

- `/iam/v1/verify` - Verify identity/token (POST)
- `/iam/v1/decision` - Evaluate access decision or JIT elevation (POST)
- `/iam/v1/break-glass` - Trigger break-glass access (POST)
- `/iam/v1/policies` - Upsert policy bundle (PUT)
- `/iam/v1/health` - Health check (GET)
- `/iam/v1/metrics` - Metrics endpoint (GET)
- `/iam/v1/config` - Configuration endpoint (GET)

## Performance Requirements

- Authentication response: ≤200ms
- Policy evaluation: ≤50ms
- Access decision: ≤100ms
- Token validation: ≤10ms
- Max memory: 512MB

## Supported Events

- `authentication_attempt`
- `access_granted`
- `access_denied`
- `privilege_escalation`
- `role_change`
- `policy_violation`

## Contracts

- **OpenAPI**: `openapi/openapi_identity_access_management.yaml`
- **Schemas**: `schemas/*.schema.json`
- **Examples**: `examples/*.json`

## References

- IAM Module Specification: `docs/architecture/modules/IDENTITY_ACCESS_MANAGEMENT_IAM_MODULE_v1_1_0.md`
- IAM Triple Analysis: `docs/architecture/modules/IAM_MODULE_TRIPLE_ANALYSIS_v1_0.md`
