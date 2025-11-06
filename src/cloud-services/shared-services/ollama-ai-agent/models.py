"""
Pydantic models for Ollama AI Agent service.

What: Defines Pydantic v2 models for request/response validation and error handling
Why: Ensures type safety, input validation, and standardized API contracts
Reads/Writes: Reads request data, writes response data (no file I/O)
Contracts: FastAPI request/response models, error envelope structure per IPC protocol
Risks: Model validation failures may expose internal error details if not handled properly
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Request model for AI prompt processing."""

    prompt: str = Field(..., description="The prompt to send to the LLM", min_length=1)
    model: Optional[str] = Field(
        default="tinyllama", description="Model name to use"
    )
    stream: Optional[bool] = Field(
        default=False, description="Whether to stream the response"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional model options"
    )


class PromptResponse(BaseModel):
    """Response model for AI prompt processing."""

    success: bool = Field(..., description="Whether the request was successful")
    response: str = Field(..., description="The generated response from the LLM")
    model: str = Field(..., description="The model used for generation")
    timestamp: str = Field(..., description="ISO timestamp of the response")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    ollama_available: bool = Field(
        ..., description="Whether Ollama service is available"
    )


class ErrorDetail(BaseModel):
    """Error detail model for error envelope."""

    code: str = Field(..., description="Error code", min_length=1)
    message: str = Field(..., description="Error message", min_length=1)
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )


class ErrorResponse(BaseModel):
    """Error response envelope model per IPC protocol contract."""

    error: ErrorDetail = Field(..., description="Error information")

