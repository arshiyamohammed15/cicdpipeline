"""
HTTP API Service for Pre-Implementation Hooks
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from .integration_registry import IntegrationRegistry
import logging
from typing import Dict, Any
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
integration_registry = IntegrationRegistry()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        integrations = integration_registry.list_integrations()
        return jsonify({
            'status': 'healthy',
            'integrations': integrations,
            'total_rules': 293,
            'enforcement': 'active'
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/generate', methods=['POST'])
def generate_code():
    """Generate code with constitution validation."""
    try:
        data = request.get_json()

        if not data or 'prompt' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': 'Prompt is required'
            }), 400

        service_name = data.get('service', 'openai')
        context = {
            'file_type': data.get('file_type', 'python'),
            'task_type': data.get('task_type', 'general'),
            'temperature': data.get('temperature', 0.3),
            'max_tokens': data.get('max_tokens', 2000)
        }

        logger.info(f"Code generation request: service={service_name}, file_type={context['file_type']}")

        result = integration_registry.generate_code(
            service_name, data['prompt'], context
        )

        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"API error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }), 500

@app.route('/validate', methods=['POST'])
def validate_only():
    """Validate prompt without generation."""
    try:
        data = request.get_json()

        if not data or 'prompt' not in data:
            return jsonify({
                'success': False,
                'error': 'INVALID_REQUEST',
                'message': 'Prompt is required'
            }), 400

        logger.info("Prompt validation request")

        result = integration_registry.validate_prompt(
            data['prompt'],
            {
                'file_type': data.get('file_type', 'python'),
                'task_type': data.get('task_type', 'general')
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
        logger.error(f"Validation error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 500

@app.route('/integrations', methods=['GET'])
def list_integrations():
    """List available integrations."""
    try:
        integrations = integration_registry.list_integrations()
        return jsonify({
            'integrations': integrations,
            'total': len(integrations)
        })
    except Exception as e:
        logger.error(f"List integrations error: {e}")
        return jsonify({
            'error': 'LIST_ERROR',
            'message': str(e)
        }), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get service statistics."""
    try:
        # This would need to be implemented in the registry
        return jsonify({
            'total_rules': 293,
            'enforcement_active': True,
            'available_integrations': integration_registry.list_integrations()
        })
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({
            'error': 'STATS_ERROR',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Constitution Validation Service...")
    logger.info("This service enforces all 293 ZeroUI constitution rules before AI code generation.")
    logger.info("Service will be available at http://localhost:5000")
    logger.info("Press Ctrl+C to stop")

    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down validation service...")
    except Exception as e:
        logger.error(f"Service error: {e}")
        raise
