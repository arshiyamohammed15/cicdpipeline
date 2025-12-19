# Identity & Access Management Module (EPC-1)

**Version:** 1.1.0
**Module ID:** M21 (code identifier for EPC-1)
**Description:** Authentication and authorization gatekeeper for ZeroUI ecosystem with RBAC/ABAC evaluation, JWT token management, and policy enforcement

## Overview

The Identity & Access Management (IAM) Module provides secure access control for the ZeroUI ecosystem. It implements token verification, access decision evaluation, policy management, JIT elevation, and break-glass access capabilities per IAM spec v1.1.0.

## Features

- **Token Verification**: JWT token validation with RS256 (RSA-2048) signatures, 1h expiry, refresh at 55m
- **Access Decision Evaluation**: RBAC/ABAC evaluation with precedence order (deny → RBAC → ABAC)
- **Policy Management**: Versioned policy bundles with SHA-256 snapshot_id, immutable releases
- **JIT Elevation**: Just-in-time privilege elevation with dual approval for admin scope
- **Break-Glass Access**: Crisis mode access with minimal time-boxed admin (default 4h)
- **Receipt-Driven Architecture**: All operations generate Ed25519-signed receipts for audit

## Prerequisites

- **Python 3.11+**
- **FastAPI** and dependencies (see requirements.txt)

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to module directory
cd src/cloud-services/shared-services/identity-access-management

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Set environment (optional, defaults to development)
export ENVIRONMENT="development"
```

### 3. Run the Service

```bash
# Run FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Or using Python module
python -m identity_access_management.main
```

### 4. Run Tests

```bash
# Run all tests
python -m pytest tests/test_identity_access_management_*.py -v

# Run with coverage
python -m pytest tests/ --cov=identity_access_management --cov-report=html
```

## API Endpoints

Per IAM spec v1.1.0, the module provides the following API endpoints:

- `GET /health` - Root health check
- `GET /iam/v1/health` - Health check
- `GET /iam/v1/metrics` - Runtime metrics
- `GET /iam/v1/config` - Module configuration
- `POST /iam/v1/verify` - Verify identity/token
- `POST /iam/v1/decision` - Evaluate access decision or JIT elevation
- `POST /iam/v1/break-glass` - Trigger break-glass access
- `PUT /iam/v1/policies` - Upsert policy bundle (versioned)

## Architecture

This module implements ZeroUI's three-tier architecture:

- **Tier 1 (VS Code Extension)**: Receipt-driven UI components for IAM operations
- **Tier 2 (Edge Agent)**: Optional delegation for local caching and validation
- **Tier 3 (Cloud Services)**: Full business logic for authentication, authorization, and policy management

## Performance Requirements

Per IAM spec (section 1):

- Authentication response: ≤200ms p95, ≤500ms p99, 5,000 RPS
- Policy evaluation: ≤50ms p95, ≤100ms p99, 10,000 RPS
- Access decision: ≤100ms p95, ≤200ms p99, 5,000 RPS
- Token validation: ≤10ms p95, ≤20ms p99, 20,000 RPS
- Max memory: 512 MB

## Security

- All receipts are Ed25519-signed via PM-7 (Evidence & Receipt Indexing Service / ERIS)
- Receipts stored in PM-7 (ERIS)
- JWT tokens: RS256 (RSA-2048), 1h expiry, refresh at 55m
- Token revocation: jti denylist with TTL=exp, propagate within 5s
- Rate limiting: 50 RPS/client, burst 200 for 10s
- Idempotency: Required for /policies endpoint via X-Idempotency-Key (24h window)
- CORS: Configured via environment variables (see Configuration)

## Dependencies

This module depends on:

- **PM-7 (ERIS)**: Receipt storage and signing (mock implementation)
- **CCP-6 (Data Plane)**: Policy storage and caching (mock implementation)
- **CCP-1 (Trust Plane)**: Device posture and service identity (mock implementation)

**Note:** Mock dependencies are used for development. Production deployments require real implementations of PM-7, CCP-6, and CCP-1.

## Configuration

### Environment Variables

- `ENVIRONMENT` - Environment name (default: "development")
  - Used for service metadata and logging

### CORS Configuration

CORS origins are configured via environment variable:

```bash
# Allow specific origins (comma-separated)
export CORS_ORIGINS="https://app.example.com,https://admin.example.com"

