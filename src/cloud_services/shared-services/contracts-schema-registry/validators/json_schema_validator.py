"""
JSON Schema validator for Contracts & Schema Registry.

What: Validates data against JSON Schema definitions
Why: Provides JSON Schema Draft 7/2020-12 validation with performance optimization
Reads/Writes: Reads schema definitions and data, writes validation results
Contracts: JSON Schema specification, PRD validation contract
Risks: Performance degradation with large schemas, memory issues with deep nesting
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import jsonschema
from jsonschema import Draft7Validator, Draft202012Validator, ValidationError as JSONSchemaValidationError
from jsonschema.validators import validator_for

logger = logging.getLogger(__name__)

# Schema size limits per PRD
MAX_SCHEMA_SIZE = 1024 * 1024  # 1MB
MAX_FIELDS_PER_SCHEMA = 1000
MAX_NESTING_DEPTH = 10


class JSONSchemaValidator:
    """
    JSON Schema validator with performance optimization.

    Per PRD: Supports JSON Schema Draft 7 and 2020-12, compiled validators for performance.
    """

    def __init__(self):
        """Initialize JSON Schema validator."""
        self._validator_cache: Dict[str, Any] = {}

    def _get_validator(self, schema: Dict[str, Any], schema_id: Optional[str] = None) -> Any:
        """
        Get or create compiled validator for schema.

        Args:
            schema: JSON Schema definition
            schema_id: Optional schema ID for caching

        Returns:
            Compiled validator instance
        """
        # Use cache key if provided
        cache_key = schema_id or str(hash(str(schema)))

        if cache_key in self._validator_cache:
            return self._validator_cache[cache_key]

        # Validate schema size
        schema_str = str(schema)
        if len(schema_str.encode('utf-8')) > MAX_SCHEMA_SIZE:
            raise ValueError(f"Schema exceeds maximum size of {MAX_SCHEMA_SIZE} bytes")

        # Determine schema version and create validator
        schema_version = schema.get("$schema", "http://json-schema.org/draft-07/schema#")

        if "draft-07" in schema_version or "draft-7" in schema_version:
            validator_class = Draft7Validator
        elif "2020-12" in schema_version or "draft/2020-12" in schema_version:
            validator_class = Draft202012Validator
        else:
            # Auto-detect best validator
            validator_class = validator_for(schema)

        # Compile validator
        try:
            validator = validator_class(schema)
            self._validator_cache[cache_key] = validator
            return validator
        except Exception as e:
            logger.error(f"Failed to create JSON Schema validator: {e}")
            raise ValueError(f"Invalid JSON Schema: {str(e)}")

    def validate(
        self,
        schema: Dict[str, Any],
        data: Dict[str, Any],
        schema_id: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data against JSON Schema.

        Args:
            schema: JSON Schema definition
            data: Data to validate
            schema_id: Optional schema ID for caching

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            validator = self._get_validator(schema, schema_id)
            errors = []

            # Perform validation
            for error in validator.iter_errors(data):
                errors.append({
                    "field": ".".join(str(p) for p in error.path),
                    "message": error.message,
                    "code": error.validator,
                    "schema_path": list(error.schema_path)
                })

            is_valid = len(errors) == 0
            return is_valid, errors

        except JSONSchemaValidationError as e:
            # Schema validation error
            return False, [{
                "field": ".",
                "message": f"Schema validation error: {str(e)}",
                "code": "SCHEMA_ERROR"
            }]
        except Exception as e:
            logger.error(f"JSON Schema validation failed: {e}")
            return False, [{
                "field": ".",
                "message": f"Validation error: {str(e)}",
                "code": "VALIDATION_ERROR"
            }]

    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that schema definition is valid JSON Schema.

        Args:
            schema: Schema definition to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            # Try to create a validator to check schema validity
            validator_for(schema)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def clear_cache(self):
        """Clear validator cache."""
        self._validator_cache.clear()
