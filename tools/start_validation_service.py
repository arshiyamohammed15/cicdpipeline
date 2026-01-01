#!/usr/bin/env python3
"""
Start the Constitution Validation Service

This service enforces the complete set of ZeroUI constitution rules before any AI
code generation. Rule counts are derived from docs/constitution (single source of truth).
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
src_root = project_root / "src"
if str(src_root) not in sys.path:
    sys.path.insert(0, str(src_root))

import logging
from validator.integrations.api_service import app
from config.constitution.rule_catalog import get_catalog_counts

def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('validation_service.log')
        ]
    )

def main():
    """Start the validation service."""
    setup_logging()
    logger = logging.getLogger(__name__)

    counts = get_catalog_counts()
    total_rules = counts.get("enabled_rules", counts.get("total_rules", 0))

    logger.info("=" * 60)
    logger.info("STARTING CONSTITUTION VALIDATION SERVICE")
    logger.info("=" * 60)
    logger.info(
        "This service enforces all %s ZeroUI constitution rules before AI code generation.",
        total_rules or "all available",
    )
    logger.info("Service will be available at http://localhost:5000")
    logger.info("All AI code generation requests will be validated against the constitution.")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    # Check for required environment variables
    check_environment()

    try:
        logger.info("Starting Flask application...")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down validation service...")
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)
    finally:
        logger.info("Constitution validation service stopped.")

def check_environment():
    """Check environment configuration."""
    logger = logging.getLogger(__name__)

    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning("OPENAI_API_KEY not set - OpenAI integration will be disabled")
        logger.info("Set OPENAI_API_KEY environment variable to enable OpenAI integration")

    # Check for Cursor API key
    if not os.getenv('CURSOR_API_KEY'):
        logger.warning("CURSOR_API_KEY not set - Cursor integration will be disabled")
        logger.info("Set CURSOR_API_KEY environment variable to enable Cursor integration")

    # Check for Cursor API URL
    cursor_url = os.getenv('CURSOR_API_URL', 'https://api.cursor.sh')
    logger.info(f"Cursor API URL: {cursor_url}")

    # Check OpenAI model
    openai_model = os.getenv('OPENAI_MODEL', 'gpt-4')
    logger.info(f"OpenAI model: {openai_model}")

if __name__ == '__main__':
    main()
