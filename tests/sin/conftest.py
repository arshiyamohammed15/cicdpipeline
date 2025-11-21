"""
Test fixtures and utilities for SIN module tests.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sin_module_path = project_root / "src" / "cloud-services" / "product-services" / "signal-ingestion-normalization"
sys.path.insert(0, str(sin_module_path.parent))

# Import modules using importlib with proper package setup
import importlib.util

# Create package structure
package_name = "signal_ingestion_normalization"
package = type(sys)('module')
package.__path__ = [str(sin_module_path)]
sys.modules[package_name] = package

def load_module(name, file_path):
    """Load a module from a file path with proper package setup."""
    full_name = f"{package_name}.{name}"
    spec = importlib.util.spec_from_file_location(full_name, file_path)
    module = importlib.util.module_from_spec(spec)
    # Set __package__ and __name__ for relative imports
    module.__package__ = package_name
    module.__name__ = full_name
    module.__file__ = str(file_path)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module

# Load modules in dependency order
models = load_module("models", sin_module_path / "models.py")
dependencies = load_module("dependencies", sin_module_path / "dependencies.py")
governance_mod = load_module("governance", sin_module_path / "governance.py")
producer_registry_mod = load_module("producer_registry", sin_module_path / "producer_registry.py")
validation_mod = load_module("validation", sin_module_path / "validation.py")
normalization_mod = load_module("normalization", sin_module_path / "normalization.py")
routing_mod = load_module("routing", sin_module_path / "routing.py")
deduplication_mod = load_module("deduplication", sin_module_path / "deduplication.py")
dlq_mod = load_module("dlq", sin_module_path / "dlq.py")
observability_mod = load_module("observability", sin_module_path / "observability.py")
services_mod = load_module("services", sin_module_path / "services.py")

# Extract classes and functions
SignalEnvelope = models.SignalEnvelope
SignalKind = models.SignalKind
Environment = models.Environment
ProducerRegistration = models.ProducerRegistration
Plane = models.Plane
DataContract = models.DataContract
Resource = models.Resource
RoutingClass = models.RoutingClass
ErrorCode = models.ErrorCode
IngestStatus = models.IngestStatus

MockM21IAM = dependencies.MockM21IAM
MockM32Trust = dependencies.MockM32Trust
MockM35Budgeting = dependencies.MockM35Budgeting
MockM29DataGovernance = dependencies.MockM29DataGovernance
MockM34SchemaRegistry = dependencies.MockM34SchemaRegistry
MockAPIGateway = dependencies.MockAPIGateway

ProducerRegistry = producer_registry_mod.ProducerRegistry
ProducerRegistryError = producer_registry_mod.ProducerRegistryError
ValidationEngine = validation_mod.ValidationEngine
NormalizationEngine = normalization_mod.NormalizationEngine
RoutingEngine = routing_mod.RoutingEngine
RoutingRule = routing_mod.RoutingRule
DeduplicationStore = deduplication_mod.DeduplicationStore
DLQHandler = dlq_mod.DLQHandler
MetricsRegistry = observability_mod.MetricsRegistry
StructuredLogger = observability_mod.StructuredLogger
HealthChecker = observability_mod.HealthChecker
GovernanceEnforcer = governance_mod.GovernanceEnforcer
SignalIngestionService = services_mod.SignalIngestionService


@pytest.fixture
def mock_iam():
    """Mock IAM dependency."""
    return MockM21IAM()


@pytest.fixture
def mock_trust():
    """Mock Trust dependency."""
    return MockM32Trust()


@pytest.fixture
def mock_budgeting():
    """Mock Budgeting dependency."""
    return MockM35Budgeting()


@pytest.fixture
def mock_data_governance():
    """Mock Data Governance dependency."""
    return MockM29DataGovernance()


@pytest.fixture
def mock_schema_registry():
    """Mock Schema Registry dependency."""
    return MockM34SchemaRegistry()


@pytest.fixture
def mock_api_gateway():
    """Mock API Gateway dependency."""
    return MockAPIGateway()


@pytest.fixture
def producer_registry(mock_schema_registry, mock_budgeting):
    """Producer registry instance."""
    return ProducerRegistry(mock_schema_registry, mock_budgeting)


@pytest.fixture
def governance_enforcer(mock_data_governance):
    """Governance enforcer instance."""
    return GovernanceEnforcer(mock_data_governance)


@pytest.fixture
def validation_engine(producer_registry, governance_enforcer, mock_schema_registry):
    """Validation engine instance."""
    return ValidationEngine(producer_registry, governance_enforcer, mock_schema_registry)


@pytest.fixture
def normalization_engine(mock_schema_registry):
    """Normalization engine instance."""
    return NormalizationEngine(mock_schema_registry)


@pytest.fixture
def routing_engine():
    """Routing engine instance."""
    return RoutingEngine()


@pytest.fixture
def deduplication_store():
    """Deduplication store instance."""
    return DeduplicationStore()


@pytest.fixture
def dlq_handler(mock_trust):
    """DLQ handler instance."""
    return DLQHandler(mock_trust)


@pytest.fixture
def metrics_registry():
    """Metrics registry instance."""
    return MetricsRegistry()


@pytest.fixture
def structured_logger():
    """Structured logger instance."""
    return StructuredLogger()


@pytest.fixture
def health_checker():
    """Health checker instance."""
    return HealthChecker()


@pytest.fixture
def ingestion_service(
    producer_registry, validation_engine, normalization_engine, routing_engine,
    deduplication_store, dlq_handler, metrics_registry, structured_logger, governance_enforcer
):
    """Signal ingestion service instance."""
    return SignalIngestionService(
        producer_registry,
        validation_engine,
        normalization_engine,
        routing_engine,
        deduplication_store,
        dlq_handler,
        metrics_registry,
        structured_logger,
        governance_enforcer
    )


@pytest.fixture
def sample_signal():
    """Sample SignalEnvelope for testing."""
    return SignalEnvelope(
        signal_id="signal_123",
        tenant_id="tenant_1",
        environment=Environment.DEV,
        producer_id="producer_1",
        signal_kind=SignalKind.EVENT,
        signal_type="pr_opened",
        occurred_at=datetime.utcnow(),
        ingested_at=datetime.utcnow(),
        payload={
            "event_name": "pr_opened",
            "severity": "info",
            "pr_id": 123
        },
        schema_version="1.0.0"
    )


@pytest.fixture
def sample_producer():
    """Sample ProducerRegistration for testing."""
    return ProducerRegistration(
        producer_id="producer_1",
        name="Test Producer",
        plane=Plane.EDGE,
        owner="test_owner",
        allowed_signal_kinds=[SignalKind.EVENT, SignalKind.METRIC],
        allowed_signal_types=["pr_opened", "test_failed"],
        contract_versions={"pr_opened": "1.0.0", "test_failed": "1.0.0"}
    )


@pytest.fixture
def sample_contract():
    """Sample DataContract for testing."""
    return DataContract(
        signal_type="pr_opened",
        contract_version="1.0.0",
        required_fields=["event_name", "pr_id"],
        optional_fields=["severity"],
        pii_flags={"pr_id": False},
        secrets_flags={}
    )


@pytest.fixture
def registered_producer(producer_registry, sample_producer, sample_contract, mock_schema_registry):
    """Register a producer and contract for testing."""
    # Register contract in schema registry
    mock_schema_registry.register_contract(
        sample_contract.signal_type,
        sample_contract.contract_version,
        sample_contract.model_dump()
    )

    # Register test_failed contract as well (since sample_producer allows it)
    test_failed_contract = DataContract(
        signal_type="test_failed",
        contract_version="1.0.0",
        required_fields=["event_name"],
        optional_fields=[]
    )
    mock_schema_registry.register_contract(
        test_failed_contract.signal_type,
        test_failed_contract.contract_version,
        test_failed_contract.model_dump()
    )

    # Register producer
    producer_registry.register_producer(sample_producer)
    return sample_producer
