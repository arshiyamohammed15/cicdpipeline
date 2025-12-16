"""
Cursor IDE Integration with Pre-Implementation Hooks
"""

import os
import json
from typing import Dict, Any, Optional
from .ai_service_wrapper import AIServiceIntegration

class CursorIntegration(AIServiceIntegration):
    """Cursor IDE integration with constitution validation."""

    def __init__(self):
        super().__init__("cursor")
        self.api_key = os.getenv('CURSOR_API_KEY')
        self.base_url = os.getenv('CURSOR_API_URL', 'https://api.cursor.sh')
        self._validate_config()

    def _validate_config(self):
        """Validate configuration."""
        if not self.api_key:
            self.logger.warning("CURSOR_API_KEY not set, Cursor integration disabled")
            return
        
        # Validate API key: check not None, not empty, proper format
        api_key = self.api_key.strip()
        if not api_key:
            self.logger.error("CURSOR_API_KEY is empty or whitespace only")
            self.api_key = None
            return
        
        # Validate API key format (Cursor keys are typically base64-like strings, at least 20 characters)
        if len(api_key) < 20:
            self.logger.error("CURSOR_API_KEY format appears invalid (should be at least 20 characters)")
            self.api_key = None
            return
        
        # Validate base URL format
        if self.base_url:
            base_url = self.base_url.strip()
            if not base_url.startswith(('http://', 'https://')):
                self.logger.error(f"Invalid CURSOR_API_URL format: {base_url} (should start with http:// or https://)")
                self.base_url = 'https://api.cursor.sh'
            else:
                self.base_url = base_url
        
        self.logger.info(f"Cursor integration configured with API URL: {self.base_url}")

    def generate_code(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code through Cursor with validation."""
        # Always validate first, regardless of API key status
        validation_result = self._validate_and_generate(prompt, context)

        # If validation failed, return the violation result
        if not validation_result['success']:
            return validation_result

        # If validation passed but no API key, return configuration error
        if not self.api_key:
            return {
                'success': False,
                'error': 'CURSOR_NOT_CONFIGURED',
                'message': 'Cursor API key not configured',
                'validation_passed': True
            }

        # Validation passed and API key available, return the validated result
        return validation_result

    def _call_ai_service(self, prompt: str, context: Dict[str, Any]) -> str:
        """Call Cursor API."""
        import requests

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'prompt': prompt,
            'file_type': context.get('file_type', 'python'),
            'task_type': context.get('task_type', 'general'),
            'temperature': context.get('temperature', 0.3),
            'max_tokens': context.get('max_tokens', 2000)
        }

        response = requests.post(
            f"{self.base_url}/v1/generate",
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        result = response.json()

        return result['generated_code']

    def _build_system_message(self, context: Dict[str, Any]) -> str:
        """Build system message for Cursor."""
        return """You are Cursor IDE's code generation assistant.
        Generate code that follows the ZeroUI 2.0 Constitution rules.
        Ensure all code is clean, documented, and follows best practices."""

    def _build_user_message(self, prompt: str, context: Dict[str, Any]) -> str:
        """Build user message for Cursor."""
        file_type = context.get('file_type', 'typescript')
        return f"""Generate {file_type} code: {prompt}

        Follow ZeroUI 2.0 Constitution rules:
        - Do exactly what's asked
        - Use only given information
        - Follow coding standards
        - Include proper documentation
        """
