"""
HTTP API Service for Pre-Implementation Hooks
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from .integration_registry import IntegrationRegistry
import logging
from typing import Dict, Any, Optional, Tuple
import traceback
import re
from pathlib import Path
from validator.pre_implementation_hooks import PreImplementationHookManager

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
integration_registry = IntegrationRegistry()
hook_manager = PreImplementationHookManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for input validation
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_PROMPT_LENGTH = 100000  # 100k characters
ALLOWED_FILE_TYPES = {'python', 'typescript', 'javascript', 'java', 'cpp', 'c', 'go', 'rust', 'general'}
ALLOWED_TASK_TYPES = {'general', 'api', 'database', 'ui', 'security', 'performance', 'testing'}
VALID_SERVICE_NAMES = {'openai', 'cursor'}


def validate_prompt(prompt: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate and sanitize user prompt.
    
    Args:
        prompt: The prompt to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(prompt, str):
        return False, "Prompt must be a string"
    
    if len(prompt.strip()) == 0:
        return False, "Prompt cannot be empty"
    
    if len(prompt) > MAX_PROMPT_LENGTH:
        return False, f"Prompt exceeds maximum length of {MAX_PROMPT_LENGTH} characters"
    
    # Sanitize: remove potential script injection attempts
    # Allow normal code but block obvious injection patterns
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'eval\s*\(',
        r'exec\s*\(',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False, f"Prompt contains potentially dangerous content: {pattern}"
    
    return True, None


def validate_file_path(file_path: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate file path against allowlist and security checks.
    
    Args:
        file_path: The file path to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(file_path, str):
        return False, "File path must be a string"
    
    if len(file_path.strip()) == 0:
        return False, "File path cannot be empty"
    
    # Check for path traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        return False, "Invalid file path: path traversal not allowed"
    
    # Check for absolute paths (security risk)
    try:
        path_obj = Path(file_path)
        if path_obj.is_absolute():
            return False, "Absolute file paths are not allowed"
    except Exception as e:
        return False, f"Invalid file path format: {str(e)}"
    
    return True, None


def validate_json_payload(data: Any, required_fields: list) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate JSON payload structure and content.
    
    Args:
        data: The JSON data to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message, validated_data)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object", None
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}", None
    
    validated_data = {}
    
    # Validate and sanitize each field
    for key, value in data.items():
        if not isinstance(key, str):
            return False, f"Invalid field name: {key}", None
        
        # Validate string fields
        if isinstance(value, str) and len(value) > MAX_PROMPT_LENGTH:
            return False, f"Field '{key}' exceeds maximum length", None
        
        validated_data[key] = value
    
    return True, None, validated_data

@app.route('/health', methods=['GET'])
def health_check() -> tuple:
    """Health check endpoint."""
    try:
        from ..health import get_health_endpoint
        from ..shared_health_stats import get_health_response
        health_status = get_health_endpoint()
        
        # Use shared health response for consistency
        shared_health = get_health_response(include_backend=True)
        
        # Merge shared health data into response
        health_status['rule_counts'] = shared_health.get('rule_counts', {})
        health_status['backend'] = shared_health.get('backend', {})

        integrations = integration_registry.list_integrations()

        # Add integration info to health status
        health_status['integrations'] = integrations
        health_status['integration_status'] = integration_registry.get_integration_status()

        status_code = 200 if health_status['status'] == 'healthy' else 503
        return jsonify(health_status), status_code
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Health check failed'
        }), 500

@app.route('/healthz', methods=['GET'])
def healthz() -> tuple:
    """Kubernetes-style healthz endpoint (simple liveness probe)."""
    try:
        from ..health import HealthChecker
        checker = HealthChecker()
        rule_check = checker.check_rule_count_consistency()

        if rule_check['healthy']:
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'reason': rule_check.get('message', 'Rule count mismatch')
            }), 503
    except Exception as e:
        logger.error(f"Healthz check error: {e}", exc_info=True)
        return jsonify({'status': 'error'}), 500

@app.route('/generate', methods=['POST'])
def generate_code() -> tuple:
    """Generate code with constitution validation."""
    try:
        # Check request size
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': f'Request size exceeds maximum of {MAX_REQUEST_SIZE} bytes'
            }), 400
        
        # Validate JSON payload
        data = request.get_json()
        is_valid, error_msg, validated_data = validate_json_payload(data, ['prompt'])
        if not is_valid:
            logger.warning(f"Invalid request payload: {error_msg}")
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': error_msg or 'Invalid request payload'
            }), 400
        
        data = validated_data
        
        # Validate prompt
        prompt = data.get('prompt')
        is_valid, error_msg = validate_prompt(prompt)
        if not is_valid:
            logger.warning(f"Invalid prompt: {error_msg}")
            return jsonify({
                'success': False,
                'error': 'INVALID_PROMPT',
                'message': error_msg or 'Invalid prompt'
            }), 400
        
        # Validate service name
        service_name = data.get('service', 'openai')
        if service_name not in VALID_SERVICE_NAMES:
            logger.warning(f"Invalid service name: {service_name}")
            return jsonify({
                'success': False,
                'error': 'INVALID_SERVICE',
                'message': f'Invalid service name. Must be one of: {", ".join(VALID_SERVICE_NAMES)}'
            }), 400
        
        # Validate file_type
        file_type = data.get('file_type', 'python')
        if file_type not in ALLOWED_FILE_TYPES:
            logger.warning(f"Invalid file type: {file_type}")
            return jsonify({
                'success': False,
                'error': 'INVALID_FILE_TYPE',
                'message': f'Invalid file type. Must be one of: {", ".join(ALLOWED_FILE_TYPES)}'
            }), 400
        
        # Validate task_type
        task_type = data.get('task_type', 'general')
        if task_type not in ALLOWED_TASK_TYPES:
            logger.warning(f"Invalid task type: {task_type}")
            return jsonify({
                'success': False,
                'error': 'INVALID_TASK_TYPE',
                'message': f'Invalid task type. Must be one of: {", ".join(ALLOWED_TASK_TYPES)}'
            }), 400
        
        # Validate file_path if provided
        if 'file_path' in data:
            is_valid, error_msg = validate_file_path(data['file_path'])
            if not is_valid:
                logger.warning(f"Invalid file path: {error_msg}")
                return jsonify({
                    'success': False,
                    'error': 'INVALID_FILE_PATH',
                    'message': error_msg or 'Invalid file path'
                }), 400
        
        # Validate numeric parameters
        temperature = data.get('temperature', 0.3)
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
            logger.warning(f"Invalid temperature: {temperature}")
            return jsonify({
                'success': False,
                'error': 'INVALID_TEMPERATURE',
                'message': 'Temperature must be between 0 and 2'
            }), 400
        
        max_tokens = data.get('max_tokens', 2000)
        if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 100000:
            logger.warning(f"Invalid max_tokens: {max_tokens}")
            return jsonify({
                'success': False,
                'error': 'INVALID_MAX_TOKENS',
                'message': 'max_tokens must be between 1 and 100000'
            }), 400
        
        context = {
            'file_type': file_type,
            'task_type': task_type,
            'temperature': float(temperature),
            'max_tokens': int(max_tokens),
            'file_path': data.get('file_path')
        }

        logger.info(f"Code generation request: service={service_name}, file_type={context['file_type']}")

        result = integration_registry.generate_code(
            service_name, prompt, context
        )

        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"API error: {e}", exc_info=True)
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': 'An internal error occurred'
        }), 500

@app.route('/validate', methods=['POST'])
def validate_only() -> tuple:
    """Validate prompt without generation."""
    try:
        # Check request size
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': f'Request size exceeds maximum of {MAX_REQUEST_SIZE} bytes'
            }), 400
        
        # Validate JSON payload
        data = request.get_json()
        is_valid, error_msg, validated_data = validate_json_payload(data, ['prompt'])
        if not is_valid:
            logger.warning(f"Invalid request payload: {error_msg}")
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': error_msg or 'Invalid request payload'
            }), 400
        
        data = validated_data
        
        # Validate prompt
        prompt = data.get('prompt')
        is_valid, error_msg = validate_prompt(prompt)
        if not is_valid:
            logger.warning(f"Invalid prompt: {error_msg}")
            return jsonify({
                'success': False,
                'error': 'INVALID_PROMPT',
                'message': error_msg or 'Invalid prompt'
            }), 400
        
        # Validate file_type
        file_type = data.get('file_type', 'python')
        if file_type not in ALLOWED_FILE_TYPES:
            logger.warning(f"Invalid file type: {file_type}")
            return jsonify({
                'success': False,
                'error': 'INVALID_FILE_TYPE',
                'message': f'Invalid file type. Must be one of: {", ".join(ALLOWED_FILE_TYPES)}'
            }), 400
        
        # Validate task_type
        task_type = data.get('task_type', 'general')
        if task_type not in ALLOWED_TASK_TYPES:
            logger.warning(f"Invalid task type: {task_type}")
            return jsonify({
                'success': False,
                'error': 'INVALID_TASK_TYPE',
                'message': f'Invalid task type. Must be one of: {", ".join(ALLOWED_TASK_TYPES)}'
            }), 400

        logger.info("Prompt validation request")

        result = integration_registry.validate_prompt(
            prompt,
            {
                'file_type': file_type,
                'task_type': task_type
            }
        )

        # Ensure violations are properly formatted
        if 'violations' in result and result['violations']:
            # The registry should already format them, but ensure consistency
            formatted_violations = []
            for v in result['violations']:
                if isinstance(v, dict):
                    formatted_violations.append(v)
                else:
                    # Convert Violation object to dict
                    formatted_violations.append({
                        'rule_id': getattr(v, 'rule_id', 'unknown'),
                        'rule_number': getattr(v, 'rule_number', 0),
                        'severity': getattr(v, 'severity', 'unknown'),
                        'message': getattr(v, 'message', ''),
                        'file_path': getattr(v, 'file_path', ''),
                        'line_number': getattr(v, 'line_number', 0),
                        'code_snippet': getattr(v, 'code_snippet', ''),
                        'fix_suggestion': getattr(v, 'fix_suggestion', '')
                    })
            result['violations'] = formatted_violations

        return jsonify(result)

    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': 'An internal validation error occurred'
        }), 500

@app.route('/integrations', methods=['GET'])
def list_integrations() -> tuple:
    """List available integrations."""
    try:
        integrations = integration_registry.list_integrations()
        return jsonify({
            'integrations': integrations,
            'total': len(integrations)
        })
    except Exception as e:
        logger.error(f"List integrations error: {e}", exc_info=True)
        return jsonify({
            'error': 'LIST_ERROR',
            'message': 'Failed to list integrations'
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats() -> tuple:
    """Get service statistics."""
    try:
        from ..shared_health_stats import get_stats_response
        stats = get_stats_response(include_backend=True)
        
        # Add integration-specific stats
        stats['available_integrations'] = integration_registry.list_integrations()
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}", exc_info=True)
        return jsonify({
            'error': 'STATS_ERROR',
            'message': 'Failed to retrieve statistics'
        }), 500

if __name__ == '__main__':
    logger.info("Starting Constitution Validation Service...")
    logger.info(
        "This service enforces all %s ZeroUI constitution rules before AI code generation.",
        hook_manager.total_rules
    )
    logger.info("Service will be available at http://localhost:5000")
    logger.info("Press Ctrl+C to stop")

    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down validation service...")
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise
