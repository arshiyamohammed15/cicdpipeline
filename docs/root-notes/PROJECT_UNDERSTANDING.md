# ZeroUI 2.0 - Comprehensive Project Understanding

**Document Purpose**: Deep understanding of ZeroUI 2.0 architecture, patterns, and implementation guidelines for new module development.

**Last Updated**: Current session
**Status**: Complete understanding based on codebase analysis

---

## 1. Project Overview

### 1.1 What is ZeroUI 2.0?

ZeroUI 2.0 is an enterprise-grade AI-powered code validation and development platform implementing a **three-tier hybrid architecture** with strict separation of concerns:

- **415 Constitution Rules**: Comprehensive rule set for code validation
- **22 Rule Validators**: AST-based code analysis
- **Three-Tier Architecture**: Presentation, Edge Processing, and Business Logic layers
- **24+ Microservices**: Python/FastAPI cloud services
- **20 Business Modules**: M01-M20 covering various domains
- **Comprehensive Testing**: 100+ test files with unit, integration, security, performance, and resilience tests

### 1.2 Key Principles

1. **Strict Separation of Concerns**: Business logic ONLY in Tier 3 (Cloud Services)
2. **Receipt-Driven UI**: All UI rendering from Edge Agent receipts
3. **Multi-Tenant Isolation**: Strong tenant boundaries throughout
4. **Observability First**: Comprehensive metrics, logs, and traces
5. **Security by Design**: IAM, KMS, data governance integrated
6. **Contract-Driven**: OpenAPI schemas and JSON Schema validation

---

## 2. Three-Tier Architecture

### 2.1 Tier 1: VS Code Extension (Presentation Layer)

**Location**: `src/vscode-extension/`
**Technology**: TypeScript, VS Code Extension API
**Responsibility**: Presentation-only UI rendering

**Key Characteristics**:
- Receives receipts from Edge Agent
- Renders UI only (NO business logic)
- 20 module UI components + 6 core UI components
- Modular structure with manifest-based registration

**Structure**:
```
src/vscode-extension/
├── extension.ts                    # Main orchestration
├── modules/                        # Module logic (manifest-based)
│   ├── m01-mmm-engine/
│   │   ├── module.manifest.json
│   │   ├── index.ts
│   │   ├── commands.ts
│   │   ├── providers/
│   │   ├── views/
│   │   └── actions/
│   └── [m02-m20 other modules...]
└── ui/                            # UI components
    ├── [Core UI Components]
    └── [20 Module UI Components]
```

**Pattern**: ExtensionInterface → UIComponentManager → UIComponent

### 2.2 Tier 2: Edge Agent (Delegation Layer)

**Location**: `src/edge-agent/`
**Technology**: TypeScript
**Responsibility**: Delegation and validation only

**Key Characteristics**:
- Delegates tasks to Cloud Services
- Validates results (NO business logic)
- 6 infrastructure modules (security, cache, inference, etc.)
- Business logic modules (M01-M20) do NOT need Edge Agent implementations

**Structure**:
```
src/edge-agent/
├── EdgeAgent.ts                    # Main orchestrator
├── core/
│   ├── AgentOrchestrator.ts
│   ├── DelegationManager.ts
│   └── ValidationCoordinator.ts
└── modules/
    ├── security-enforcer/
    ├── cache-manager/
    ├── hybrid-orchestrator/
    ├── local-inference/
    ├── model-manager/
    └── resource-optimizer/
```

**Pattern**: Implements `DelegationInterface` for infrastructure modules only

### 2.3 Tier 3: Cloud Services (Business Logic Layer)

**Location**: `src/cloud_services/`
**Technology**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic
**Responsibility**: ALL business logic implementation

**Key Characteristics**:
- FastAPI microservices
- Service-oriented architecture
- Clear Client/Product/Shared service separation
- Independent service modules with FastAPI routers

**Structure**:
```
src/cloud_services/
├── client-services/                # 9 modules (company-owned, private data)
│   ├── compliance-security-challenges/
│   ├── cross-cutting-concerns/
│   ├── feature-development-blind-spots/
│   ├── knowledge-silo-prevention/
│   ├── legacy-systems-safety/
│   ├── merge-conflicts-delays/
│   ├── monitoring-observability-gaps/
│   ├── release-failures-rollbacks/
│   └── technical-debt-accumulation/
├── product-services/               # 4 modules (ZeroUI-owned, cross-tenant)
│   ├── detection-engine-core/
│   ├── knowledge-integrity-discovery/
│   ├── mmm_engine/
│   ├── signal-ingestion-normalization/
│   └── user_behaviour_intelligence/
└── shared-services/                # 10+ modules (ZeroUI-owned, infrastructure)
    ├── alerting-notification-service/
    ├── budgeting-rate-limiting-cost-observability/
    ├── configuration-policy-management/
    ├── contracts-schema-registry/
    ├── data-governance-privacy/
    ├── deployment-infrastructure/
    ├── evidence-receipt-indexing-service/
    ├── health-reliability-monitoring/
    ├── identity-access-management/
    └── key-management-service/
```

