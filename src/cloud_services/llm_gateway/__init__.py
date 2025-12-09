"""
LLM Gateway & Safety Enforcement service package.

Exposes FastAPI application, request/response models, and orchestration logic
matching the ZeroUI architecture blueprint.

Note: FastAPI app creation is defined in ``cloud_services.llm_gateway.main``.
Imports are intentionally lazy to avoid side effects during test collection.
"""

__all__: list[str] = []
