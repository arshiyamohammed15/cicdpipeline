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
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .models import HealthResponse
from .middleware import RequestLoggingMiddleware
from .llm_manager import OllamaProcessManager

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

# Global Ollama process manager
ollama_manager: OllamaProcessManager = OllamaProcessManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI startup/shutdown events.
    
    Starts Ollama service on startup and stops it on shutdown.
    """
    # Startup: Start Ollama service
    logger.info("Starting Ollama AI Agent service...")
    if ollama_manager.start():
        logger.info("Ollama service started successfully")
    else:
        logger.warning("Ollama service could not be started automatically. It may already be running.")
    
    yield
    
    # Shutdown: Stop Ollama service
    logger.info("Shutting down Ollama AI Agent service...")
    ollama_manager.stop()
    logger.info("Ollama AI Agent service stopped")


app = FastAPI(
    title="ZeroUI Ollama AI Agent Service",
    version="2.0.0",
    description="AI Agent service for processing prompts via Ollama LLM (Shared Services Plane)",
    lifespan=lifespan
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
    from .services import OllamaAIService
    service = OllamaAIService()
    ollama_available = service.check_ollama_available()
    
    return HealthResponse(
        status="healthy" if ollama_available else "degraded",
        timestamp=datetime.utcnow(),
        ollama_available=ollama_available,
        llm_name=service.llm_name,
        model_name=service.model_name
    )
