"""
FastAPI application for Signal Ingestion & Normalization (SIN) Module.

What: FastAPI app setup with CORS, health endpoints, router registration
Why: Expose SIN functionality via REST API
Reads/Writes: HTTP request/response handling
Contracts: PRD §5 Data & API Contracts
Risks: CORS configuration, authentication middleware
"""

import logging
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .dependencies import (
    MockM21IAM, MockM32Trust, MockM35Budgeting, MockM29DataGovernance,
    MockM34SchemaRegistry, MockAPIGateway
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

logger = logging.getLogger(__name__)

# Global service instances (in production, use dependency injection)
_ingestion_service: Optional[SignalIngestionService] = None
_producer_registry: Optional[ProducerRegistry] = None
_dlq_handler: Optional[DLQHandler] = None
_health_checker: Optional[HealthChecker] = None
_iam: Optional[MockM21IAM] = None


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="Signal Ingestion & Normalization API",
        description="API for ingesting, validating, normalizing, and routing signals",
        version="1.0.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, configure appropriately
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(router)

    # Initialize services
    initialize_services()

    return app


def initialize_services() -> None:
    """Initialize global service instances."""
    global _ingestion_service, _producer_registry, _dlq_handler, _health_checker, _iam
    
    # Don't reinitialize if already initialized
    if _iam is not None:
        return

    # Initialize dependencies
    _iam = MockM21IAM()
    iam = _iam
    trust = MockM32Trust()
    budgeting = MockM35Budgeting()
    data_governance = MockM29DataGovernance()
    schema_registry = MockM34SchemaRegistry()
    api_gateway = MockAPIGateway()

    # Initialize components
    _producer_registry = ProducerRegistry(schema_registry, budgeting)
    governance_enforcer = GovernanceEnforcer(data_governance)
    validation_engine = ValidationEngine(_producer_registry, governance_enforcer, schema_registry)
    normalization_engine = NormalizationEngine(schema_registry)
    routing_engine = RoutingEngine()
    deduplication_store = DeduplicationStore()
    _dlq_handler = DLQHandler(trust)
    metrics_registry = MetricsRegistry()
    structured_logger = StructuredLogger()
    _health_checker = HealthChecker()

    # Initialize main service
    _ingestion_service = SignalIngestionService(
        _producer_registry,
        validation_engine,
        normalization_engine,
        routing_engine,
        deduplication_store,
        _dlq_handler,
        metrics_registry,
        structured_logger,
        governance_enforcer
    )

    logger.info("SIN services initialized")


def get_ingestion_service() -> SignalIngestionService:
    """Get ingestion service instance."""
    global _ingestion_service
    if _ingestion_service is None:
        initialize_services()
    return _ingestion_service


def get_producer_registry() -> ProducerRegistry:
    """Get producer registry instance."""
    global _producer_registry
    if _producer_registry is None:
        initialize_services()
    return _producer_registry


def get_dlq_handler() -> DLQHandler:
    """Get DLQ handler instance."""
    global _dlq_handler
    if _dlq_handler is None:
        initialize_services()
    return _dlq_handler


def get_health_checker() -> HealthChecker:
    """Get health checker instance."""
    global _health_checker
    if _health_checker is None:
        initialize_services()
    return _health_checker


def get_iam_instance() -> MockM21IAM:
    """Get IAM instance."""
    global _iam
    if _iam is None:
        initialize_services()
    return _iam


# Create app instance
app = create_app()

