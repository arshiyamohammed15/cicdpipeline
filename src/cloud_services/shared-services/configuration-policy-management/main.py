"""
Main FastAPI application for Configuration & Policy Management (M23).

What: FastAPI application entry point with middleware, routes, and health checks per PRD v1.1.0
Why: Orchestrates service components, provides HTTP server for M23 operations
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
from .middleware import RequestLoggingMiddleware, RateLimitingMiddleware

# Service metadata per Rule 62
SERVICE_NAME = "configuration-policy-management"
SERVICE_VERSION = "1.1.0"
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
    Lifespan context manager for FastAPI startup/shutdown events.

    Per PRD: Database connection initialization, service startup.
    """
    logger.info("Starting Configuration & Policy Management service...")
    logger.info(f"Service: {SERVICE_NAME}, Version: {SERVICE_VERSION}")

    # Initialize database connection
    from .database.connection import get_engine
    engine = get_engine()
    logger.info("Database connection initialized")

    yield

    logger.info("Shutting down Configuration & Policy Management service...")


app = FastAPI(
    title="ZeroUI Configuration & Policy Management Service",
    version="1.1.0",
    description="Enterprise-grade policy lifecycle management, configuration enforcement, and gold standards compliance (M23)",
    lifespan=lifespan
)

# Request logging middleware (must be first to log all requests per Rule 173)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware per PRD
app.add_middleware(RateLimitingMiddleware)

# CORS middleware - configure via CORS_ORIGINS environment variable
# Production validation: reject "*" in production
cors_origins_env = os.getenv("CORS_ORIGINS", "*" if SERVICE_ENV == "development" else "")
cors_origins = [origin.strip() for origin in cors_origins_env.split(",")] if cors_origins_env else []

# Production CORS validation: reject wildcard in production
if SERVICE_ENV == "production":
    if "*" in cors_origins or not cors_origins:
        logger.error("CORS_ORIGINS must be set to specific origins in production. Wildcard '*' is not allowed.")
        raise ValueError("CORS_ORIGINS must be set to specific origins in production. Wildcard '*' is not allowed.")
elif not cors_origins and SERVICE_ENV != "development":
    logger.warning("CORS_ORIGINS not set in non-development environment - CORS disabled. Set CORS_ORIGINS environment variable.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else (["*"] if SERVICE_ENV == "development" else []),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/policy/v1", tags=["configuration-policy-management"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        version=SERVICE_VERSION,
        timestamp=datetime.utcnow().isoformat()
    )
