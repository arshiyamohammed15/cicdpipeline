# Budgeting, Rate-Limiting & Cost Observability Module (EPC-13)

Enterprise-grade resource budgeting, rate-limiting enforcement, and cost transparency for ZeroUI ecosystem.

## Module Information

- **Module ID**: M35 (code identifier for EPC-13)
- **Version**: 1.0.0
- **PRD Version**: 3.0.0
- **Status**: ✅ Ready for Implementation

## Quick Start

### Installation

```bash
cd src/cloud-services/shared-services/budgeting-rate-limiting-cost-observability
pip install -r requirements.txt
```

### Running the Service

```bash
python -m main
```

The service will start on `http://localhost:8000`

### Health Check

```bash
curl http://localhost:8000/budget/v1/health
```

## Architecture

### Components

1. **Budget Management Engine**: Real-time budget enforcement with period calculation
2. **Rate-Limiting Framework**: Multiple algorithms (token bucket, leaky bucket, fixed window, sliding window log)
3. **Cost Calculation Engine**: Real-time metering, attribution, aggregation, anomaly detection
4. **Quota Management System**: Allocation strategies, enforcement, renewal automation
5. **Receipt Service**: Canonical PM-7 (ERIS) receipt generation for all operations
6. **Event Service**: Event publishing to EPC-4 (Alerting & Notification Service) using common envelope pattern

### Dependencies

- **EPC-1 (IAM)**: Authentication and authorization
- **PM-7 (ERIS)**: Receipt storage and signing
- **CCP-6 (Data Plane)**: Persistent storage
- **EPC-4 (Alerting & Notification Service)**: Event delivery
- **EPC-11 (Key Management)**: Receipt signing

## API Endpoints

### Budgets
- `POST /budget/v1/budgets/check` - Check budget availability
- `POST /budget/v1/budgets` - Create budget
- `GET /budget/v1/budgets` - List budgets

### Rate Limits
- `POST /budget/v1/rate-limits/check` - Check rate limit

### Cost Tracking
- `POST /budget/v1/cost-tracking/record` - Record cost

### Quotas
- `POST /budget/v1/quotas/allocate` - Allocate quota

## Testing

### Run Tests

```bash
pytest tests/ -v --cov=. --cov-report=html
```

### Test Coverage

Current coverage includes:
- Budget service unit tests
- Receipt service unit tests
- Additional tests in progress

## Database Schema

All database tables are defined in `database/models.py`:
- `budget_definitions`
- `rate_limit_policies`
- `cost_records`
- `quota_allocations`
- `budget_utilization`
- `rate_limit_usage`
- `quota_usage_history`

## Configuration

Environment variables:
- `DATABASE_URL`: Database connection string
- `ENVIRONMENT`: Environment (development, staging, production)
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins

## Documentation

- **PRD**: `docs/architecture/modules/BUDGETING_RATE_LIMITING_COST_OBSERVABILITY_PRD_patched.md`
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`

## License

Proprietary - ZeroUI Internal Use Only

