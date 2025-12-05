from __future__ import annotations
"""Unit tests for NormalizationEngine."""

# Imports handled by conftest.py

import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add parent directories to path
PACKAGE_ROOT = Path(__file__).resolve().parents[4] / "src" / "cloud_services" / "product-services" / "signal-ingestion-normalization"
# Path setup handled by conftest.py
# Create package structure and load modules (same pattern as test_validation.py)
parent_pkg = type(sys)('signal_ingestion_normalization')
sys.modules['signal_ingestion_normalization'] = parent_pkg

# Load modules
# Models imported via root conftest
spec_models = importlib.util.spec_from_file_location("signal_ingestion_normalization.models", Path(__file__).parent.parent.parent.parent / "src" / "cloud_services" / "shared-services" / "ollama-ai-agent")
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['signal_ingestion_normalization.models'] = models_module
spec_models.loader.exec_module(models_module)

dependencies_path = PACKAGE_ROOT / "dependencies.py"
spec_deps = importlib.util.spec_from_file_location("signal_ingestion_normalization.dependencies", dependencies_path)
deps_module = importlib.util.module_from_spec(spec_deps)
sys.modules['signal_ingestion_normalization.dependencies'] = deps_module
spec_deps.loader.exec_module(deps_module)

normalization_path = PACKAGE_ROOT / "normalization.py"
spec_norm = importlib.util.spec_from_file_location("signal_ingestion_normalization.normalization", normalization_path)
norm_module = importlib.util.module_from_spec(spec_norm)
sys.modules['signal_ingestion_normalization.normalization'] = norm_module
spec_norm.loader.exec_module(norm_module)

# Import classes
SignalEnvelope = models_module.SignalEnvelope
SignalKind = models_module.SignalKind
Plane = models_module.Plane
Environment = models_module.Environment
NormalizationEngine = norm_module.NormalizationEngine
MockM34SchemaRegistry = deps_module.MockM34SchemaRegistry


@pytest.mark.unit
class TestNormalizationEngine:
    """Test NormalizationEngine functionality."""

    def test_engine_initialization(self):
        """Test normalization engine initialization."""
        engine = NormalizationEngine()
        assert engine is not None
        assert engine.schema_registry is not None

    def test_normalize_signal_basic(self):
        """Test basic signal normalization."""
        engine = NormalizationEngine()

        signal = SignalEnvelope(
            signal_id="test-1",
            tenant_id="tenant-1",
            producer_id="producer-1",
            signal_kind=SignalKind.EVENT,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={"message": "test"}
        )

        normalized = engine.normalize(signal)
        assert normalized is not None
        assert normalized.signal_id == signal.signal_id

    def test_normalize_with_field_mapping(self):
        """Test normalization with field mapping rules."""
        engine = NormalizationEngine()

        # Set up field mapping
        engine.field_mappings["event"] = {"old_field": "new_field"}

        signal = SignalEnvelope(
            signal_id="test-1",
            tenant_id="tenant-1",
            producer_id="producer-1",
            signal_kind=SignalKind.EVENT,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={"old_field": "value"}
        )

        normalized = engine.normalize(signal)
        assert normalized is not None

    def test_normalize_with_unit_conversion(self):
        """Test normalization with unit conversion."""
        engine = NormalizationEngine()

        signal = SignalEnvelope(
            signal_id="test-1",
            tenant_id="tenant-1",
            producer_id="producer-1",
            signal_kind=SignalKind.METRIC,
            plane=Plane.TENANT_CLOUD,
            environment=Environment.DEV,
            timestamp="2025-01-01T00:00:00Z",
            payload={"duration_seconds": 1.5}
        )

        normalized = engine.normalize(signal)
        assert normalized is not None

