"""
FastAPI application for Detection Engine Core Module (M05).

What: FastAPI app setup with CORS, health endpoints, router registration
Why: Expose Detection Engine Core functionality via REST API per PRD §3.9
Reads/Writes: HTTP request/response handling
Contracts: PRD §3.7, §3.9
Risks: CORS configuration, authentication middleware
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from .routes import router
except ImportError:
    # For direct execution or testing
    from routes import router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="Detection Engine Core API",
        description="API for detection engine core decision evaluation and feedback",
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

    logger.info("Detection Engine Core API initialized")

    return app


# Create app instance
app = create_app()

