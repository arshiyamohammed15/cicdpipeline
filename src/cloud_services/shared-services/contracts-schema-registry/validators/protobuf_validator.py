"""
Protobuf schema validator for Contracts & Schema Registry.

What: Validates data against Protobuf schema definitions
Why: Provides Protobuf message validation and type checking
Reads/Writes: Reads Protobuf schemas and data, writes validation results
Contracts: Protobuf specification, PRD validation contract
Risks: Complex schema parsing, performance with large messages
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Try to import protobuf, fallback to basic validation if not available
try:
    from google.protobuf import message, descriptor_pb2
    from google.protobuf.json_format import MessageToDict, ParseDict
    PROTOBUF_AVAILABLE = True
except ImportError:
    PROTOBUF_AVAILABLE = False
    logger.warning("protobuf not available, using basic Protobuf validation")


class ProtobufValidator:
    """
    Protobuf schema validator.

    Per PRD: Supports Protobuf schema parsing and message validation.
    """

    def __init__(self):
        """Initialize Protobuf validator."""
        self._schema_cache: Dict[str, Any] = {}

    def _parse_schema(self, schema_definition: Dict[str, Any], schema_id: Optional[str] = None) -> Any:
        """
        Parse Protobuf schema definition.

        Args:
            schema_definition: Protobuf schema definition (FileDescriptorProto or dict)
            schema_id: Optional schema ID for caching

        Returns:
            Parsed Protobuf schema
        """
        cache_key = schema_id or str(hash(str(schema_definition)))

        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]

        try:
            if PROTOBUF_AVAILABLE:
                # Try to parse as FileDescriptorProto
                if isinstance(schema_definition, dict):
                    # Assume it's a FileDescriptorProto in dict form
                    file_descriptor = descriptor_pb2.FileDescriptorProto()
                    # This is simplified - full implementation would need proper parsing
                    self._schema_cache[cache_key] = schema_definition
                    return schema_definition
                else:
                    self._schema_cache[cache_key] = schema_definition
                    return schema_definition
            else:
                # Basic validation without protobuf library
                if not isinstance(schema_definition, dict):
                    raise ValueError("Protobuf schema must be a dictionary")

                # Check for required fields in message definition
                if "message_type" not in schema_definition and "name" not in schema_definition:
                    # Might be a message definition directly
                    if "fields" not in schema_definition:
                        raise ValueError("Protobuf schema must have message_type or fields")

                self._schema_cache[cache_key] = schema_definition
                return schema_definition

        except Exception as e:
            logger.error(f"Failed to parse Protobuf schema: {e}")
            raise ValueError(f"Invalid Protobuf schema: {str(e)}")

    def validate(
        self,
        schema: Dict[str, Any],
        data: Dict[str, Any],
        schema_id: Optional[str] = None
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate data against Protobuf schema.

        Args:
            schema: Protobuf schema definition
            data: Data to validate (as dict)
            schema_id: Optional schema ID for caching

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            parsed_schema = self._parse_schema(schema, schema_id)
            errors = []

            if PROTOBUF_AVAILABLE:
                # Use protobuf for validation
                try:
                    # This is simplified - full implementation would need message class generation
                    # For now, do basic validation
                    return self._basic_validate(parsed_schema, data)
                except Exception as e:
                    errors.append({
                        "field": ".",
                        "message": f"Protobuf validation error: {str(e)}",
                        "code": "PROTOBUF_VALIDATION_ERROR"
                    })
                    return False, errors
            else:
                # Basic validation without protobuf library
                return self._basic_validate(parsed_schema, data)

        except Exception as e:
            logger.error(f"Protobuf validation failed: {e}")
            return False, [{
                "field": ".",
                "message": f"Validation error: {str(e)}",
                "code": "VALIDATION_ERROR"
            }]

    def _basic_validate(self, schema: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Basic Protobuf validation.

        Args:
            schema: Parsed Protobuf schema
            data: Data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Extract message type definition
        message_def = schema
        if "message_type" in schema:
            # FileDescriptorProto format
            if len(schema["message_type"]) > 0:
                message_def = schema["message_type"][0]

        # Check for fields
        if "field" in message_def or "fields" in message_def:
            fields = message_def.get("field", message_def.get("fields", []))

            # Validate required fields
            for field in fields:
                field_name = field.get("name")
                field_number = field.get("number")
                field_type = field.get("type")
                label = field.get("label")  # optional, required, repeated

                if label == "LABEL_REQUIRED" or label == 2:  # REQUIRED
                    if field_name not in data:
                        errors.append({
                            "field": field_name,
                            "message": f"Required field '{field_name}' is missing",
                            "code": "MISSING_FIELD"
                        })

                # Basic type checking if field exists
                if field_name in data:
                    value = data[field_name]

                    # Map Protobuf types to Python types
                    type_map = {
                        1: (str, "string"),  # TYPE_STRING
                        2: (float, "double"),  # TYPE_DOUBLE
                        3: (float, "float"),  # TYPE_FLOAT
                        4: (int, "int64"),  # TYPE_INT64
                        5: (int, "uint64"),  # TYPE_UINT64
                        6: (int, "int32"),  # TYPE_INT32
                        8: (bool, "bool"),  # TYPE_BOOL
                        9: (str, "string"),  # TYPE_STRING
                    }

                    if field_type in type_map:
                        expected_type, type_name = type_map[field_type]
                        if not isinstance(value, expected_type):
                            errors.append({
                                "field": field_name,
                                "message": f"Field '{field_name}' must be of type {type_name}",
                                "code": "TYPE_ERROR"
                            })

        return len(errors) == 0, errors

    def validate_schema(self, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that schema definition is valid Protobuf schema.

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
