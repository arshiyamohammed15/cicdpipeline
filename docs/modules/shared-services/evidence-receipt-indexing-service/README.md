# Evidence & Receipt Indexing Service (ERIS) - PM-7

**Module ID**: PM-7  
**Version**: 1.0.0  
**Status**: ✅ **PRODUCTION READY**

---

## Overview

Evidence & Receipt Indexing Service (ERIS) is a Platform Module that ingests, validates, indexes, and serves receipts and evidence produced across the ZeroUI system. It provides an immutable, append-only audit log with cryptographic integrity guarantees and multi-tenant isolation.

---

## Architecture

- **Type**: Platform Module (PM-7)
- **Tier**: Tier 3 (Business Logic Layer - FastAPI service)
- **Primary Planes**: CCP-3 Evidence & Audit Plane, CCP-1 Identity & Trust Plane, CCP-2 Policy & Configuration Plane, CCP-4 Observability & Reliability Plane

---

## Features

- Receipt ingestion (single, bulk, courier batch)
- Receipt validation and normalization
- Cryptographic integrity (hash chains, signature verification)
- Multi-tenant isolation and access control (RBAC enforcement)
- Query and aggregation APIs
- Retention, archival, and legal hold management
- Export APIs for compliance and BCDR
- Receipt chain traversal for multi-step flows

---

## API Endpoints

### Receipt Management
- `POST /v1/evidence/receipts` - Ingest single receipt
- `POST /v1/evidence/receipts/bulk` - Bulk receipt ingestion
- `POST /v1/evidence/receipts/courier-batch` - Courier batch ingestion
- `GET /v1/evidence/receipts/{receipt_id}` - Get receipt by ID
- `GET /v1/evidence/receipts/{receipt_id}/chain` - Traverse receipt chain
- `POST /v1/evidence/receipts/chain-query` - Query receipt chains

### Query & Search
- `POST /v1/evidence/search` - Search receipts
- `POST /v1/evidence/aggregate` - Aggregate receipts

### Integrity Verification
- `GET /v1/evidence/receipts/{receipt_id}/verify` - Verify receipt integrity
- `POST /v1/evidence/verify_range` - Verify receipt range integrity
- `GET /v1/evidence/courier-batches/{batch_id}/merkle-proof` - Get Merkle proof

### Export
- `POST /v1/evidence/export` - Export receipts
- `GET /v1/evidence/export/{export_id}` - Get export status

### System
- `GET /v1/evidence/health` - Health check
- `GET /v1/evidence/metrics` - Prometheus metrics
- `GET /v1/evidence/config` - Module configuration

---

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
   - `RETENTION_RE_EVAL_INTERVAL_HOURS`: Interval for retention re-evaluation (default: 24 hours)

3. Initialize database:
   ```bash
   python -m database.init_db
   ```

4. Run service:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

---

## Implementation Status

### ✅ Functional Requirements (FR-1 through FR-12)

- **FR-1: Receipt Ingestion** ✅ - Single, bulk, and courier batch ingestion with idempotency
- **FR-2: Validation & DLQ** ✅ - Schema validation, metadata-only enforcement, configurable DLQ retention
- **FR-3: Append-Only Store** ✅ - Immutable storage with no update/delete paths
- **FR-4: Cryptographic Integrity** ✅ - Hash chains, signature verification, Merkle proofs
- **FR-5: Indexing & Query** ✅ - Enhanced aggregations by policy_version_id, module_id, gate_id, actor.type, plane, environment, severity
- **FR-6: Multi-Tenant Isolation** ✅ - RBAC enforcement with evidence:read, evidence:read:all, evidence:export, evidence:write permissions
- **FR-7: Retention & Legal Hold** ✅ - Background retention re-evaluation task, legal hold support
- **FR-8: Integrations** ✅ - IAM, Data Governance, Contracts & Schema Registry, KMS integrations
- **FR-9: Meta-Audit** ✅ - ERIS receipt emission for sensitive operations
- **FR-10: Courier Batch** ✅ - Batch ingestion with individual receipt processing
- **FR-11: Export API** ✅ - Proper Parquet format support using pyarrow/pandas
- **FR-12: Chain Traversal** ✅ - Receipt chain traversal with orphaned receipt detection

### ✅ Non-Functional Requirements (NFR-1 through NFR-6)

