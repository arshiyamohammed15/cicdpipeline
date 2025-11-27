"""
FastAPI application for User Behaviour Intelligence (UBI) Module (EPC-9).

What: FastAPI app setup with CORS, health endpoints, router registration
Why: Expose UBI functionality via REST API per PRD Section 11
Reads/Writes: HTTP request/response handling
Contracts: PRD Section 11 APIs & Integration Contracts
Risks: CORS configuration, authentication middleware
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .middleware import IAMAuthMiddleware
from .service_registry import initialize_services

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="User Behaviour Intelligence API",
        description="API for behavioural analytics, feature computation, baseline management, and signal generation",
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

    # IAM authentication middleware
    app.add_middleware(IAMAuthMiddleware)

    # Include routers
    app.include_router(router)

    # Initialize services
    initialize_services()

    logger.info("UBI API initialized")

    return app


# Create app instance
app = create_app()

