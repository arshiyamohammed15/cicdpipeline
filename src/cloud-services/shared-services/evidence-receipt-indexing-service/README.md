# Evidence & Receipt Indexing Service (ERIS) - PM-7

## Overview

Evidence & Receipt Indexing Service (ERIS) is a Platform Module (PM-7) that ingests, validates, indexes, and serves receipts and evidence produced across the ZeroUI system. It provides an immutable, append-only audit log with cryptographic integrity guarantees and multi-tenant isolation.

## Architecture

- **Type**: Platform Module (PM-7)
- **Tier**: Tier 3 (Business Logic Layer - FastAPI service)
- **Primary Planes**: CCP-3 Evidence & Audit Plane, CCP-1 Identity & Trust Plane, CCP-2 Policy & Configuration Plane, CCP-4 Observability & Reliability Plane

## Features

- Receipt ingestion (single, bulk, courier batch)
- Receipt validation and normalization
- Cryptographic integrity (hash chains, signature verification)
- Multi-tenant isolation and access control
- Query and aggregation APIs
- Retention, archival, and legal hold management
- Export APIs for compliance and BCDR
- Receipt chain traversal for multi-step flows

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `IAM_SERVICE_URL`: IAM service endpoint (optional, uses mock if not set)
   - `DATA_GOVERNANCE_SERVICE_URL`: Data Governance service endpoint (optional)
   - `CONTRACTS_SCHEMA_REGISTRY_URL`: Contracts & Schema Registry endpoint (optional)
   - `KMS_SERVICE_URL`: KMS service endpoint (optional)

3. Initialize database:
   ```bash
   python -m database.init_db
   ```

4. Run service:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- `GET /v1/evidence/health` - Health check
- `GET /v1/evidence/metrics` - Prometheus metrics
- `GET /v1/evidence/config` - Module configuration
- `POST /v1/evidence/receipts` - Ingest single receipt
- `POST /v1/evidence/receipts/bulk` - Bulk receipt ingestion
- `POST /v1/evidence/receipts/courier-batch` - Courier batch ingestion
- `POST /v1/evidence/search` - Search receipts
- `POST /v1/evidence/aggregate` - Aggregate receipts
- `GET /v1/evidence/receipts/{receipt_id}` - Get receipt by ID
- `GET /v1/evidence/receipts/{receipt_id}/verify` - Verify receipt integrity
- `POST /v1/evidence/verify_range` - Verify receipt range integrity
- `GET /v1/evidence/courier-batches/{batch_id}/merkle-proof` - Get Merkle proof
- `POST /v1/evidence/export` - Export receipts
- `GET /v1/evidence/export/{export_id}` - Get export status
- `GET /v1/evidence/receipts/{receipt_id}/chain` - Traverse receipt chain
- `POST /v1/evidence/receipts/chain-query` - Query receipt chains

## Testing

Run tests:
```bash
pytest tests/
```

## Documentation

See `docs/architecture/modules/ERIS_PRD.md` for complete Product Requirements Document.

