# Key Management Service Module (EPC-11)

**Version:** 0.1.0
**Module ID:** M33 (code identifier for EPC-11)
**Description:** Cryptographic foundation and trust anchor for ZeroUI ecosystem

## Overview

The Key Management Service (KMS) Module provides cryptographic key lifecycle management, digital signing, encryption/decryption, and trust anchor management for the ZeroUI ecosystem. It implements HSM abstraction, key rotation, dual authorization, and comprehensive audit logging per KMS spec v0.1.0.

## Features

- **Key Lifecycle Management**: Generate, rotate, revoke cryptographic keys (RSA-2048, Ed25519, AES-256)
- **Digital Signing**: Create and verify digital signatures (Ed25519, RSA-PSS, RSA-PKCS1v15)
- **Encryption/Decryption**: Encrypt and decrypt data using AES-256-GCM, ChaCha20-Poly1305
- **Trust Anchor Management**: Ingest and manage X.509 certificates and trust anchors
- **HSM Abstraction**: Hardware Security Module interface with mock implementation
- **Dual Authorization**: Require dual approval for key lifecycle operations
- **Usage Limits**: Enforce per-key usage limits and rate limiting
- **Receipt-Driven Architecture**: All operations generate signed receipts for audit

## Prerequisites

- **Python 3.11+**
- **FastAPI** and dependencies (see requirements.txt)
- **HSM** (optional, mock implementation provided)

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to module directory
cd src/cloud-services/shared-services/key-management-service

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
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# Or using Python module
python -m key_management_service.main
```

### 4. Run Tests

```bash
# Run all tests
python -m pytest tests/test_key_management_service_*.py -v

# Run with coverage
python -m pytest tests/ --cov=key_management_service --cov-report=html
```

## API Endpoints

Per KMS spec v0.1.0, the module provides the following API endpoints:

- `GET /health` - Root health check
- `GET /kms/v1/health` - Health check with dependency status
- `GET /kms/v1/metrics` - Prometheus-format metrics
- `GET /kms/v1/config` - Module configuration
- `POST /kms/v1/keys` - Generate cryptographic key
- `POST /kms/v1/sign` - Create digital signature
- `POST /kms/v1/verify` - Verify digital signature
- `POST /kms/v1/encrypt` - Encrypt data
- `POST /kms/v1/decrypt` - Decrypt data
- `POST /kms/v1/keys/{key_id}/rotate` - Rotate key
- `POST /kms/v1/keys/{key_id}/revoke` - Revoke key
- `POST /kms/v1/trust-anchors` - Ingest trust anchor (certificate)

## Architecture

This module implements ZeroUI's three-tier architecture:

- **Tier 1 (VS Code Extension)**: Receipt-driven UI components for key management
- **Tier 2 (Edge Agent)**: Optional delegation for local key caching
- **Tier 3 (Cloud Services)**: Full business logic for key lifecycle, signing, encryption

## Performance Requirements

Per KMS spec:

- Key generation: ≤500ms p95, ≤1000ms p99, 100 RPS
- Signing: ≤50ms p95, ≤100ms p99, 1,000 RPS
- Verification: ≤20ms p95, ≤50ms p99, 2,000 RPS
- Encryption: ≤30ms p95, ≤60ms p99, 1,000 RPS
- Decryption: ≤30ms p95, ≤60ms p99, 1,000 RPS

## Security

- All receipts are Ed25519-signed via PM-7 (Evidence & Receipt Indexing Service / ERIS)
- Receipts stored in PM-7 (ERIS)
- mTLS validation required for all requests
- JWT validation optional but recommended
- Dual authorization required for key lifecycle operations
- Tenant isolation enforced at all levels
- Key state management: active, pending_rotation, archived, destroyed
- Usage limits: Default 10,000 operations per day per key
- CORS: Configured via environment variables (see Configuration)

## Dependencies

This module depends on:

- **EPC-1 (IAM)**: Authentication and authorization (mock implementation)
- **PM-7 (ERIS)**: Receipt storage and signing (mock implementation)
- **CCP-6 (Data Plane)**: Key metadata storage (mock implementation)
- **CCP-1 (Trust Plane)**: Certificate validation and mTLS (mock implementation)

**Note:** Mock dependencies are used for development. Production deployments require real implementations of EPC-1, PM-7, CCP-6, and CCP-1.

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

### Key Rotation Schedule

Default rotation schedule (per KMS spec):
- RSA-2048: 90 days
- Ed25519: 365 days
- AES-256: 90 days

### Allowed Algorithms

- **Signing**: Ed25519, RSA-PSS-SHA256, RSA-PKCS1v15-SHA256
- **Encryption**: AES-256-GCM, ChaCha20-Poly1305

### Dual Authorization Operations

Operations requiring dual authorization:
- Key generation (`key_lifecycle`)
- Key rotation (`key_lifecycle`)
- Key revocation (`key_lifecycle`)

## Testing

Comprehensive test coverage includes:

- Unit tests: Service layer, key lifecycle, cryptographic operations
- Integration tests: All API endpoints
- Middleware tests: Request logging, rate limiting, mTLS validation
- Security tests: Tenant isolation, dual authorization, key state management
- HSM tests: HSM interface and mock implementation

Run all tests:

```bash
python -m pytest tests/test_key_management_service_*.py -v --cov=key_management_service --cov-report=html
```

## Development

### Project Structure

```
key-management-service/
├── __init__.py
├── dependencies.py      # Mock dependencies (EPC-1, PM-7, CCP-6, CCP-1)
├── hsm/
│   ├── __init__.py
│   ├── interface.py    # HSM interface abstraction
│   └── mock_hsm.py     # Mock HSM implementation
├── main.py             # FastAPI application entry point
├── middleware.py       # Request logging, rate limiting, mTLS, JWT validation
├── models.py           # Pydantic models
├── routes.py           # API route handlers
├── services.py         # Business logic (KMS service, key lifecycle, crypto ops)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

