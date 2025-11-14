"""
Avro schema validator for Contracts & Schema Registry.

What: Validates data against Avro schema definitions
Why: Provides Avro schema parsing and binary format validation
Reads/Writes: Reads Avro schemas and data, writes validation results
Contracts: Avro specification, PRD validation contract
Risks: Performance issues with complex schemas, binary format handling
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
import json

logger = logging.getLogger(__name__)

# Try to import fastavro, fallback to basic validation if not available
try:
    import fastavro
    FASTAVRO_AVAILABLE = True
except ImportError:
    FASTAVRO_AVAILABLE = False
    logger.warning("fastavro not available, using basic Avro validation")


class AvroValidator:
    """
    Avro schema validator.

    Per PRD: Supports Avro schema parsing and binary format validation.
    """

    def __init__(self):
        """Initialize Avro validator."""
        self._schema_cache: Dict[str, Any] = {}

    def _parse_schema(self, schema_definition: Dict[str, Any], schema_id: Optional[str] = None) -> Any:
        """
        Parse Avro schema definition.

        Args:
            schema_definition: Avro schema definition (dict or JSON string)
            schema_id: Optional schema ID for caching

        Returns:
            Parsed Avro schema
        """
        cache_key = schema_id or str(hash(str(schema_definition)))

        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]

        try:
            # Convert to dict if string
            if isinstance(schema_definition, str):
                schema_dict = json.loads(schema_definition)
            else:
                schema_dict = schema_definition

            if FASTAVRO_AVAILABLE:
                # Parse schema using fastavro
                parsed_schema = fastavro.parse_schema(schema_dict)
                self._schema_cache[cache_key] = parsed_schema
                return parsed_schema
            else:
                # Basic validation without fastavro
                if not isinstance(schema_dict, dict):
                    raise ValueError("Avro schema must be a dictionary")

                if "type" not in schema_dict and "fields" not in schema_dict:
                    raise ValueError("Avro schema must have 'type' or 'fields'")

                # Store parsed dict
                self._schema_cache[cache_key] = schema_dict
                return schema_dict

        except Exception as e:
            logger.error(f"Failed to parse Avro schema: {e}")
            raise ValueError(f"Invalid Avro schema: {str(e)}")

    def validate(
        self,
        schema: Dict[str, Any],
        data: Dict[str, Any],
        schema_id: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data against Avro schema.

        Args:
            schema: Avro schema definition
            data: Data to validate
            schema_id: Optional schema ID for caching

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            parsed_schema = self._parse_schema(schema, schema_id)
            errors = []

            if FASTAVRO_AVAILABLE:
                # Use fastavro for validation
                try:
                    fastavro.validate(data, parsed_schema)
                    return True, []
                except Exception as e:
                    errors.append({
                        "field": ".",
                        "message": f"Avro validation error: {str(e)}",
                        "code": "AVRO_VALIDATION_ERROR"
                    })
                    return False, errors
            else:
                # Basic validation without fastavro
                return self._basic_validate(parsed_schema, data)

        except Exception as e:
            logger.error(f"Avro validation failed: {e}")
            return False, [{
                "field": ".",
                "message": f"Validation error: {str(e)}",
                "code": "VALIDATION_ERROR"
            }]

    def _basic_validate(self, schema: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Basic Avro validation without fastavro library.

        Args:
            schema: Parsed Avro schema
            data: Data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check if schema has fields (record type)
        if "fields" in schema:
            # Record type validation
            required_fields = {f["name"] for f in schema["fields"] if not f.get("default")}

            for field_name in required_fields:
                if field_name not in data:
                    errors.append({
                        "field": field_name,
                        "message": f"Required field '{field_name}' is missing",
                        "code": "MISSING_FIELD"
                    })

            # Validate field types (basic)
            for field in schema["fields"]:
                field_name = field["name"]
                field_type = field.get("type")

                if field_name in data:
                    value = data[field_name]
                    # Basic type checking
                    if field_type == "string" and not isinstance(value, str):
                        errors.append({
                            "field": field_name,
                            "message": f"Field '{field_name}' must be a string",
                            "code": "TYPE_ERROR"
                        })
                    elif field_type == "int" and not isinstance(value, int):
                        errors.append({
                            "field": field_name,
                            "message": f"Field '{field_name}' must be an integer",
                            "code": "TYPE_ERROR"
                        })
                    elif field_type == "long" and not isinstance(value, int):
                        errors.append({
                            "field": field_name,
                            "message": f"Field '{field_name}' must be a long integer",
                            "code": "TYPE_ERROR"
                        })
                    elif field_type == "float" and not isinstance(value, (int, float)):
                        errors.append({
                            "field": field_name,
                            "message": f"Field '{field_name}' must be a float",
                            "code": "TYPE_ERROR"
                        })
                    elif field_type == "double" and not isinstance(value, (int, float)):
                        errors.append({
                            "field": field_name,
                            "message": f"Field '{field_name}' must be a double",
                            "code": "TYPE_ERROR"
                        })
                    elif field_type == "boolean" and not isinstance(value, bool):
                        errors.append({
                            "field": field_name,
                            "message": f"Field '{field_name}' must be a boolean",
                            "code": "TYPE_ERROR"
                        })

        return len(errors) == 0, errors

    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that schema definition is valid Avro schema.

        Args:
            schema: Schema definition to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            self._parse_schema(schema)
            return True, []
        except Exception as e:
            return False, [str(e)]

    def clear_cache(self):
        """Clear schema cache."""
        self._schema_cache.clear()
