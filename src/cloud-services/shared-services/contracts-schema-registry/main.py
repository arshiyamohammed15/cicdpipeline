"""
Main FastAPI application for Contracts & Schema Registry (M34).

What: FastAPI application entry point with middleware, routes, and health checks per PRD v1.2.0
Why: Orchestrates service components, provides HTTP server for registry operations
Reads/Writes: Reads configuration, writes HTTP responses (no file I/O)
Contracts: FastAPI application contract, CORS middleware, request logging middleware
Risks: Service unavailability if dependencies fail, CORS misconfiguration, middleware errors
"""

import json
import logging
import os
import socket
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .models import HealthResponse
from .middleware import (
    RequestLoggingMiddleware, RateLimitingMiddleware,
    TenantIsolationMiddleware, IdempotencyMiddleware
)
from .database.connection import get_engine, health_check
from .database.models import Base

# Service metadata per Rule 62
SERVICE_NAME = "contracts-schema-registry"
SERVICE_VERSION = "1.2.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Configure logging per Rule 4083 - JSON format
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Starting Contracts & Schema Registry service...")

    # Initialize database
    try:
        engine = get_engine()
        # Create tables if using mock (SQLite)
        if engine.url.drivername == "sqlite":
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created (SQLite mock mode)")
        else:
            logger.info("Connected to PostgreSQL database")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Health check
    db_health = health_check()
    if db_health["connected"]:
        logger.info("Service ready")
    else:
        logger.warning("Service started but database not connected")

    yield

    # Shutdown
    logger.info("Shutting down Contracts & Schema Registry service...")


app = FastAPI(
    title="ZeroUI Contracts & Schema Registry",
    version="1.2.0",
    description="Centralized schema management, validation, and contract enforcement for ZeroUI ecosystem (Module M34)",
    lifespan=lifespan
)

# Request logging middleware (must be first to log all requests per Rule 173)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware per PRD
app.add_middleware(RateLimitingMiddleware)

# Tenant isolation middleware per PRD
app.add_middleware(TenantIsolationMiddleware)

# Idempotency middleware per PRD
app.add_middleware(IdempotencyMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/registry/v1", tags=["contracts-schema-registry"])


@app.get("/health", response_model=HealthResponse)
def health_check_endpoint() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    checks = [
        {"name": "service", "status": "pass", "detail": "Service is running"},
    ]

    # Check database
    db_health = health_check()
    checks.append({
        "name": "database",
        "status": "pass" if db_health["connected"] else "fail",
        "detail": db_health.get("error", "Database connected")
    })

    # Determine overall status
    status = "healthy"
    if any(check["status"] == "fail" for check in checks):
        status = "unhealthy"
    elif any(check["status"] == "warn" for check in checks):
        status = "degraded"

    return HealthResponse(
        status=status,
        timestamp=datetime.utcnow().isoformat(),
        checks=checks
    )
