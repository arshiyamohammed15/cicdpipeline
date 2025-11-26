"""
LLM Gateway & Safety Enforcement service package.

Exposes FastAPI application, request/response models, and orchestration logic
matching the ZeroUI architecture blueprint.
"""

from .main import app

__all__ = ["app"]

