"""
Main FastAPI application for Key Management Service (KMS).

What: FastAPI application entry point with middleware, routes, and health checks per KMS spec v0.1.0
Why: Orchestrates service components, provides HTTP server for KMS operations
Reads/Writes: Reads configuration, writes HTTP responses (no file I/O)
Contracts: FastAPI application contract, CORS middleware, request logging middleware, mTLS validation
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
from .middleware import RequestLoggingMiddleware, RateLimitingMiddleware, mTLSValidationMiddleware, JWTValidationMiddleware
from .dependencies import MockM27EvidenceLedger, MockM29DataPlane, MockM32TrustPlane, MockM21IAM

# Service metadata per Rule 62
SERVICE_NAME = "key-management-service"
SERVICE_VERSION = "0.1.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Configure logging per Rule 4083 - JSON format
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

# Initialize mock dependencies
evidence_ledger = MockM27EvidenceLedger()
data_plane = MockM29DataPlane()
trust_plane = MockM32TrustPlane()
iam = MockM21IAM()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup/shutdown events.

    Per KMS spec: Key rotation initialization, trust store initialization.
    """
    logger.info("Starting Key Management Service...")
    logger.info(f"Service: {SERVICE_NAME}, Version: {SERVICE_VERSION}")

    # Initialize trust anchors for development
    if SERVICE_ENV == "development":
        trust_plane.add_trust_anchor("internal-ca-dev", {
            "type": "internal_ca",
            "certificate": b"mock-certificate",
            "version": "1.0"
        })
        logger.info("Initialized development trust anchors")

    yield

    logger.info("Shutting down Key Management Service...")


app = FastAPI(
    title="ZeroUI Key Management Service",
    version="0.1.0",
    description="Cryptographic foundation and trust anchor for ZeroUI ecosystem (KMS Module M33)",
    lifespan=lifespan
)

# Request logging middleware (must be first to log all requests per Rule 173)
app.add_middleware(RequestLoggingMiddleware)

# Rate limiting middleware per KMS spec
app.add_middleware(RateLimitingMiddleware)

# mTLS validation middleware per KMS spec
app.add_middleware(mTLSValidationMiddleware, trust_plane=trust_plane)

# JWT validation middleware per KMS spec (optional but recommended)
app.add_middleware(JWTValidationMiddleware, iam=iam)

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
app.include_router(router, prefix="/kms/v1", tags=["key-management"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    checks = [
        {"name": "service", "status": "pass", "detail": "Service is running"},
        {"name": "hsm", "status": "pass", "detail": "HSM connectivity check (mock)"},
        {"name": "storage", "status": "pass", "detail": "Metadata storage available (mock)"},
        {"name": "trust_store", "status": "pass", "detail": "Trust store available (mock)"}
    ]

    # Determine overall status
    status = "healthy"
    if any(check["status"] == "fail" for check in checks):
        status = "unhealthy"
    elif any(check["status"] == "warn" for check in checks):
        status = "degraded"

    return HealthResponse(
        status=status,
        checks=checks
    )
