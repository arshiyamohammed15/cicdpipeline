"""
Main application for Deployment & Infrastructure (EPC-8).

What: Deployment automation and infrastructure management service
Why: Provides standardized deployment processes and infrastructure management
Reads/Writes: Reads configuration, writes deployment artifacts
Contracts: Deployment API contract
Risks: Deployment failures, infrastructure misconfiguration
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
SERVICE_NAME = "deployment-infrastructure"
SERVICE_VERSION = "1.0.0"
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

    Per deployment API contract: Service initialization.
    """
    logger.info("Starting Deployment & Infrastructure service...")
    logger.info(f"Service: {SERVICE_NAME}, Version: {SERVICE_VERSION}")

    yield

    logger.info("Shutting down Deployment & Infrastructure service...")


app = FastAPI(
    title="ZeroUI Deployment & Infrastructure Service",
    version="1.0.0",
    description="Deployment automation and infrastructure management (EPC-8)",
    lifespan=lifespan
)

# Request logging middleware (must be first to log all requests per Rule 173)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware per deployment API contract
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
app.include_router(router, prefix="/deploy/v1", tags=["deployment-infrastructure"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        environment=SERVICE_ENV,
        timestamp=datetime.utcnow()
    )
