"""API routes for the LLM Gateway service."""

from __future__ import annotations

from fastapi import APIRouter

from cloud_services.llm_gateway.models import DryRunDecision, LLMRequest, LLMResponse
from cloud_services.llm_gateway.services import LLMGatewayService, build_default_service

router = APIRouter(prefix="/api/v1/llm", tags=["llm-gateway"])
service: LLMGatewayService = build_default_service()


@router.post("/chat", response_model=LLMResponse)
async def chat_endpoint(request: LLMRequest) -> LLMResponse:
    return await service.handle_chat(request)


@router.post("/embedding", response_model=LLMResponse)
async def embedding_endpoint(request: LLMRequest) -> LLMResponse:
    return await service.handle_embedding(request)


@router.post("/policy/dry-run", response_model=DryRunDecision)
async def dry_run_endpoint(request: LLMRequest) -> DryRunDecision:
    return await service.dry_run(request)


@router.get("/safety/incidents")
def list_incidents() -> dict:
    return service.list_incidents()
