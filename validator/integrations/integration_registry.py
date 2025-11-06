"""
Integration Registry for AI Services
"""

import logging
from typing import Dict, Type, Optional, List, Any
from .ai_service_wrapper import AIServiceIntegration

class IntegrationRegistry:
    """Registry for AI service integrations."""

    def __init__(self):
        self.integrations: Dict[str, AIServiceIntegration] = {}
        self.logger = logging.getLogger(__name__)
        self._load_integrations()

    def _load_integrations(self):
        """Load available integrations."""
        # Load OpenAI integration
        try:
            from .openai_integration import OpenAIIntegration
            self.integrations['openai'] = OpenAIIntegration()
            self.logger.info("OpenAI integration loaded successfully")
        except ImportError as e:
            self.logger.warning(f"OpenAI integration not available: {e}")
        except Exception as e:
            self.logger.error(f"Error loading OpenAI integration: {e}")

        # Load Cursor integration
        try:
            from .cursor_integration import CursorIntegration
            self.integrations['cursor'] = CursorIntegration()
            self.logger.info("Cursor integration loaded successfully")
        except ImportError as e:
            self.logger.warning(f"Cursor integration not available: {e}")
        except Exception as e:
            self.logger.error(f"Error loading Cursor integration: {e}")

        # Load other integrations as they become available
        # Future: Add Claude, local models, etc.

        self.logger.info(f"Loaded {len(self.integrations)} AI service integrations")

    def get_integration(self, service_name: str) -> Optional[AIServiceIntegration]:
        """Get integration by service name."""
        integration = self.integrations.get(service_name)
        if integration:
            self.logger.info(f"Using integration: {service_name}")
        else:
            self.logger.error(f"Integration not found: {service_name}")
        return integration

    def generate_code(self, service_name: str, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code with automatic validation."""
        integration = self.get_integration(service_name)

        if not integration:
            available = list(self.integrations.keys())
            return {
                'success': False,
                'error': 'INTEGRATION_NOT_FOUND',
                'message': f"Integration for '{service_name}' not available",
                'available_integrations': available,
                'suggestion': f"Use one of: {', '.join(available)}"
            }

        self.logger.info(f"Generating code via {service_name} with prompt: {prompt[:100]}...")
        return integration.generate_code(prompt, context)

    def list_integrations(self) -> List[str]:
        """List available integrations."""
        return list(self.integrations.keys())

    def validate_prompt(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate prompt without generation."""
        from validator.pre_implementation_hooks import PreImplementationHookManager

        hook_manager = PreImplementationHookManager()
        result = hook_manager.validate_before_generation(
            prompt,
            context.get('file_type', 'python'),
            context.get('task_type', 'general')
        )

        # Format violations for API response
        if 'violations' in result and result['violations']:
            # Format violations properly
            formatted_violations = []
            for v in result['violations']:
                if isinstance(v, dict):
                    formatted_violations.append(v)
                else:
                    # Convert Violation object to dict
                    formatted_violations.append({
                        'rule_id': getattr(v, 'rule_id', 'unknown'),
                        'rule_number': getattr(v, 'rule_number', 0),
                        'severity': str(getattr(v, 'severity', 'unknown')),
                        'message': getattr(v, 'message', ''),
                        'file_path': getattr(v, 'file_path', ''),
                        'line_number': getattr(v, 'line_number', 0),
                        'code_snippet': getattr(v, 'code_snippet', ''),
                        'fix_suggestion': getattr(v, 'fix_suggestion', '')
                    })
            result['violations'] = formatted_violations

        return result

    def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all integrations."""
        status = {}
        for name, integration in self.integrations.items():
            try:
                # Check if integration is properly configured
                if hasattr(integration, 'client') and integration.client is None:
                    status[name] = 'not_configured'
                elif hasattr(integration, 'api_key') and not integration.api_key:
                    status[name] = 'not_configured'
                else:
                    status[name] = 'ready'
            except Exception as e:
                status[name] = f'error: {str(e)}'
                self.logger.error(f"Error checking status for {name}: {e}")

        # Get actual rule count from hook manager (single source of truth)
        from validator.pre_implementation_hooks import PreImplementationHookManager
        hook_manager = PreImplementationHookManager()
        total_rules = hook_manager.total_rules
        
        return {
            'total_integrations': len(self.integrations),
            'integration_status': status,
            'constitution_enforcement': 'active',
            'total_rules': total_rules
        }
