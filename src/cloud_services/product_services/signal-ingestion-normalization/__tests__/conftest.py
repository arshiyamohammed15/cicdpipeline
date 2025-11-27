"""Pytest fixtures for Signal Ingestion & Normalization tests."""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

# Add parent directories to path for imports
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

# Create parent package structure
parent_pkg = type(sys)('signal_ingestion_normalization')
sys.modules['signal_ingestion_normalization'] = parent_pkg

# Load modules in dependency order
modules_to_load = [
    ("models", "models.py"),
    ("dependencies", "dependencies.py"),
    ("producer_registry", "producer_registry.py"),
    ("governance", "governance.py"),
    ("validation", "validation.py"),
    ("normalization", "normalization.py"),
    ("routing", "routing.py"),
    ("deduplication", "deduplication.py"),
    ("dlq", "dlq.py"),
    ("observability", "observability.py"),
    ("services", "services.py"),
    ("routes", "routes.py"),
    ("main", "main.py"),
]

for module_name, filename in modules_to_load:
    module_path = PACKAGE_ROOT / filename
    if module_path.exists():
        spec = importlib.util.spec_from_file_location(
            f"signal_ingestion_normalization.{module_name}",
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"signal_ingestion_normalization.{module_name}"] = module
        spec.loader.exec_module(module)

# Import main app
main_module = sys.modules['signal_ingestion_normalization.main']
app = main_module.create_app()


@pytest.fixture
def test_client():
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_signal_envelope():
    """Create a mock SignalEnvelope for testing."""
    from signal_ingestion_normalization.models import SignalEnvelope, SignalKind, Plane, Environment
    return SignalEnvelope(
        signal_id="test-signal-1",
        tenant_id="tenant-1",
        producer_id="producer-1",
        signal_kind=SignalKind.EVENT,
        plane=Plane.TENANT_CLOUD,
        environment=Environment.DEV,
        timestamp="2025-01-01T00:00:00Z",
        payload={"message": "test signal"}
    )


@pytest.fixture
def mock_producer_registry():
    """Create a mock ProducerRegistry."""
    registry = Mock()
    registry.is_registered.return_value = True
    registry.get_producer.return_value = {
        "producer_id": "producer-1",
        "name": "Test Producer",
        "allowed_signal_types": ["event", "metric"]
    }
    return registry


@pytest.fixture
def mock_validation_engine():
    """Create a mock ValidationEngine."""
    engine = Mock()
    engine.validate_structure.return_value = (True, None)
    engine.validate_governance.return_value = (True, None)
    engine.coerce_recoverable_errors.return_value = ([], [])
    return engine


@pytest.fixture
def mock_normalization_engine():
    """Create a mock NormalizationEngine."""
    engine = Mock()
    engine.normalize.return_value = Mock()
    return engine


@pytest.fixture
def mock_routing_engine():
    """Create a mock RoutingEngine."""
    engine = Mock()
    engine.route.return_value = ["destination-1"]
    return engine

