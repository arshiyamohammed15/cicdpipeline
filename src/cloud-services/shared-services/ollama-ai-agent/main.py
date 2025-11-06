"""
Main FastAPI application for Ollama AI Agent service.

What: FastAPI application entry point with middleware, routes, and health checks
Why: Orchestrates service components, provides HTTP server for LLM prompt processing
Reads/Writes: Reads configuration, writes HTTP responses (no file I/O)
Contracts: FastAPI application contract, CORS middleware, request logging middleware
Risks: Service unavailability if Ollama not running, CORS misconfiguration, middleware errors
"""

import json
import logging
import os
import socket
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .models import HealthResponse
from .middleware import RequestLoggingMiddleware

# Service metadata per Rule 62
SERVICE_NAME = "ollama-ai-agent"
SERVICE_VERSION = "2.0.0"
SERVICE_ENV = os.getenv("ENVIRONMENT", "development")
SERVICE_HOST = socket.gethostname()

# Configure logging per Rule 4083 - JSON format
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ZeroUI Ollama AI Agent Service",
    version="2.0.0",
    description="AI Agent service for processing prompts via Ollama LLM (Shared Services Plane)"
)

# Request logging middleware (must be first to log all requests per Rule 173)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api/v1", tags=["ollama-ai-agent"])


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """
    Root health check endpoint.

    Returns:
        HealthResponse with service status
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        ollama_available=False
    )
