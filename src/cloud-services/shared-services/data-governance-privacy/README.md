# Data Governance & Privacy Module (M22)

Enterprise-grade data classification, privacy enforcement, consent management, lineage tracking, retention automation, and rights orchestration for the ZeroUI platform.

## Overview

| Capability | Description |
| --- | --- |
| Data Classification | Automated detection of PII/SPI/PHI with pattern matching, heuristic scoring, and manual overrides |
| Privacy Enforcement | Policy-driven IAM integration with consent validation, violation detection, and signed receipts |
| Consent Management | Granular consent capture, verification, withdrawal, and lifecycle metrics |
| Data Lineage | End-to-end lineage capture, provenance queries, and impact analysis |
| Retention & Deletion | Policy enforcement with legal hold awareness and automated deletion recommendations |
| Data Subject Rights | Automated workflows for GDPR/CCPA rights (access, rectification, erasure, restriction, portability, objection) |

## Architecture

- **Language:** Python 3.11+
- **Framework:** FastAPI (Tier 3 business logic only)
- **Data Layer:** PostgreSQL schema defined in `database/schema.sql` with SQLAlchemy ORM models
- **Dependencies:** Mock integrations for M21 (IAM), M23 (Policy), M27 (Evidence Ledger), M29 (Data Plane), M33 (KMS)
- **Entry Point:** `main.py` (`uvicorn src.cloud-services.shared-services.data-governance-privacy.main:app --reload`)

## Quick Start

```bash
# Install dependencies
pip install -r src/cloud-services/shared-services/data-governance-privacy/requirements.txt

# Initialize database (ensure PostgreSQL is running)
python src/cloud-services/shared-services/data-governance-privacy/database/init_db.py --database-url postgresql://user:pass@localhost:5432/m22_privacy

# Run service
uvicorn src.cloud-services.shared-services.data-governance-privacy.main:app --host 0.0.0.0 --port 8080 --reload
```

## API Summary

| Endpoint | Method | Description |
| --- | --- | --- |
| `/privacy/v1/health` | GET | Service health |
| `/privacy/v1/metrics` | GET | Latency & throughput metrics |
| `/privacy/v1/config` | GET | Module identity, endpoints, performance budgets |
| `/privacy/v1/classification` | POST | Classify data payload |
| `/privacy/v1/consent/check` | POST | Verify consent for purpose & categories |
| `/privacy/v1/compliance` | POST | Enforce privacy policy (IAM + consent + receipts) |
| `/privacy/v1/lineage` | POST/GET | Capture lineage / query lineage |
| `/privacy/v1/retention/evaluate` | POST | Evaluate retention action |
| `/privacy/v1/rights/request` | POST | Submit rights request (202 Accepted) |

Refer to `models.py` for full request/response schemas.

## Testing

```bash
pytest tests/test_data_governance_privacy_service.py \
       tests/test_data_governance_privacy_routes.py \
       tests/test_data_governance_privacy_performance.py \
       tests/test_data_governance_privacy_functional.py \
       tests/test_data_governance_privacy_security.py -v
```

- **Unit tests:** `tests/test_data_governance_privacy_service.py`
- **Integration tests:** `tests/test_data_governance_privacy_routes.py`
- **Performance tests:** `tests/test_data_governance_privacy_performance.py`
- **Functional tests:** `tests/test_data_governance_privacy_functional.py`
- **Security tests:** `tests/test_data_governance_privacy_security.py`

All tests are hermetic, deterministic, and align with PRD acceptance criteria (latency budgets, consent accuracy, privacy enforcement, tenant isolation).