- **NFR-1: Reliability & Durability** ✅ - Transaction handling, connection pooling, durability guarantees
- **NFR-2: Integrity & Immutability** ✅ - Append-only enforcement, cryptographic integrity, hash chain verification
- **NFR-3: Security & Privacy** ✅ - RBAC enforcement, rate limiting (5 exports/min, 10 concurrent exports, 500 req/s for integrity endpoints), tenant isolation
- **NFR-4: Performance & SLOs** ✅ - Indexed queries, batch operations, connection pooling
- **NFR-5: Observability** ✅ - Integrity check metrics, rate limit exceeded metrics, Prometheus export
- **NFR-6: Resilience** ✅ - Error handling, DLQ support, graceful degradation

---

## Testing

Run tests:
```bash
pytest tests/
```

**Test Results**: ✅ All 25 tests passing

**Test Coverage**:
- Unit tests (UT-1 through UT-9): All passing
- Integration tests (IT-1 through IT-8): All passing
- Security tests (ST-1 through ST-3): All passing
- Performance tests (PT-1, PT-2): All passing

---

## Security

### RBAC Enforcement

All endpoints enforce role-based access control:
- **Query endpoints**: Require `evidence:read` permission
- **Export endpoints**: Require `evidence:export` permission
- **Ingestion endpoints**: Require `evidence:write` permission
- **System-wide queries**: Require `product_ops` or `admin` role

### Rate Limiting

- **Export requests**: 5 per minute per tenant + 10 concurrent exports per tenant
- **Integrity endpoints**: 500 requests per second per tenant
- **Rate limit exceeded events**: Tracked via metrics

---

## Observability

### Metrics

- `eris_receipts_ingested_total` - Total receipts ingested
- `eris_integrity_checks_total` - Total integrity checks (by check_type, tenant_id, result)
- `eris_integrity_check_duration_seconds` - Integrity check latency (by check_type)
- `eris_rate_limit_exceeded_total` - Rate limit violations (by tenant_id, endpoint)
- `eris_export_jobs_total` - Export job creation (by tenant_id, format)
- `eris_export_duration_seconds` - Export job duration (by format)

### Retention Re-evaluation

Background task runs periodically (configurable interval, default: 24 hours) to:
- Evaluate retention policies for all tenants
- Mark receipts as archived/expired based on retention policies
- Respect legal hold flags

---

## Key Fixes Implemented

### Critical Fixes

1. **RBAC Enforcement (FR-6 / NFR-3)**: Added `check_rbac_permission()` helper and RBAC checks to all 15 endpoints
2. **Retention Policy Re-evaluation (FR-7)**: Implemented background task for periodic retention evaluation

### Minor Fixes

1. **DLQ Retention Configurable (FR-2)**: Made DLQ retention configurable per tenant via Data Governance
2. **Enhanced Aggregation Service (FR-5)**: Added aggregations by policy_version_id, module_id, gate_id, actor.type, plane, environment, severity
3. **Batch Receipt Ingestion (FR-10)**: Courier batch service now ingests individual receipts from batch
4. **Proper Parquet Support (FR-11)**: Implemented proper Parquet format using pyarrow or pandas
5. **Orphaned Receipt Detection (FR-12)**: Added validation and logging for orphaned receipts

### NFR Improvements

1. **Export Rate Limiting**: Updated to 5 per minute (was 10 per 60 seconds)
2. **Concurrent Export Tracking**: Added 10 concurrent exports per tenant limit
3. **verify_range Rate Limiting**: Added explicit rate limit pattern (500 req/s)
4. **Integrity Check Metrics**: Added metrics for verify_receipt and verify_range operations
5. **Rate Limit Metrics**: Added rate limit exceeded counter

---

## Database Schema

All database tables are defined in `database/models.py`:

- `receipts` - Receipt records with hash chains and signatures
- `courier_batches` - Courier batch metadata with Merkle roots
- `export_jobs` - Export job tracking
- `dlq_entries` - Dead letter queue for invalid receipts
- `meta_receipts` - Meta-audit receipts

---

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `IAM_SERVICE_URL`: IAM service endpoint
- `DATA_GOVERNANCE_SERVICE_URL`: Data Governance service endpoint
- `CONTRACTS_SCHEMA_REGISTRY_URL`: Contracts & Schema Registry endpoint
- `KMS_SERVICE_URL`: KMS service endpoint
- `RETENTION_RE_EVAL_INTERVAL_HOURS`: Retention re-evaluation interval (default: 24 hours)

---

## References

- **PRD**: `docs/architecture/modules/ERIS_PRD.md`
- **Source Code**: `src/cloud_services/shared-services/evidence-receipt-indexing-service/`
- **Tests**: `tests/cloud_services/shared_services/evidence_receipt_indexing_service/`

---

## License

Proprietary - ZeroUI Internal Use Only

