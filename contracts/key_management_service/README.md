# Key Management Service (KMS) Contracts

This directory contains the API contracts for the Key Management Service (KMS) Module M33.

## Structure

- `openapi/` - OpenAPI 3.0.3 specification
- `schemas/` - JSON schemas for data models
- `examples/` - Request/response examples

## API Endpoints

- `POST /kms/v1/keys` - Generate a new cryptographic key
- `POST /kms/v1/sign` - Create a digital signature
- `POST /kms/v1/verify` - Verify a digital signature
- `POST /kms/v1/encrypt` - Encrypt plaintext
- `POST /kms/v1/decrypt` - Decrypt ciphertext
- `GET /kms/v1/health` - Health check
- `GET /kms/v1/metrics` - Service metrics (Prometheus format)
- `GET /kms/v1/config` - Effective configuration

## Error Model

All non-2xx responses conform to the `ErrorResponse` schema with error codes:
- `INVALID_REQUEST` - Invalid input parameters
- `UNAUTHENTICATED` - Authentication failed
- `UNAUTHORIZED` - Authorization failed
- `KEY_NOT_FOUND` - Key not found
- `KEY_REVOKED` - Key has been revoked
- `KEY_INACTIVE` - Key is not active
- `POLICY_VIOLATION` - Policy violation
- `RATE_LIMITED` - Rate limit exceeded
- `DEPENDENCY_UNAVAILABLE` - Dependency unavailable
- `INTERNAL_ERROR` - Internal server error

## Authentication

KMS requires mTLS for all operations. Optional JWT authentication may be used for additional authorization.

## See Also

- KMS PRD: `docs/architecture/KMS_Trust_Stores_Module_PRD_v0_1_complete.md`
