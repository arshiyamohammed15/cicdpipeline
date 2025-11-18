"""
FastAPI application entry point for Data Governance & Privacy Module (M22).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - framework hook
    yield


app = FastAPI(
    title="ZeroUI Data Governance & Privacy Service",
    version="1.0.0",
    description="Implements M22 specification for classification, consent, privacy enforcement, lineage, retention, and rights automation.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
