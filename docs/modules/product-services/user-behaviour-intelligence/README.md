# User Behaviour Intelligence Module (EPC-9)

**Module ID**: EPC-9  
**Version**: 1.0.0  
**Status**: ✅ **PRODUCTION READY**

---

## Overview

User Behaviour Intelligence (UBI) Module provides behavioural analytics, anomaly detection, and signal generation based on user activity patterns. The module consumes events from PM-3, computes features, maintains baselines, detects anomalies, and generates behavioural signals.

---

## Architecture

- **Type**: Product Module (EPC-9)
- **Tier**: Tier 3 (Business Logic Layer - FastAPI service)
- **Event Source**: PM-3 Signal Ingestion (routing classes: realtime_detection, analytics_store)

---

## Features

### Core Functionality

1. **Event Processing Pipeline**: PM-3 → UBI event transformation and ingestion
2. **Feature Computation**: Rolling window feature computation (24h, 7d, 28d windows)
3. **Baseline Management**: EMA-based baseline computation with warm-up period
4. **Anomaly Detection**: Z-score based anomaly detection with configurable thresholds
5. **Signal Generation**: Risk, opportunity, and informational signal generation
6. **Event Streaming**: Signal publishing to downstream consumers (MMM, Detection Engine)

### Integration Points

1. **PM-3 Integration**: Event consumption via routing classes with idempotency and out-of-order handling
2. **ERIS Integration**: Receipt emission with retry logic and graceful degradation
3. **IAM Integration**: Token verification and role-based authorization
4. **Data Governance Integration**: Retention policies and data deletion

### Operational Features

1. **Configuration Management**: Versioned tenant configurations with validation
2. **Privacy Controls**: Data minimisation, tenant-level event filtering, k-anonymity (5 actors)
3. **Observability**: Prometheus metrics, structured logging, tracing support
4. **Reliability**: Graceful degradation, stale data handling, automatic recovery

---

## API Endpoints

- `GET /v1/ubi/actors/{actor_id}/profile` - Get actor behavioural profile
- `POST /v1/ubi/query/signals` - Query behavioural signals
- `GET /v1/ubi/config/{tenant_id}` - Get tenant configuration
- `PUT /v1/ubi/config/{tenant_id}` - Update tenant configuration
- `GET /v1/ubi/health` - Health check
- `GET /v1/ubi/metrics` - Prometheus metrics

---

## Implementation Status

### ✅ Phase 1: Foundation & Infrastructure Setup

- Service structure (main.py, routes.py, services.py, models.py, middleware.py, dependencies.py)
- Database schema with time-series partitioning by tenant_id and dt
- Database models (SQLAlchemy ORM)
- Configuration management with versioning and validation

### ✅ Phase 2: PM-3 Event Consumption

- PM-3 client subscription to routing classes
- Event mapper (PM-3 SignalEnvelope → UBI BehaviouralEvent)
- Event ingestion pipeline with validation and privacy filtering

### ✅ Phase 3: Feature Computation Engine

- Feature definitions (Activity, Flow, Collaboration, Agent Usage)
- Feature computation service with rolling windows (24h, 7d, 28d)
- Feature store interface for time-series storage

### ✅ Phase 4: Baseline Computation

- Baseline algorithm (EMA with configurable alpha, SMA for initial computation)
- Warm-up period (7 days minimum data requirement)
- Outlier handling (exclusion beyond 3 standard deviations)
- Z-score computation for anomaly detection

### ✅ Phase 5: Anomaly Detection

- Anomaly detection engine (Z-score based with configurable thresholds)
- Severity classification (INFO, WARN, CRITICAL)
- Anomaly resolution (automatic resolution when returning to baseline)

### ✅ Phase 6: Signal Generation

- Signal generation service with score computation (0-100)
- Signal type classification
- Evidence linking (ERIS evidence handles or embedded summaries)
- Signal dimensions (Activity, Flow, Collaboration, Agent Synergy)

### ✅ Phase 7: Event Streaming

- Event stream publisher (publish to ubi.behavioural_signals stream)
- Stream filtering (MMM: all signals, Detection Engine: high-severity only)
- Backpressure handling (buffering and rate limiting)
- DLQ support for failed delivery

### ✅ Phase 8: API Endpoints

- IAM integration (token verification middleware, role-based authorization)
- API routes (GET /actors/{actor_id}/profile, POST /query/signals, GET/PUT /config/{tenant_id})
- API models (complete Pydantic models)
- Error handling (401, 403, 400, 404 error responses)

### ✅ Phase 9: ERIS Receipt Integration

- Receipt generator (configuration changes and high-severity signals)
- ERIS client (POST /v1/evidence/receipts with retry logic)
- Receipt queue (local persistent queue for ERIS unavailability)
- DLQ support for failed receipt handling

