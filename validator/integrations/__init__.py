"""
AI Service Integration Layer for Pre-Implementation Hooks
This intercepts AI code generation requests and enforces constitution rules.
"""

from .ai_service_wrapper import AIServiceIntegration, IntegrationRegistry
from .openai_integration import OpenAIIntegration
from .cursor_integration import CursorIntegration

__all__ = [
    'AIServiceIntegration',
    'IntegrationRegistry',
    'OpenAIIntegration',
    'CursorIntegration'
]
