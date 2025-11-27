"""
Data transformation engine for Contracts & Schema Registry.

What: Transforms data between schema versions
Why: Enables schema evolution with data migration per PRD
Reads/Writes: Reads source data and schemas, writes transformed data
Contracts: PRD transformation specification
Risks: Data loss during transformation, incorrect field mapping
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DataTransformer:
    """
    Data transformation engine.

    Per PRD: Transforms data between schema versions with field mapping and type conversion.
    """

    def __init__(self):
        """Initialize data transformer."""
        pass

    def transform(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any],
        data: Dict[str, Any],
        source_schema_id: Optional[str] = None,
        target_schema_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Transform data from source schema to target schema.

        Args:
            source_schema: Source schema definition
            target_schema: Target schema definition
            data: Data to transform
            source_schema_id: Optional source schema ID
            target_schema_id: Optional target schema ID

        Returns:
            Tuple of (transformed_data, transformation_applied, warnings)
        """
        warnings = []
        transformation_applied = False

        # Extract schema types
        source_type = self._get_schema_type(source_schema)
        target_type = self._get_schema_type(target_schema)

        if source_type != target_type:
            warnings.append(f"Schema type mismatch: {source_type} -> {target_type}")
            return data, False, warnings

        # Transform based on schema type
        if source_type == "json_schema":
            return self._transform_json_schema(source_schema, target_schema, data)
        elif source_type == "avro":
            return self._transform_avro(source_schema, target_schema, data)
        elif source_type == "protobuf":
            return self._transform_protobuf(source_schema, target_schema, data)
        else:
            warnings.append(f"Unsupported schema type: {source_type}")
            return data, False, warnings

    def _get_schema_type(self, schema: Dict[str, Any]) -> str:
        """
        Extract schema type from schema definition.

        Args:
            schema: Schema definition

        Returns:
            Schema type string
        """
        if "schema_type" in schema:
            return schema["schema_type"]

        if "$schema" in schema or "type" in schema:
            return "json_schema"
        elif "type" in schema and schema.get("type") == "record":
            return "avro"
        elif "message_type" in schema or "syntax" in schema:
            return "protobuf"

        return "json_schema"

    def _transform_json_schema(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Transform data between JSON Schema versions.

        Args:
            source: Source JSON Schema
            target: Target JSON Schema
            data: Data to transform

        Returns:
            Tuple of (transformed_data, transformation_applied, warnings)
        """
        warnings = []
        transformed = {}
        transformation_applied = False

        source_props = source.get("properties", {})
        target_props = target.get("properties", {})
        source_required = set(source.get("required", []))
        target_required = set(target.get("required", []))

        # Map existing fields
        for field_name, field_value in data.items():
            if field_name in target_props:
                # Field exists in target, map it
                transformed[field_name] = self._convert_value(
                    field_value,
                    source_props.get(field_name, {}),
                    target_props[field_name],
                    warnings
                )
                transformation_applied = True
            else:
                # Field removed in target schema
                warnings.append(f"Field '{field_name}' removed in target schema, dropping value")

        # Add default values for new required fields
        new_required = target_required - source_required
        for field_name in new_required:
            field_def = target_props.get(field_name, {})
            if "default" in field_def:
                transformed[field_name] = field_def["default"]
                transformation_applied = True
                warnings.append(f"Added default value for new required field '{field_name}'")
            else:
                warnings.append(f"New required field '{field_name}' has no default value")

        return transformed, transformation_applied, warnings

    def _transform_avro(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Transform data between Avro schema versions.

        Args:
            source: Source Avro schema
            target: Target Avro schema
            data: Data to transform

        Returns:
            Tuple of (transformed_data, transformation_applied, warnings)
        """
        warnings = []
        transformed = {}
        transformation_applied = False

        source_fields = {f["name"]: f for f in source.get("fields", [])}
        target_fields = {f["name"]: f for f in target.get("fields", [])}

        # Map existing fields
        for field_name, field_value in data.items():
            if field_name in target_fields:
                # Field exists in target, map it
                transformed[field_name] = self._convert_avro_value(
                    field_value,
                    source_fields.get(field_name, {}),
                    target_fields[field_name],
                    warnings
                )
                transformation_applied = True
            else:
                warnings.append(f"Field '{field_name}' removed in target schema, dropping value")

        # Add default values for new fields
        for field_name, field_def in target_fields.items():
            if field_name not in source_fields:
                if "default" in field_def:
                    transformed[field_name] = field_def["default"]
                    transformation_applied = True
                    warnings.append(f"Added default value for new field '{field_name}'")

        return transformed, transformation_applied, warnings

    def _transform_protobuf(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Transform data between Protobuf schema versions.

        Args:
            source: Source Protobuf schema
            target: Target Protobuf schema
            data: Data to transform

        Returns:
            Tuple of (transformed_data, transformation_applied, warnings)
        """
        warnings = []
        transformed = {}
        transformation_applied = False

        # Extract message types
        source_messages = source.get("message_type", [])
        target_messages = target.get("message_type", [])

        if not source_messages or not target_messages:
            warnings.append("Missing message type definitions")
            return data, False, warnings

        source_fields = {f.get("name"): f for f in source_messages[0].get("field", [])}
        target_fields = {f.get("name"): f for f in target_messages[0].get("field", [])}

        # Map existing fields by name
        for field_name, field_value in data.items():
            if field_name in target_fields:
                transformed[field_name] = field_value
                transformation_applied = True
            else:
                warnings.append(f"Field '{field_name}' removed in target schema, dropping value")

        return transformed, transformation_applied, warnings

    def _convert_value(
        self,
        value: Any,
        source_field: Dict[str, Any],
        target_field: Dict[str, Any],
        warnings: List[str]
    ) -> Any:
        """
        Convert value between field types.

        Args:
            value: Value to convert
            source_field: Source field definition
            target_field: Target field definition
            warnings: Warnings list to append to

        Returns:
            Converted value
        """
        source_type = source_field.get("type", "unknown")
        target_type = target_field.get("type", "unknown")

        # Same type, no conversion needed
        if source_type == target_type:
            return value

        # Type conversions
        try:
            if target_type == "string":
                return str(value)
            elif target_type == "integer":
                return int(value)
            elif target_type == "number":
                return float(value)
            elif target_type == "boolean":
                return bool(value)
            else:
                warnings.append(f"Type conversion from {source_type} to {target_type} not supported, keeping original value")
                return value
        except (ValueError, TypeError) as e:
            warnings.append(f"Failed to convert value: {str(e)}, keeping original value")
            return value

    def _convert_avro_value(
        self,
        value: Any,
        source_field: Dict[str, Any],
        target_field: Dict[str, Any],
        warnings: List[str]
    ) -> Any:
        """
        Convert value between Avro field types.

        Args:
            value: Value to convert
            source_field: Source field definition
            target_field: Target field definition
            warnings: Warnings list to append to

        Returns:
            Converted value
        """
        source_type = source_field.get("type", "unknown")
        target_type = target_field.get("type", "unknown")

        # Same type, no conversion needed
        if source_type == target_type:
            return value

        # Type conversions
        try:
            if target_type == "string":
                return str(value)
            elif target_type in ["int", "long"]:
                return int(value)
            elif target_type in ["float", "double"]:
                return float(value)
            elif target_type == "boolean":
                return bool(value)
            else:
                warnings.append(f"Type conversion from {source_type} to {target_type} not supported, keeping original value")
                return value
        except (ValueError, TypeError) as e:
            warnings.append(f"Failed to convert value: {str(e)}, keeping original value")
            return value
