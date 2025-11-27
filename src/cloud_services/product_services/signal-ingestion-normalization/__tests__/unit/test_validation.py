"""Unit tests for ValidationEngine."""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add parent directories to path
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

# Create package structure
parent_pkg = type(sys)('signal_ingestion_normalization')
sys.modules['signal_ingestion_normalization'] = parent_pkg

# Load required modules
models_path = PACKAGE_ROOT / "models.py"
spec_models = importlib.util.spec_from_file_location("signal_ingestion_normalization.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['signal_ingestion_normalization.models'] = models_module
spec_models.loader.exec_module(models_module)

producer_registry_path = PACKAGE_ROOT / "producer_registry.py"
spec_producer = importlib.util.spec_from_file_location("signal_ingestion_normalization.producer_registry", producer_registry_path)
producer_module = importlib.util.module_from_spec(spec_producer)
sys.modules['signal_ingestion_normalization.producer_registry'] = producer_module
spec_producer.loader.exec_module(producer_module)

governance_path = PACKAGE_ROOT / "governance.py"
spec_governance = importlib.util.spec_from_file_location("signal_ingestion_normalization.governance", governance_path)
governance_module = importlib.util.module_from_spec(spec_governance)
sys.modules['signal_ingestion_normalization.governance'] = governance_module
spec_governance.loader.exec_module(governance_module)

dependencies_path = PACKAGE_ROOT / "dependencies.py"
spec_deps = importlib.util.spec_from_file_location("signal_ingestion_normalization.dependencies", dependencies_path)
deps_module = importlib.util.module_from_spec(spec_deps)
sys.modules['signal_ingestion_normalization.dependencies'] = deps_module
spec_deps.loader.exec_module(deps_module)

validation_path = PACKAGE_ROOT / "validation.py"
spec_validation = importlib.util.spec_from_file_location("signal_ingestion_normalization.validation", validation_path)
validation_module = importlib.util.module_from_spec(spec_validation)
sys.modules['signal_ingestion_normalization.validation'] = validation_module
spec_validation.loader.exec_module(validation_module)

# Import classes
SignalEnvelope = models_module.SignalEnvelope
SignalKind = models_module.SignalKind
Plane = models_module.Plane
Environment = models_module.Environment
ErrorCode = models_module.ErrorCode
ValidationEngine = validation_module.ValidationEngine
ProducerRegistry = producer_module.ProducerRegistry
GovernanceEnforcer = governance_module.GovernanceEnforcer


@pytest.mark.unit
class TestValidationEngine:
    """Test ValidationEngine functionality."""

    def test_engine_initialization(self):
        """Test validation engine initialization."""
        producer_registry = Mock(spec=ProducerRegistry)
        governance_enforcer = Mock(spec=GovernanceEnforcer)
        engine = ValidationEngine(producer_registry, governance_enforcer)
        assert engine is not None
        assert engine.producer_registry == producer_registry
        assert engine.governance_enforcer == governance_enforcer

    def test_validate_structure_valid_signal(self):
        """Test structure validation with valid signal."""
        producer_registry = Mock(spec=ProducerRegistry)
        governance_enforcer = Mock(spec=GovernanceEnforcer)
        engine = ValidationEngine(producer_registry, governance_enforcer)

        signal = SignalEnvelope(
            signal_id="test-1",
            tenant_id="tenant-1",
            producer_id="producer-1",
            signal_kind=SignalKind.EVENT,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={}
        )

        is_valid, error = engine.validate_structure(signal)
        assert is_valid is True
        assert error is None

    def test_validate_structure_missing_signal_id(self):
        """Test structure validation with missing signal_id."""
        producer_registry = Mock(spec=ProducerRegistry)
        governance_enforcer = Mock(spec=GovernanceEnforcer)
        engine = ValidationEngine(producer_registry, governance_enforcer)

        signal = SignalEnvelope(
            signal_id="",  # Empty signal_id
            tenant_id="tenant-1",
            producer_id="producer-1",
            signal_kind=SignalKind.EVENT,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={}
        )

        is_valid, error = engine.validate_structure(signal)
        assert is_valid is False
        assert error is not None
        assert error.error_code == ErrorCode.SCHEMA_VIOLATION

    def test_validate_structure_missing_tenant_id(self):
        """Test structure validation with missing tenant_id."""
        producer_registry = Mock(spec=ProducerRegistry)
        governance_enforcer = Mock(spec=GovernanceEnforcer)
        engine = ValidationEngine(producer_registry, governance_enforcer)

        signal = SignalEnvelope(
            signal_id="test-1",
            tenant_id="",  # Empty tenant_id
            producer_id="producer-1",
            signal_kind=SignalKind.EVENT,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={}
        )

        is_valid, error = engine.validate_structure(signal)
        assert is_valid is False
        assert error is not None
        assert error.error_code == ErrorCode.SCHEMA_VIOLATION

    def test_validate_producer_registered(self):
        """Test producer validation when producer is registered."""
        producer_registry = Mock(spec=ProducerRegistry)
        producer_registry.is_registered.return_value = True
        governance_enforcer = Mock(spec=GovernanceEnforcer)
        engine = ValidationEngine(producer_registry, governance_enforcer)

        signal = SignalEnvelope(
            signal_id="test-1",
            tenant_id="tenant-1",
            producer_id="producer-1",
            signal_kind=SignalKind.EVENT,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={}
        )

        is_valid, error = engine.validate_producer(signal)
        assert is_valid is True
        assert error is None

    def test_validate_producer_not_registered(self):
        """Test producer validation when producer is not registered."""
        producer_registry = Mock(spec=ProducerRegistry)
        producer_registry.is_registered.return_value = False
        governance_enforcer = Mock(spec=GovernanceEnforcer)
        engine = ValidationEngine(producer_registry, governance_enforcer)

        signal = SignalEnvelope(
            signal_id="test-1",
            tenant_id="tenant-1",
            producer_id="unregistered-producer",
            signal_kind=SignalKind.EVENT,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={}
        )

        is_valid, error = engine.validate_producer(signal)
        assert is_valid is False
        assert error is not None
        assert error.error_code == ErrorCode.PRODUCER_NOT_REGISTERED

