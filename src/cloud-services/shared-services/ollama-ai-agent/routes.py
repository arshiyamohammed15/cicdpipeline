"""
API routes for Ollama AI Agent service.

What: FastAPI route handlers for prompt processing and health checks
Why: Provides HTTP API endpoints for LLM interaction, delegates to service layer
Reads/Writes: Reads HTTP request bodies, writes HTTP responses (no file I/O)
Contracts: FastAPI route contract, error envelope per IPC protocol (Rule 4171)
Risks: Input validation failures, service unavailability, error message exposure
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from .models import PromptRequest, PromptResponse, HealthResponse
from .services import OllamaAIService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_service() -> OllamaAIService:
    """
    Dependency to get OllamaAIService instance.

    Returns:
        OllamaAIService instance
    """
    return OllamaAIService()


# Note: FastAPI route decorators required (Rule 332 exception - framework requirement)
@router.post("/prompt", response_model=PromptResponse)
def process_prompt(
    request: PromptRequest,
    service: OllamaAIService = Depends(get_service)
) -> PromptResponse:
    """
    Process a prompt and return AI-generated response.

    Args:
        request: The prompt request
        service: Ollama AI service instance

    Returns:
        PromptResponse with generated text

    Raises:
        HTTPException: If processing fails (with error envelope per Rule 4171)
    """
    try:
        result = service.process_prompt(request)
        return result
    except Exception as exc:
        error_code = "OLLAMA_SERVICE_ERROR"
        error_message = str(exc)
        
        # Log error per Rule 4083, Rule 62, Rule 1641
        log_data_error = {
            "timestamp": datetime.utcnow().timestamp(),
            "level": "ERROR",
            "service": "ollama-ai-agent",
            "version": "2.0.0",
            "env": "development",
            "host": "localhost",
            "operation": "process_prompt",
            "error.code": error_code,
            "severity": "ERROR",
            "cause": error_message
        }
        logger.error(json.dumps(log_data_error))
        
        # Raise HTTPException with error envelope structure per Rule 4171
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": error_code,
                    "message": error_message,
                    "details": None
                }
            }
        )


# Note: FastAPI route decorators required (Rule 332 exception - framework requirement)
@router.get("/health", response_model=HealthResponse)
def health_check(
    service: OllamaAIService = Depends(get_service)
) -> HealthResponse:
    """
    Health check endpoint.

    Args:
        service: Ollama AI service instance

    Returns:
        HealthResponse with service status
    """
    ollama_available = service.check_ollama_available()

    return HealthResponse(
        status="healthy" if ollama_available else "degraded",
        timestamp=datetime.utcnow(),
        ollama_available=ollama_available,
        llm_name=service.llm_name,
        model_name=service.model_name
    )
