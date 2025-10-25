"""
OpenAI API Integration with Pre-Implementation Hooks
"""

import os
import openai
from typing import Dict, Any
from .ai_service_wrapper import AIServiceIntegration

class OpenAIIntegration(AIServiceIntegration):
    """OpenAI API integration with constitution validation."""

    def __init__(self):
        super().__init__("openai")
        self.client = None
        self.model = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            self.logger.warning("OPENAI_API_KEY not set, OpenAI integration disabled")
            return

        try:
            self.client = openai.OpenAI(api_key=api_key)
            self.model = os.getenv('OPENAI_MODEL', 'gpt-4')
            self.logger.info(f"OpenAI client initialized with model: {self.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None

    def generate_code(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code through OpenAI with validation."""
        # Always validate first, regardless of API key status
        validation_result = self._validate_and_generate(prompt, context)

        # If validation failed, return the violation result
        if not validation_result['success']:
            return validation_result

        # If validation passed but no API key, return configuration error
        if not self.client:
            return {
                'success': False,
                'error': 'OPENAI_NOT_CONFIGURED',
                'message': 'OpenAI API key not configured',
                'validation_passed': True
            }

        # Validation passed and API key available, return the validated result
        return validation_result

    def _call_ai_service(self, prompt: str, context: Dict[str, Any]) -> str:
        """Call OpenAI API."""

        system_message = self._build_system_message(context)
        user_message = self._build_user_message(prompt, context)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=context.get('temperature', 0.3),
            max_tokens=context.get('max_tokens', 2000)
        )

        return response.choices[0].message.content

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
