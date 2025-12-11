"""FastAPI application entrypoint for the SIN stub service."""
from __future__ import annotations

from fastapi import FastAPI

from .dependencies import (
    MockM21IAM,
    MockM32Trust,
    MockM35Budgeting,
    MockM29DataGovernance,
    MockM34SchemaRegistry,
    MockAPIGateway,
)
from .producer_registry import ProducerRegistry
from .validation import ValidationEngine
from .normalization import NormalizationEngine
from .routing import RoutingEngine
from .deduplication import DeduplicationStore
from .dlq import DLQHandler
from .observability import MetricsRegistry, StructuredLogger, HealthChecker
from .governance import GovernanceEnforcer
from .services import SignalIngestionService
from .routes import router

_iam: MockM21IAM | None = None
_schema_registry: MockM34SchemaRegistry | None = None
_producer_registry: ProducerRegistry | None = None
_ingestion_service: SignalIngestionService | None = None
_routing_engine: RoutingEngine | None = None
_health_checker: HealthChecker | None = None


def initialize_services() -> None:
    global _iam, _schema_registry, _producer_registry, _ingestion_service, _routing_engine, _health_checker
    _iam = MockM21IAM()
    _schema_registry = MockM34SchemaRegistry()
    _producer_registry = ProducerRegistry(_schema_registry, MockM35Budgeting())
    governance = GovernanceEnforcer(MockM29DataGovernance())
    _routing_engine = RoutingEngine()
    _health_checker = HealthChecker()
    ingestion = SignalIngestionService(
        _producer_registry,
        ValidationEngine(_producer_registry, governance, _schema_registry),
        NormalizationEngine(_schema_registry),
        _routing_engine,
        DeduplicationStore(),
        DLQHandler(MockM32Trust()),
        MetricsRegistry(),
        StructuredLogger(),
        governance,
    )
    _ingestion_service = ingestion


def create_app() -> FastAPI:
    initialize_services()
    app = FastAPI(title="Signal Ingestion Normalization", version="1.0.0")

    # attach shared instances to application state for dependency access
    app.state.iam = _iam
    app.state.schema_registry = _schema_registry
    app.state.producer_registry = _producer_registry
    app.state.ingestion_service = _ingestion_service
    app.state.health_checker = _health_checker
    app.state.dlq_handler = _ingestion_service.dlq_handler

    app.include_router(router)
    return app


app = create_app()


def get_iam_instance() -> MockM21IAM:
    return _iam  # type: ignore[return-value]


def get_schema_registry() -> MockM34SchemaRegistry:
    return _schema_registry  # type: ignore[return-value]


def get_routing_engine() -> RoutingEngine:
    return _routing_engine  # type: ignore[return-value]
