# Configuration & Policy Management Module (EPC-3)

**Version:** 1.1.0
**Module ID:** M23 (code identifier for EPC-3)
**Description:** Enterprise-grade policy lifecycle management, configuration enforcement, and gold standards compliance for ZeroUI ecosystem

## Overview

The Configuration & Policy Management Module provides comprehensive policy lifecycle management, configuration governance, and compliance checking capabilities. It supports policy evaluation with hierarchy resolution, configuration drift detection, and automated compliance validation against gold standards.

## Features

- **Policy Lifecycle Management**: Draft → Review → Approved → Active → Deprecated
- **Policy Evaluation Engine**: Real-time policy evaluation with hierarchy resolution and precedence rules
- **Configuration Governance**: Version control, drift detection, automated remediation
- **Gold Standards Framework**: SOC2, GDPR, HIPAA, NIST compliance checking
- **Receipt-Driven Architecture**: All operations generate signed receipts for audit and UI rendering

## Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+** (with JSONB support)
- **Docker & Docker Compose** (for local development)

## Quick Start

### 1. Local Development with Docker

```bash
# Navigate to module directory
cd src/cloud-services/shared-services/configuration-policy-management

# Copy environment file (if exists)
cp env.example .env

# Start PostgreSQL database
docker-compose up -d postgres

# Wait for database to be ready
docker-compose ps

# Initialize database schema
python database/init_db.py

# Or use the shell script
chmod +x database/setup.sh
./database/setup.sh
```

### 2. Manual PostgreSQL Setup

If you have PostgreSQL installed locally:

```bash
# Set environment variable
export DATABASE_URL="postgresql://username:password@localhost:5432/configuration_policy_management"

# Initialize database
python database/init_db.py

# Or using psql directly
psql $DATABASE_URL -f database/schema.sql
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 4. Run the Service

```bash
# Run FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Tests

```bash
# Run all tests
python -m pytest tests/test_configuration_policy_management_*.py -v

# Run specific test suite
python -m pytest tests/test_configuration_policy_management_service.py -v
```

## API Endpoints

Per PRD v1.1.0, the module provides 8 API endpoints:

- `GET /policy/v1/health` - Health check
- `GET /policy/v1/metrics` - Runtime metrics
- `GET /policy/v1/config` - Module configuration
- `POST /policy/v1/policies` - Create policy
- `POST /policy/v1/policies/{policy_id}/evaluate` - Evaluate policy
- `POST /policy/v1/configurations` - Create configuration
- `GET /policy/v1/standards` - List gold standards
- `POST /policy/v1/compliance/check` - Check compliance
- `GET /policy/v1/audit` - Get audit summary
- `POST /policy/v1/remediation` - Trigger remediation

## Database Schema

The module uses three main tables per PRD (lines 128-186):

- **policies**: Policy definitions with versioning and scope
- **configurations**: Configuration definitions with environment-specific deployment
- **gold_standards**: Compliance framework definitions with control mappings

See `database/schema.sql` for complete schema definition.

## Architecture

This module implements ZeroUI's three-tier architecture:

- **Tier 1 (VS Code Extension)**: Receipt-driven UI components for policy and configuration management
- **Tier 2 (Edge Agent)**: Optional delegation for local caching and validation
- **Tier 3 (Cloud Services)**: Full business logic for policy evaluation, configuration management, and compliance checking

## Performance Requirements

Per PRD (lines 924-952):

- Policy evaluation: ≤50ms p95, ≤100ms p99, 10,000 RPS
- Configuration retrieval: ≤20ms p95, ≤50ms p99, 20,000 RPS
- Compliance check: ≤100ms p95, ≤250ms p99, 5,000 RPS

## Security

- All receipts are Ed25519-signed via EPC-11 (Key Management Service)
- Receipts stored in PM-7 (ERIS)
- Tenant isolation enforced at database level
- Input validation via Pydantic models

## Dependencies

This module depends on:

- **EPC-1 (IAM)**: Access control and authentication
- **PM-7 (ERIS)**: Receipt storage and signing
- **CCP-6 (Data Plane)**: Policy storage and caching
- **EPC-11 (Key Management)**: Receipt signing
- **EPC-12 (Schema Registry)**: Schema validation
- **CCP-1 (Trust Plane)**: Identity enrichment

## Testing

Comprehensive test coverage includes:

- Unit tests: 100% coverage of all service classes
- Integration tests: All API endpoints
- Database tests: All models, constraints, indexes
- Performance tests: Latency and throughput validation
- Security tests: Policy integrity, tenant isolation
- Functional tests: All acceptance criteria

Run all tests:

```bash
python -m pytest tests/test_configuration_policy_management_*.py -v --cov=src/cloud-services/shared-services/configuration-policy-management --cov-report=html
```

## Documentation

- **PRD**: `docs/architecture/modules/CONFIGURATION_POLICY_MANAGEMENT_MODULE.md`
- **Validation Reports**: See validation reports in `docs/architecture/modules/`

## License

ZeroUI 2.0 - Internal Use Only
