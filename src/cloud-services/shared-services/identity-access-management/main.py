"""
Main FastAPI application for Identity & Access Management (IAM) service.

What: FastAPI application entry point with middleware, routes, and health checks per IAM spec v1.1.0
Why: Orchestrates service components, provides HTTP server for IAM operations
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
from .middleware import RequestLoggingMiddleware, RateLimitingMiddleware, IdempotencyMiddleware

# Service metadata per Rule 62
SERVICE_NAME = "identity-access-management"
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
    
    Per IAM spec section 10: Key rotation, policy store initialization.
    """
    logger.info("Starting Identity & Access Management service...")
    logger.info(f"Service: {SERVICE_NAME}, Version: {SERVICE_VERSION}")
    
    yield
    
    logger.info("Shutting down Identity & Access Management service...")


app = FastAPI(
    title="ZeroUI Identity & Access Management Service",
    version="1.1.0",
    description="Authentication and authorization gatekeeper for ZeroUI ecosystem (IAM Module M21)",
    lifespan=lifespan
)

# Request logging middleware (must be first to log all requests per Rule 173)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware per IAM spec section 6
app.add_middleware(RateLimitingMiddleware)

# Idempotency middleware per IAM spec section 6
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
app.include_router(router, prefix="/iam/v1", tags=["identity-access-management"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )

