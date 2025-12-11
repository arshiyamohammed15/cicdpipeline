"""
FastAPI application entrypoint for Integration Adapters Module.

What: FastAPI app initialization and configuration
Why: Application entrypoint
Reads/Writes: HTTP requests/responses
Contracts: PRD Section 11 (APIs & Integration Contracts)
Risks: App initialization errors, middleware configuration errors
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router
from .middleware import iam_auth_middleware
from .config import config

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup/shutdown without deprecated on_event hooks."""
    from .services.adapter_registry import get_adapter_registry
    from .adapters.github.adapter import GitHubAdapter
    from .adapters.gitlab.adapter import GitLabAdapter
    from .adapters.jira.adapter import JiraAdapter
    from .database.connection import init_db

    registry = get_adapter_registry()
    registry.register_adapter("github", GitHubAdapter)
    registry.register_adapter("gitlab", GitLabAdapter)
    registry.register_adapter("jira", JiraAdapter)
    init_db()
    yield
    # No-op shutdown for now (no persistent clients)


app = FastAPI(
    title="ZeroUI Integration Adapters Service",
    version="2.0.0",
    description="Integration Adapters Module (M10) - Unified adapter layer for external system integrations",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# IAM authentication middleware
app.middleware("http")(iam_auth_middleware)

# Include routers
app.include_router(router)
