"""
Schema registration with EPC-12 (Contracts & Schema Registry).

Provides automatic registration of observability schemas on module initialization.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Flag to control automatic registration
_AUTO_REGISTER_ENABLED = os.getenv("ZEROUI_OBSV_AUTO_REGISTER_SCHEMAS", "false").lower() == "true"
_REGISTRATION_ATTEMPTED = False


def register_schemas_with_epc12(
    base_url: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> bool:
    """
    Register all observability schemas with EPC-12.
    
    This function can be called explicitly to register schemas, or
    schemas will be auto-registered on first import if enabled via
    ZEROUI_OBSV_AUTO_REGISTER_SCHEMAS environment variable.
    
    Args:
        base_url: Optional EPC-12 base URL
        enabled: Optional enable flag
        
    Returns:
        True if registration succeeded, False otherwise
    """
    global _REGISTRATION_ATTEMPTED

    if _REGISTRATION_ATTEMPTED:
        logger.debug("Schema registration already attempted, skipping")
        return False

    _REGISTRATION_ATTEMPTED = True

    try:
        from ..integration.epc12_schema_registry import register_observability_schemas

        results = register_observability_schemas(base_url=base_url, enabled=enabled)
        success = results.get("succeeded", 0) > 0

        if success:
            logger.info(
                f"Successfully registered {results['succeeded']} schemas with EPC-12"
            )
        else:
            logger.warning("No schemas were registered with EPC-12")

        return success
    except Exception as e:
        logger.error(f"Failed to register schemas with EPC-12: {e}")
        return False


def _auto_register_if_enabled() -> None:
    """Auto-register schemas on module import if enabled."""
    if _AUTO_REGISTER_ENABLED:
        register_schemas_with_epc12()


# Auto-register on import if enabled
_auto_register_if_enabled()
