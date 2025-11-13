"""
AI Service Integration Layer for Pre-Implementation Hooks
This intercepts AI code generation requests and enforces constitution rules.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from abc import ABC, abstractmethod
from validator.pre_implementation_hooks import PreImplementationHookManager
from validator.models import Violation, Severity

class AIServiceIntegration(ABC):
    """Abstract base for AI service integrations."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.hook_manager = PreImplementationHookManager()
        self.logger = logging.getLogger(f"{__name__}.{service_name}")

    @abstractmethod
    def generate_code(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code through the AI service with validation."""
        pass

    def _validate_and_generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method that enforces pre-implementation validation."""

        # Step 1: Pre-implementation validation
        file_type = context.get('file_type', 'python')
        task_type = context.get('task_type', 'general')

        validation_result = self.hook_manager.validate_before_generation(
            prompt, file_type, task_type
        )

        # Step 2: Block generation if violations found
        if not validation_result['valid']:
            self.logger.error(f"Constitution violations detected: {len(validation_result['violations'])}")

            return {
                'success': False,
                'error': 'CONSTITUTION_VIOLATION',
                'violations': self._format_violations(validation_result['violations']),
                'recommendations': validation_result['recommendations'],
                'blocked_by': 'pre_implementation_hooks',
                'service': self.service_name
            }

        # Step 3: Proceed with actual AI generation if validation passes
        self.logger.info(f"Prompt validated against {validation_result['total_rules_checked']} rules")

        try:
            ai_result = self._call_ai_service(prompt, context)

            # Step 4: Post-generation validation - validate generated code
            from validator.post_generation_validator import PostGenerationValidator
            post_validator = PostGenerationValidator()

            file_type = context.get('file_type', 'python')
            file_path = context.get('file_path', 'generated_code')

            post_validation_result = post_validator.validate_generated_code(
                ai_result,
                file_type=file_type,
                file_path=file_path
            )

            # Step 5: Block if violations found in generated code
            if not post_validation_result['valid']:
                self.logger.error(
                    f"Generated code violations detected: {post_validation_result['total_violations']}"
                )

                return {
                    'success': False,
                    'error': 'GENERATED_CODE_VIOLATION',
                    'violations': post_validation_result['violations'],
                    'total_violations': post_validation_result['total_violations'],
                    'violations_by_severity': post_validation_result['violations_by_severity'],
                    'compliance_score': post_validation_result.get('compliance_score', 0.0),
                    'blocked_by': 'post_generation_validator',
                    'service': self.service_name,
                    'generated_code': ai_result  # Include code for review
                }

            # Step 6: Return successful generation with validation info
            self.logger.info(
                f"Generated code validated: {post_validation_result['total_violations']} violations found"
            )

            return {
                'success': True,
                'generated_code': ai_result,
                'validation_info': {
                    'pre_validation': {
                        'rules_checked': validation_result['total_rules_checked'],
                        'categories_validated': validation_result['relevant_categories']
                    },
                    'post_validation': {
                        'violations_found': post_validation_result['total_violations'],
                        'compliance_score': post_validation_result.get('compliance_score', 1.0)
                    }
                }
            }
        except Exception as e:
            self.logger.error(f"AI service error: {e}")
            return {
                'success': False,
                'error': 'AI_SERVICE_ERROR',
                'message': str(e)
            }

    @abstractmethod
    def _call_ai_service(self, prompt: str, context: Dict[str, Any]) -> str:
        """Call the actual AI service."""
        pass

    def _format_violations(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """Format violations for API response."""
        return [{
            'rule_id': v.rule_id,
            'rule_number': getattr(v, 'rule_number', 0),
            'severity': v.severity.value if hasattr(v.severity, 'value') else str(v.severity),
            'message': v.message,
            'file_path': v.file_path,
            'line_number': getattr(v, 'line_number', 0),
            'code_snippet': getattr(v, 'code_snippet', ''),
            'fix_suggestion': getattr(v, 'fix_suggestion', '')
        } for v in violations]


class IntegrationRegistry:
    """Registry for AI service integrations."""

    def __init__(self):
        self.integrations: Dict[str, AIServiceIntegration] = {}
        self._load_integrations()

    def _load_integrations(self):
        """Load available integrations."""
        try:
            from .openai_integration import OpenAIIntegration
            self.integrations['openai'] = OpenAIIntegration()
            self.logger.info("OpenAI integration loaded")
        except ImportError as e:
            self.logger.warning(f"OpenAI integration not available: {e}")

        try:
            from .cursor_integration import CursorIntegration
            self.integrations['cursor'] = CursorIntegration()
            self.logger.info("Cursor integration loaded")
        except ImportError as e:
            self.logger.warning(f"Cursor integration not available: {e}")

    def get_integration(self, service_name: str) -> Optional[AIServiceIntegration]:
        """Get integration by service name."""
        return self.integrations.get(service_name)

    def generate_code(self, service_name: str, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code with automatic validation."""
        integration = self.get_integration(service_name)

        if not integration:
            return {
                'success': False,
                'error': 'INTEGRATION_NOT_FOUND',
                'message': f"Integration for {service_name} not available",
                'available_integrations': list(self.integrations.keys())
            }

        return integration.generate_code(prompt, context)

    def list_integrations(self) -> List[str]:
        """List available integrations."""
        return list(self.integrations.keys())

    def validate_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate prompt without generation."""
        hook_manager = PreImplementationHookManager()
        return hook_manager.validate_before_generation(
            prompt,
            context.get('file_type', 'python'),
            context.get('task_type', 'general')
        )
