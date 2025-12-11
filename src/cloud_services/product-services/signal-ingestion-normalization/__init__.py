"""Stub implementation of the Signal Ingestion & Normalization service for tests."""

from .models import (
    SignalEnvelope,
    SignalKind,
    Environment,
    Plane,
    DataContract,
    ProducerRegistration,
    RoutingClass,
    RoutingRule,
    IngestStatus,
)
from .dependencies import (
    MockM21IAM,
    MockM32Trust,
    MockM35Budgeting,
    MockM29DataGovernance,
    MockM34SchemaRegistry,
    MockAPIGateway,
)
from .producer_registry import ProducerRegistry, ProducerRegistryError
from .validation import ValidationEngine
from .normalization import NormalizationEngine
from .routing import RoutingEngine
from .deduplication import DeduplicationStore
from .dlq import DLQHandler
from .observability import MetricsRegistry, StructuredLogger, HealthChecker
from .governance import GovernanceEnforcer
from .services import SignalIngestionService

__all__ = [
    "SignalEnvelope",
    "SignalKind",
    "Environment",
    "Plane",
    "DataContract",
    "ProducerRegistration",
    "RoutingClass",
    "RoutingRule",
    "IngestStatus",
    "MockM21IAM",
    "MockM32Trust",
    "MockM35Budgeting",
    "MockM29DataGovernance",
    "MockM34SchemaRegistry",
    "MockAPIGateway",
    "ProducerRegistry",
    "ProducerRegistryError",
    "ValidationEngine",
    "NormalizationEngine",
    "RoutingEngine",
    "DeduplicationStore",
    "DLQHandler",
    "MetricsRegistry",
    "StructuredLogger",
    "HealthChecker",
    "GovernanceEnforcer",
    "SignalIngestionService",
    "create_app",
    "app",
]

try:
    from .main import create_app, app  # type: ignore
except Exception:  # pragma: no cover - during partial imports
    create_app = None  # type: ignore
    app = None  # type: ignore
