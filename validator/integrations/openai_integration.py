"""
OpenAI API Integration with Pre-Implementation Hooks
"""

import os
from typing import Dict, Any

from shared_libs.error_recovery import (
    ErrorClassifier,
    RetryPolicy,
    call_with_recovery,
)
from shared_libs.openai_adapter import llm_generate_text
from .ai_service_wrapper import AIServiceIntegration

_DEFAULT_RECOVERY_POLICY = RetryPolicy(
    max_attempts=2,
    base_delay_ms=50,
    max_delay_ms=200,
)
_DEFAULT_ERROR_CLASSIFIER = ErrorClassifier()
_DEFAULT_TIMEOUT_MS = 30_000


class OpenAIIntegration(AIServiceIntegration):
    """OpenAI API integration with constitution validation."""

    def __init__(self):
        super().__init__("openai")
        self.client = None
        self.model = None
        self.use_real_services = os.getenv("USE_REAL_SERVICES", "").lower() == "true"
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client."""
        if not self.use_real_services:
            self.logger.info("USE_REAL_SERVICES is false; OpenAI client disabled")
            return

        api_key = os.getenv('OPENAI_API_KEY')
        
        # Validate API key: check not None, not empty, proper format
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not set, OpenAI integration disabled")
            return
        
        api_key = api_key.strip()
        if not api_key:
            self.logger.error("OPENAI_API_KEY is empty or whitespace only")
            return
        
        # Validate API key format (OpenAI keys typically start with 'sk-' and are 51+ characters)
        if not api_key.startswith('sk-') or len(api_key) < 20:
            self.logger.error("OPENAI_API_KEY format appears invalid (should start with 'sk-' and be at least 20 characters)")
            return

        try:
            from openai import OpenAI

            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv('OPENAI_MODEL', None)

            # Validate model name format
            if not self.model or not isinstance(self.model, str) or len(self.model.strip()) == 0:
                raise ValueError("OPENAI_MODEL must be set when USE_REAL_SERVICES=true")

            self.logger.info(f"OpenAI client initialized with model: {self.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            self.client = None

    def generate_code(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code through OpenAI with validation."""
        return self._validate_and_generate(prompt, context)

    def _call_ai_service(self, prompt: str, context: Dict[str, Any]) -> str:
        """Call OpenAI API."""

        system_message = self._build_system_message(context)
        user_message = self._build_user_message(prompt, context)

        response = call_with_recovery(
            lambda: llm_generate_text(
                prompt=user_message,
                system_message=system_message,
                model=self.model,
                temperature=context.get('temperature', 0.3),
                max_tokens=context.get('max_tokens', 2000),
            ),
            policy=_DEFAULT_RECOVERY_POLICY,
            classifier=_DEFAULT_ERROR_CLASSIFIER,
            timeout_ms=_DEFAULT_TIMEOUT_MS,
        )

        return response["output_text"]

    def _build_system_message(self, context: Dict[str, Any]) -> str:
        """Build system message with constitution context."""
        return """You are a code generation assistant that follows strict constitution rules.
        Generate clean, readable, maintainable code that follows best practices.
        Always include proper error handling and documentation."""

    def _build_user_message(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build user message with context."""
        file_type = context.get('file_type', 'python')
        task_type = context.get('task_type', 'general')

        return f"""Generate {file_type} code for: {prompt}

        Requirements:
        - Language: {file_type}
        - Task type: {task_type}
        - Follow coding best practices
        - Include proper error handling
        - Add documentation comments
        """