# Default: "*" (all origins) - NOT RECOMMENDED FOR PRODUCTION
```

### Rate Limiting

Default rate limits (per IAM spec section 6):
- 50 RPS per client
- Burst: 200 requests per 10 seconds

## Testing

Comprehensive test coverage includes:

- Unit tests: Service layer, token validation, RBAC/ABAC evaluation
- Integration tests: All API endpoints
- Middleware tests: Request logging, rate limiting, idempotency
- Security tests: Token validation, policy enforcement, tenant isolation

Run all tests:

```bash
python -m pytest tests/test_identity_access_management_*.py -v --cov=identity_access_management --cov-report=html
```

## Development

### Project Structure

```
identity-access-management/
├── __init__.py
├── dependencies.py      # Mock dependencies (PM-7, CCP-6, CCP-1)
├── main.py             # FastAPI application entry point
├── middleware.py       # Request logging, rate limiting, idempotency
├── models.py           # Pydantic models
├── routes.py           # API route handlers
├── services.py         # Business logic (IAM service, token validator, etc.)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

### Adding New Features

1. **New Endpoints**: Add routes to `routes.py`
2. **Business Logic**: Add services to `services.py`
3. **Models**: Add Pydantic models to `models.py`
4. **Middleware**: Add middleware to `middleware.py`

## Production Deployment

### Infrastructure Requirements

Per IAM spec:

- **Compute**: Minimum 2 vCPU, 512 MB RAM
- **Networking**: TLS 1.3, service mesh integration
- **Storage**: Receipt storage via PM-7, policy storage via CCP-6

### Deployment Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   export ENVIRONMENT="production"
   export CORS_ORIGINS="https://app.example.com"
   ```

3. **Deploy Application**
   ```bash
   # Using uvicorn
   uvicorn main:app --host 0.0.0.0 --port 8001 --workers 4

   # Or using process manager (systemd, PM2, etc.)
   ```

### Health Checks

The service provides health check endpoints:

- **Liveness**: `GET /health` - Service is running
- **Readiness**: `GET /iam/v1/health` - Service is ready

### Monitoring

Monitor the following metrics:

- Authentication latency (p95, p99)
- Decision evaluation latency (p95, p99)
- Policy evaluation latency (p95, p99)
- Token validation latency (p95, p99)
- Error rates by error code
- Rate limit violations

## Troubleshooting

### Token Verification Fails

```bash
# Check token format
# Tokens must be JWT with required claims: kid, iat, exp, aud, iss, sub, scope

# Check token expiration
# Tokens expire after 1 hour, refresh at 55 minutes
```

### Rate Limiting Issues

```bash
# Check rate limit configuration
# Default: 50 RPS, burst 200/10s

# Check client identification
# Rate limits are per client (X-Client-Id header or IP address)
```

### Policy Evaluation Errors

```bash
# Check policy format
# Policies must be valid JSON with required fields: id, rules, status

# Check policy status
# Only "released" policies are evaluated
```

## Integration

### With Other Modules

- **EPC-3 (Configuration & Policy Management)**: Uses IAM for access control
- **EPC-11 (Key Management)**: Uses IAM for authentication
- **EPC-12 (Schema Registry)**: Uses IAM for access control

### API Client Example

```python
import httpx

# Verify token
response = httpx.post(
    "http://iam-service:8001/iam/v1/verify",
    json={"token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."}
)

# Evaluate access decision
response = httpx.post(
    "http://iam-service:8001/iam/v1/decision",
    json={
        "subject": {"sub": "user123", "roles": ["developer"]},
        "action": "read",
        "resource": "config:policy:123"
    }
)
```

## License

ZeroUI 2.0 - Internal Use Only

## Version History

- **v1.1.0**: Current version - Full IAM spec implementation
- **v1.0.0**: Initial implementation