### ✅ Phase 10: Data Governance Integration

- Data Governance client (retention policies, data deletion, privacy classification)
- Retention policy evaluation (daily batch job support)
- Data deletion (time-range and actor-based deletion)

### ✅ Phase 11: Observability & Metrics

- Metrics registry (all 8 Prometheus-format metrics per NFR-5)
- Tracing support (OpenTelemetry integration structure)

### ✅ Phase 12: Degradation & Reliability

- Degradation service (stale data detection, graceful degradation)
- Recovery handling (automatic resume when dependencies recover)

### ✅ Phase 13: OpenAPI Contract

- OpenAPI specification (complete API specification with all endpoints)
- Schemas (all request/response models documented)

### ✅ Phase 14: Testing

- Test structure (unit, integration, performance, security, privacy, resilience test directories)
- Sample tests (feature computation, baseline computation, anomaly detection, E2E tests)
- Test framework (pytest-based test structure)

---

## Production Components

### ✅ Database Connection Setup

- Connection pooling (QueuePool with configurable pool size: 20-200 connections)
- Connection management (pool_pre_ping=True, pool_recycle=600 seconds)
- Health checks (database health check endpoint with pool metrics)
- Repository pattern (complete repository layer for all entities)

### ✅ Event Bus Integration

- Flexible event bus interface (abstract EventBus class supporting multiple implementations)
- Kafka support (KafkaEventBus using aiokafka for async operations)
- RabbitMQ support (RabbitMQEventBus using aio-pika for async operations)
- In-memory bus (InMemoryEventBus for testing and development)
- Auto-detection (environment-based bus type selection)

### ✅ Prometheus Client Integration

- Full Prometheus integration (all 8 metrics per PRD NFR-5)
- Metrics endpoint (`/v1/ubi/metrics` for Prometheus scraping)
- Fallback mode (in-memory metrics when prometheus_client not available)
- Environment control (`UBI_OBSERVABILITY_MODE=prometheus` to enable Prometheus export)

### ✅ Complete Test Suite

- Unit tests (UT-UBI-01 through UT-UBI-05)
- Integration tests (IT-UBI-01 through IT-UBI-04)
- Performance tests (PT-UBI-01, PT-UBI-02)
- Security tests (ST-UBI-01, ST-UBI-02, ST-UBI-03)
- Privacy tests (PR-UBI-01, PR-UBI-02, PR-UBI-03)
- Resilience tests (RT-UBI-01, RT-UBI-02)

---

## Database Schema

All database tables are defined in `database/models.py`:

- `behavioural_events` - Time-series partitioned by tenant_id and dt
- `behavioural_features` - Feature storage with rolling windows
- `behavioural_baselines` - Baseline computation results
- `behavioural_signals` - Generated signals with scores and severity
- `tenant_configurations` - Versioned tenant configurations

---

## Testing

Run tests:
```bash
pytest tests/ -v
```

**Test Coverage**: Comprehensive coverage for all PRD Section 13 test cases

---

## Configuration

### Environment Variables

- `UBI_DATABASE_URL`: PostgreSQL connection string
- `PM3_SERVICE_URL`: PM-3 Signal Ingestion service URL
- `ERIS_SERVICE_URL`: ERIS service URL
- `IAM_SERVICE_URL`: IAM service URL
- `DATA_GOVERNANCE_SERVICE_URL`: Data Governance service URL
- `UBI_EVENT_BUS_TYPE`: Event bus type (kafka, rabbitmq, in_memory)
- `UBI_OBSERVABILITY_MODE`: Observability mode (prometheus, in_memory)

---

## Observability

### Prometheus Metrics

- `ubi_events_processed_total{tenant_id, event_type, status}` - Total events processed
- `ubi_signals_generated_total{tenant_id, dimension, signal_type}` - Total signals generated
- `ubi_anomalies_total{tenant_id, dimension, severity}` - Total anomalies detected
- `ubi_receipt_emission_total{tenant_id, status}` - Total receipts emitted
- `ubi_feature_computation_duration_seconds{tenant_id, feature_name}` - Feature computation latency
- `ubi_baseline_recompute_duration_seconds{tenant_id, actor_scope}` - Baseline recompute latency
- `ubi_api_request_duration_seconds{tenant_id, endpoint, method}` - API request latency
- `ubi_queue_size{tenant_id}` - Queue size gauge

---

## References

- **PRD**: `docs/architecture/modules/UBI_PRD.md`
- **Source Code**: `src/cloud_services/product-services/user_behaviour_intelligence/`
- **Tests**: `tests/cloud_services/product_services/user_behaviour_intelligence/`

---

## License

Proprietary - ZeroUI Internal Use Only

