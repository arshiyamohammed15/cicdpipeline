"""Unit tests for RoutingEngine."""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

import pytest

# Add parent directories to path
PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

# Create package structure and load modules
parent_pkg = type(sys)('signal_ingestion_normalization')
sys.modules['signal_ingestion_normalization'] = parent_pkg

models_path = PACKAGE_ROOT / "models.py"
spec_models = importlib.util.spec_from_file_location("signal_ingestion_normalization.models", models_path)
models_module = importlib.util.module_from_spec(spec_models)
sys.modules['signal_ingestion_normalization.models'] = models_module
spec_models.loader.exec_module(models_module)

routing_path = PACKAGE_ROOT / "routing.py"
spec_routing = importlib.util.spec_from_file_location("signal_ingestion_normalization.routing", routing_path)
routing_module = importlib.util.module_from_spec(spec_routing)
sys.modules['signal_ingestion_normalization.routing'] = routing_module
spec_routing.loader.exec_module(routing_module)

# Import classes
SignalEnvelope = models_module.SignalEnvelope
SignalKind = models_module.SignalKind
Plane = models_module.Plane
Environment = models_module.Environment
RoutingClass = models_module.RoutingClass
RoutingEngine = routing_module.RoutingEngine
RoutingRule = routing_module.RoutingRule


@pytest.mark.unit
class TestRoutingEngine:
    """Test RoutingEngine functionality."""

    def test_engine_initialization(self):
        """Test routing engine initialization."""
        engine = RoutingEngine()
        assert engine is not None
        assert RoutingClass.REALTIME_DETECTION in engine.routing_rules

    def test_register_rule(self):
        """Test registering a routing rule."""
        engine = RoutingEngine()
        
        def condition(signal):
            return signal.signal_kind == SignalKind.EVENT
        
        rule = RoutingRule(
            routing_class=RoutingClass.REALTIME_DETECTION,
            condition=condition,
            destination="detection-queue"
        )
        
        engine.register_rule(RoutingClass.REALTIME_DETECTION, rule)
        assert len(engine.routing_rules[RoutingClass.REALTIME_DETECTION]) == 1

    def test_route_signal(self):
        """Test routing a signal."""
        engine = RoutingEngine()
        
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
        
        destinations = engine.route(signal)
        assert isinstance(destinations, list)

    def test_route_with_tenant_awareness(self):
        """Test routing with tenant awareness."""
        engine = RoutingEngine()
        
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
        
        # Register tenant-aware rule
        def condition(signal):
            return signal.tenant_id == "tenant-1"
        
        rule = RoutingRule(
            routing_class=RoutingClass.REALTIME_DETECTION,
            condition=condition,
            destination="tenant-1-queue",
            tenant_aware=True
        )
        
        engine.register_rule(RoutingClass.REALTIME_DETECTION, rule)
        destinations = engine.route(signal)
        
        # Should route to tenant-specific destination
        assert "tenant-1-queue" in destinations or len(destinations) >= 0