---

## 3. Module Structure & Implementation Patterns

### 3.1 Standard Cloud Service Module Structure

Every cloud service module follows this structure:

```
{module-name}/
├── __init__.py
├── main.py                 # FastAPI app entrypoint
├── routes.py               # API routes (HTTP concerns only)
├── services.py            # Business logic (ALL logic here)
├── models.py               # Pydantic domain models
├── dependencies.py         # Mock clients for shared services
├── service_registry.py     # Service registry for DI
├── middleware.py           # Optional: Custom middleware
├── config.py               # Configuration management
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLAlchemy ORM models
│   ├── repositories.py     # Repository pattern
│   ├── connection.py       # DB session management
│   └── migrations/         # Alembic migrations
├── integrations/          # External service clients
│   ├── iam_client.py
│   ├── eris_client.py
│   └── [other clients]
├── observability/
│   ├── metrics.py          # Prometheus metrics
│   ├── tracing.py          # OpenTelemetry tracing
│   └── audit.py             # Audit logging
├── reliability/
│   └── circuit_breaker.py  # Circuit breaker patterns
└── requirements.txt        # Python dependencies
```

### 3.2 Implementation Pattern: main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .service_registry import initialize_services

def create_app() -> FastAPI:
    initialize_services()
    
    app = FastAPI(
        title="ZeroUI {Module Name} Service",
        version="2.0.0",
        description="{Module Name} business logic service"
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(router, prefix="/api/v1", tags=["{module-name}"])
    
    return app

app = create_app()
```

### 3.3 Implementation Pattern: routes.py

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from .models import ProcessDataRequest, ProcessDataResponse
from .services import {ModuleName}Service
from .database.connection import get_db

router = APIRouter(prefix="/v1/{module-name}", tags=["{module-name}"])

_service: {ModuleName}Service | None = None

def get_service() -> {ModuleName}Service:
    global _service
    if _service is None:
        _service = {ModuleName}Service()
    return _service

def get_tenant_id(request: Request) -> str:
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant context missing")
    return tenant_id

@router.post("/process", response_model=ProcessDataResponse)
async def process_data(
    request_body: ProcessDataRequest,
    request: Request,
    service: {ModuleName}Service = Depends(get_service),
    db: Session = Depends(get_db),
) -> ProcessDataResponse:
    tenant_id = get_tenant_id(request)
    # Route only handles HTTP concerns, delegates to service
    result = await service.process_data(request_body, db)
    db.commit()
    return result
```

**CRITICAL**: All business logic goes in `services.py`, NOT in `routes.py`.

### 3.4 Implementation Pattern: services.py

```python
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from .models import ProcessDataRequest, ProcessDataResponse
from .database.repositories import DataRepository
from .integrations.iam_client import IAMClient
from .integrations.eris_client import ERISClient
from .observability.metrics import record_operation_metrics

logger = logging.getLogger(__name__)

class {ModuleName}Service:
    """
    Main service orchestrating {Module Name} business logic.
    
    Per PRD: Implements all functional requirements.
    """
    
    def __init__(
        self,
        db_session: Optional[Session] = None,
        iam_client: Optional[IAMClient] = None,
        eris_client: Optional[ERISClient] = None
    ):
        self.db_session = db_session
        self.iam_client = iam_client or IAMClient()
        self.eris_client = eris_client or ERISClient()
        self.repository = DataRepository(db_session) if db_session else None
    
    async def process_data(self, request: ProcessDataRequest, db: Session) -> ProcessDataResponse:
        """
        IMPLEMENT YOUR BUSINESS LOGIC HERE
        This is the ONLY place where business logic should exist.
        """
        # 1. Validate input
        # 2. Check permissions (via IAM)
        # 3. Process data (your business logic)
        # 4. Persist results (via repository)
        # 5. Emit receipts (via ERIS)
        # 6. Record metrics
        # 7. Return response
        
        return ProcessDataResponse(...)
```

### 3.5 Implementation Pattern: models.py (Pydantic)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class {ModuleName}Data(BaseModel):
    id: str = Field(..., description="Unique identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    status: Status = Field(..., description="Status")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProcessDataRequest(BaseModel):
    data: Dict[str, Any] = Field(..., description="Input data")
    options: Optional[Dict[str, Any]] = None

class ProcessDataResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### 3.6 Implementation Pattern: database/models.py (SQLAlchemy)

```python
from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()

# Platform-independent UUID type
class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

class {ModuleName}Model(Base):
    __tablename__ = "{module_name}"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    metadata = Column(JSONB if HAS_POSTGRES else JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_{module_name}_tenant_status', 'tenant_id', 'status'),
    )
```

### 3.7 Implementation Pattern: database/repositories.py

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import {ModuleName}Model
from ..models import {ModuleName}Data

class {ModuleName}Repository:
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, data: {ModuleName}Data) -> {ModuleName}Data:
        db_model = {ModuleName}Model(
            id=data.id,
            tenant_id=data.tenant_id,
            status=data.status.value,
            metadata=data.metadata
        )
        self.session.add(db_model)
        self.session.flush()
        return self._to_schema(db_model)
    
    def get(self, tenant_id: str, id: str) -> Optional[{ModuleName}Data]:
        model = self.session.query({ModuleName}Model).filter(
            {ModuleName}Model.tenant_id == tenant_id,
            {ModuleName}Model.id == id
        ).first()
        return self._to_schema(model) if model else None
    
    def list(self, tenant_id: str) -> List[{ModuleName}Data]:
        models = self.session.query({ModuleName}Model).filter(
            {ModuleName}Model.tenant_id == tenant_id
        ).all()
        return [self._to_schema(m) for m in models]
    
    def _to_schema(self, model: {ModuleName}Model) -> {ModuleName}Data:
        return {ModuleName}Data(
            id=str(model.id),
            tenant_id=model.tenant_id,
            status=Status(model.status),
            metadata=model.metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )
```

---

## 4. Dependencies & Integrations

### 4.1 Shared Services Integration Pattern

Modules integrate with shared services via:

1. **Service Registry Pattern**: Centralized accessors for shared services
2. **Mock Clients**: Development/testing with mock implementations
3. **Real Clients**: Production HTTP clients to actual services

**Example: service_registry.py**

```python
from typing import Optional
from .dependencies import MockM21IAM, MockM7ERIS, MockM22DataGovernance
from .integrations.iam_client import IAMClient
from .integrations.eris_client import ERISClient

_iam: Optional[IAMClient] = None
_eris: Optional[ERISClient] = None

def initialize_services() -> None:
    global _iam, _eris
    if _iam is not None:
        return
    
    # In production, use real clients
    _iam = IAMClient()
    _eris = ERISClient()
    
    logger.info("Service registry initialized")

def get_iam() -> IAMClient:
    if _iam is None:
        initialize_services()
    return _iam
```

### 4.2 Key Shared Services

#### M21 - Identity & Access Management (IAM)
- **Location**: `src/cloud_services/shared-services/identity-access-management/`
- **Purpose**: Authentication, authorization, token validation
- **Integration**: Via `IAMClient` or `MockM21IAM`

#### M27 - Evidence Receipt Indexing Service (ERIS)
- **Location**: `src/cloud_services/shared-services/evidence-receipt-indexing-service/`
- **Purpose**: Receipt storage, signing, audit trail
- **Integration**: Via `ERISClient` or `MockM7ERIS`

#### M29 - Data Governance & Privacy
- **Location**: `src/cloud_services/shared-services/data-governance-privacy/`
- **Purpose**: Data classification, PII handling, retention policies
- **Integration**: Via `DataGovernanceClient` or `MockM29DataGovernance`

#### M33 - Key Management Service (KMS)
- **Location**: `src/cloud_services/shared-services/key-management-service/`
- **Purpose**: Secret management, cryptographic operations
- **Integration**: Via `KMSClient` or `MockM33KMS`

#### M35 - Budgeting, Rate-Limiting & Cost Observability
- **Location**: `src/cloud_services/shared-services/budgeting-rate-limiting-cost-observability/`
- **Purpose**: Budget enforcement, rate limiting, cost tracking
- **Integration**: Via `BudgetClient` or `MockM35Budgeting`

#### M34 - Contracts & Schema Registry
- **Location**: `src/cloud_services/shared-services/contracts-schema-registry/`
- **Purpose**: Schema validation, contract management
- **Integration**: Via `SchemaRegistryClient` or `MockM34SchemaRegistry`

### 4.3 Integration Client Pattern

```python
import httpx
from typing import Optional, Dict, Any

class IAMClient:
    def __init__(self, base_url: str = "http://iam-service:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        response = await self.client.post(
            f"{self.base_url}/v1/iam/verify",
            json={"token": token}
        )
        response.raise_for_status()
        return response.json()
    
    async def check_permission(self, tenant_id: str, resource: str, action: str) -> bool:
        # Implementation
        pass
```

---

## 5. Observability Patterns

### 5.1 Metrics (Prometheus)

**Location**: `{module}/observability/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge

# Counters
operations_total = Counter(
    "{module}_operations_total",
    "Total operations",
    ["tenant_id", "operation_type"]
)

# Histograms
operation_latency = Histogram(
    "{module}_operation_latency_seconds",
    "Operation latency",
    ["tenant_id"],
    buckets=[0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0, 2.0]
)

# Gauges
active_connections = Gauge(
    "{module}_active_connections",
    "Active connections",
    ["tenant_id"]
)

def record_operation(tenant_id: str, operation_type: str, latency: float):
    operations_total.labels(tenant_id, operation_type).inc()
    operation_latency.labels(tenant_id).observe(latency)
```

### 5.2 Structured Logging

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def log_operation(
    tenant_id: str,
    operation: str,
    status: str,
    metadata: Dict[str, Any] = None
):
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "operation": operation,
        "status": status,
        "metadata": metadata or {}
    }
    logger.info(json.dumps(log_data))
```

### 5.3 Tracing (OpenTelemetry)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def process_with_trace(operation: str):
    with tracer.start_as_current_span(operation) as span:
        span.set_attribute("tenant_id", tenant_id)
        # Your operation
        span.set_status(trace.Status(trace.StatusCode.OK))
```

---

## 6. Testing Patterns

### 6.1 Test Structure

```
tests/
├── {module_name}/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── test_services.py
│   │   ├── test_repositories.py
│   │   └── test_models.py
│   ├── integration/
│   │   ├── test_api.py
│   │   └── test_clients.py
│   ├── security/
│   │   └── test_security.py
│   ├── performance/
│   │   └── test_performance.py
│   └── resilience/
│       └── test_resilience.py
```

### 6.2 Test Fixture Pattern

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .main import app
from .database.models import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def client(db_session):
    def get_db():
        yield db_session
    app.dependency_overrides[get_db] = get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### 6.3 Test Markers

Tests use pytest markers:
- `@pytest.mark.unit` - Unit tests (fast, pure functions)
- `@pytest.mark.integration` - Integration tests (I/O, process boundaries)
- `@pytest.mark.security` - Security tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow tests (opt-in only)

---

## 7. Database Patterns

### 7.1 Database Connection

**Location**: `{module}/database/connection.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base

DATABASE_URL = "postgresql://user:pass@localhost/dbname"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 7.2 Migration Pattern

Uses Alembic for migrations:
- Migration files in `database/migrations/`
- Version control for schema changes
- Supports PostgreSQL (primary) and SQLite (testing)

---

## 8. Module-Specific Details

### 8.1 Module Categories

> **⚠️ SINGLE SOURCE OF TRUTH**: Module categorization and implementation locations are defined in **[ZeroUI Module Categories V 3.0](../architecture/ZeroUI%20Module%20Categories%20V%203.0.md)**. That document contains the complete mapping of all modules (FM/PM/EPC/CCP) to their actual implementation paths. Do not duplicate this information here.

### 8.2 Integration Adapters Module (PM-5 / M10)

**Status**: PRD exists, implementation pending
**Location**: Would be in `src/cloud_services/client-services/integration-adapters/`
**PRD**: `docs/architecture/modules/Integration_Adapters_Module_Patched.md`

**Key Requirements**:
- Unified adapter contract for external tools
- Managed lifecycle for connections (auth, webhooks, polling)
- Safe, idempotent, observable HTTP/API interactions
- Normalized events/actions for other modules
- Integration with IAM, KMS, Budgeting, ERIS

**Components**:
- Integration Registry Service (IRS)
- Adapter Runtime
- Inbound Gateway (webhooks)
- Polling/Scheduler
- Outbound Action Dispatcher
- Observability & Receipts Hooks

---

## 9. Key Technologies & Dependencies

### 9.1 Python Stack

- **Python**: 3.11+
- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **SQLAlchemy**: ORM
- **Alembic**: Migrations
- **pytest**: Testing
- **Prometheus Client**: Metrics
- **OpenTelemetry**: Tracing

### 9.2 TypeScript Stack

- **TypeScript**: Language
- **VS Code Extension API**: Extension framework
- **Node.js**: Runtime

### 9.3 Database

- **PostgreSQL**: Primary (with JSONB support)
- **SQLite**: Testing/development fallback

### 9.4 Observability

- **Prometheus**: Metrics
- **OpenTelemetry**: Distributed tracing
- **Structured Logging**: JSON logs

---

## 10. Critical Implementation Rules

### 10.1 Separation of Concerns

❌ **NEVER** put business logic in:
- VS Code Extension (Tier 1)
- Edge Agent modules (Tier 2)

✅ **ALWAYS** put business logic in:
- Cloud Services (Tier 3)

### 10.2 Data Flow

```
Tier 1 (VS Code Extension) ← Receipts ← Tier 2 (Edge Agent) ← HTTP/HTTPS ← Tier 3 (Cloud Services)
```

**One-way flow**: Tier 1 ← Tier 2 ← Tier 3

### 10.3 Tenant Isolation

- All operations MUST be tenant-scoped
- Database queries MUST filter by `tenant_id`
- Logs MUST include `tenant_id`
- Metrics MUST be tagged with `tenant_id`

### 10.4 Error Handling

- Use appropriate HTTP status codes
- Return structured error responses
- Log errors with context
- Emit metrics for error rates
- Generate ERIS receipts for failures

### 10.5 Receipt Generation

- Generate ERIS receipts for sensitive operations
- Include correlation IDs
- Link to original decision/action
- Sign receipts via KMS

---

## 11. Module Implementation Checklist

When implementing a new module:

### Tier 3 (Cloud Services)
- [ ] Create service directory in correct category (client/product/shared)
- [ ] Implement `main.py` with FastAPI app
- [ ] Implement `routes.py` (HTTP concerns only)
- [ ] Implement `services.py` (ALL business logic)
- [ ] Implement `models.py` (Pydantic models)
- [ ] Implement `database/models.py` (SQLAlchemy ORM)
- [ ] Implement `database/repositories.py` (Repository pattern)
- [ ] Implement `database/connection.py` (DB session)
- [ ] Implement `dependencies.py` (Mock clients)
- [ ] Implement `service_registry.py` (DI)
- [ ] Implement `observability/metrics.py` (Prometheus)
- [ ] Implement integration clients if needed
- [ ] Add health endpoint
- [ ] Add tests (unit, integration, security, performance)

### Tier 2 (Edge Agent)
- [ ] Only if infrastructure module (not business logic module)
- [ ] Implement `DelegationInterface`
- [ ] Register in `EdgeAgent.ts`

### Tier 1 (VS Code Extension)
- [ ] Create UI component files
- [ ] Implement `ExtensionInterface.ts`
- [ ] Implement `UIComponent.ts` (presentation only)
- [ ] Implement `UIComponentManager.ts`
- [ ] Register in `extension.ts`
- [ ] Add commands to `package.json`

---

## 12. Documentation References

### Architecture Documents
- `docs/architecture/zeroui-architecture.md` - Complete architecture (single source of truth)
- `docs/architecture/modules-mapping-and-gsmd-guide.md` - Module mappings

### Module PRDs
- `docs/architecture/modules/` - All module PRDs
- `docs/architecture/modules/Integration_Adapters_Module_Patched.md` - Integration Adapters PRD

### Contracts
- `contracts/` - OpenAPI and JSON Schema contracts
- `contracts/integration_adaptors/` - Integration Adapters contracts

---

## 13. Next Steps for New Module Implementation

1. **Read the PRD**: Understand all functional and non-functional requirements
2. **Review Similar Modules**: Study existing implementations (MMM, SIN, UBI)
3. **Design Data Model**: Define Pydantic models and SQLAlchemy models
4. **Design API**: Define routes and request/response models
5. **Implement Service Layer**: Core business logic in `services.py`
6. **Implement Repository Layer**: Database access in `repositories.py`
7. **Implement Routes**: HTTP handling in `routes.py`
8. **Add Observability**: Metrics, logging, tracing
9. **Add Tests**: Unit, integration, security, performance
10. **Document**: Update README, add docstrings

---

**End of Document**