### Adding New Features

1. **New Endpoints**: Add routes to `routes.py`
2. **Business Logic**: Add services to `services.py`
3. **Models**: Add Pydantic models to `models.py`
4. **HSM Operations**: Extend HSM interface in `hsm/interface.py`

### HSM Integration

The module provides HSM abstraction via `hsm/interface.py`. To integrate with a real HSM:

1. Implement `HSMInterface` from `hsm/interface.py`
2. Replace `MockHSM` with your HSM implementation in `services.py`
3. Update configuration to use real HSM

## Production Deployment

### Infrastructure Requirements

Per KMS spec:

- **Compute**: Minimum 4 vCPU, 2 GB RAM
- **HSM**: Hardware Security Module (AWS CloudHSM, Azure Dedicated HSM, etc.)
- **Networking**: TLS 1.3, mTLS required, service mesh integration
- **Storage**: Key metadata storage via CCP-6, receipt storage via PM-7

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

3. **Configure HSM**
   ```bash
   # Set HSM connection details
   export HSM_ENDPOINT="hsm.example.com"
   export HSM_CREDENTIALS="..."
   ```

4. **Deploy Application**
   ```bash
   # Using uvicorn
   uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4

   # Or using process manager (systemd, PM2, etc.)
   ```

### Health Checks

The service provides health check endpoints:

- **Liveness**: `GET /health` - Service is running
- **Readiness**: `GET /kms/v1/health` - Service is ready (checks HSM, storage, trust store)

### Monitoring

Monitor the following metrics:

- Key generation latency (p95, p99)
- Signing latency (p95, p99)
- Verification latency (p95, p99)
- Encryption/decryption latency (p95, p99)
- Error rates by error code
- Key usage counts
- HSM availability

## Troubleshooting

### Key Generation Fails

```bash
# Check HSM connectivity
# Health endpoint reports HSM status

# Check dual authorization
# Key generation requires X-Approval-Token header
```

### Signing/Verification Errors

```bash
# Check key state
# Keys must be "active" for cryptographic operations

# Check key usage limits
# Default: 10,000 operations per day per key
```

### mTLS Validation Fails

```bash
# Check client certificate
# mTLS middleware validates client certificates

# Check trust store
# Certificates must be in trust store (CCP-1)
```

## Integration

### With Other Modules

- **EPC-1 (IAM)**: Uses KMS for receipt signing
- **EPC-3 (Configuration & Policy Management)**: Uses KMS for receipt signing
- **EPC-12 (Schema Registry)**: Uses KMS for schema signing

### API Client Example

```python
import httpx
import base64

# Generate key
response = httpx.post(
    "http://kms-service:8002/kms/v1/keys",
    json={
        "tenant_id": "tenant123",
        "environment": "prod",
        "plane": "laptop",
        "key_type": "RSA-2048",
        "key_usage": "sign",
        "key_alias": "my-signing-key"
    },
    headers={"X-Approval-Token": "approval-token-123"}
)

# Sign data
data = b"Hello, World!"
data_b64 = base64.b64encode(data).decode('utf-8')

response = httpx.post(
    "http://kms-service:8002/kms/v1/sign",
    json={
        "key_id": "key-123",
        "data": data_b64,
        "algorithm": "RSA-PSS-SHA256",
        "tenant_id": "tenant123",
        "environment": "prod",
        "plane": "laptop"
    }
)
```

## License

ZeroUI 2.0 - Internal Use Only

## Version History

- **v0.1.0**: Current version - Initial KMS spec implementation
