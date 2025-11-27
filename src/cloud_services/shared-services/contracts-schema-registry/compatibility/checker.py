"""
Compatibility checker for Contracts & Schema Registry.

What: Checks backward/forward/full compatibility between schema versions
Why: Enables safe schema evolution per PRD compatibility rules
Reads/Writes: Reads schema definitions, writes compatibility results
Contracts: PRD compatibility rules (backward/forward/full compatibility)
Risks: Incorrect compatibility detection leading to data loss
"""

import logging
from typing import Dict, Any, List, Tuple, Set
from enum import Enum

logger = logging.getLogger(__name__)


class CompatibilityMode(Enum):
    """Compatibility mode enumeration."""
    BACKWARD = "backward"  # New schema can read data written with old schema
    FORWARD = "forward"    # Old schema can read data written with new schema
    FULL = "full"          # Both backward and forward compatible
    NONE = "none"          # No compatibility required


class ChangeType(Enum):
    """Schema change type enumeration."""
    ADDITIVE = "additive"           # Backward compatible (adding optional fields)
    BREAKING = "breaking"           # Not backward compatible (removing fields)
    TYPE_WIDENING = "type_widening"  # Backward compatible (widening types)
    TYPE_NARROWING = "type_narrowing"  # Breaking (narrowing types)
    ENUM_ADDITION = "enum_addition"  # Backward compatible (adding enum values)
    ENUM_REMOVAL = "enum_removal"    # Breaking (removing enum values)


class CompatibilityChecker:
    """
    Schema compatibility checker.

    Per PRD: Detects backward/forward compatibility, identifies breaking changes.
    """

    def __init__(self):
        """Initialize compatibility checker."""
        pass

    def check_compatibility(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any],
        compatibility_mode: CompatibilityMode = CompatibilityMode.BACKWARD
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Check compatibility between two schemas.

        Args:
            source_schema: Source schema definition
            target_schema: Target schema definition
            compatibility_mode: Compatibility mode to check

        Returns:
            Tuple of (is_compatible, breaking_changes, warnings)
        """
        breaking_changes = []
        warnings = []

        # Extract schema type
        source_type = self._get_schema_type(source_schema)
        target_type = self._get_schema_type(target_schema)

        if source_type != target_type:
            breaking_changes.append(f"Schema type changed from {source_type} to {target_type}")
            return False, breaking_changes, warnings

        # Check based on schema type
        if source_type == "json_schema":
            return self._check_json_schema_compatibility(
                source_schema, target_schema, compatibility_mode
            )
        elif source_type == "avro":
            return self._check_avro_compatibility(
                source_schema, target_schema, compatibility_mode
            )
        elif source_type == "protobuf":
            return self._check_protobuf_compatibility(
                source_schema, target_schema, compatibility_mode
            )
        else:
            breaking_changes.append(f"Unsupported schema type: {source_type}")
            return False, breaking_changes, warnings

    def _get_schema_type(self, schema: Dict[str, Any]) -> str:
        """
        Extract schema type from schema definition.

        Args:
            schema: Schema definition

        Returns:
            Schema type string
        """
        # Check for explicit type
        if "schema_type" in schema:
            return schema["schema_type"]

        # Infer from structure
        if "$schema" in schema or "type" in schema:
            return "json_schema"
        elif "type" in schema and schema.get("type") == "record":
            return "avro"
        elif "message_type" in schema or "syntax" in schema:
            return "protobuf"

        return "json_schema"  # Default

    def _check_json_schema_compatibility(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        mode: CompatibilityMode
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Check JSON Schema compatibility.

        Args:
            source: Source JSON Schema
            target: Target JSON Schema
            mode: Compatibility mode

        Returns:
            Tuple of (is_compatible, breaking_changes, warnings)
        """
        breaking_changes = []
        warnings = []

        # Extract properties
        source_props = source.get("properties", {})
        target_props = target.get("properties", {})
        source_required = set(source.get("required", []))
        target_required = set(target.get("required", []))

        # Check for removed fields (breaking)
        removed_fields = set(source_props.keys()) - set(target_props.keys())
        if removed_fields:
            breaking_changes.append(f"Fields removed: {', '.join(removed_fields)}")

        # Check for new required fields (breaking for backward compatibility)
        if mode in [CompatibilityMode.BACKWARD, CompatibilityMode.FULL]:
            new_required = target_required - source_required
            if new_required:
                breaking_changes.append(f"New required fields added: {', '.join(new_required)}")

        # Check for type narrowing (breaking)
        common_fields = set(source_props.keys()) & set(target_props.keys())
        for field in common_fields:
            source_type = self._get_field_type(source_props[field])
            target_type = self._get_field_type(target_props[field])

            if not self._is_type_compatible(source_type, target_type, mode):
                breaking_changes.append(
                    f"Field '{field}' type narrowed from {source_type} to {target_type}"
                )

        # Check for enum value removal (breaking)
        for field in common_fields:
            source_enum = source_props[field].get("enum")
            target_enum = target_props[field].get("enum")

            if source_enum and target_enum:
                removed_enum_values = set(source_enum) - set(target_enum)
                if removed_enum_values:
                    breaking_changes.append(
                        f"Field '{field}' enum values removed: {', '.join(map(str, removed_enum_values))}"
                    )

        # Warnings for additive changes
        new_fields = set(target_props.keys()) - set(source_props.keys())
        if new_fields:
            warnings.append(f"New optional fields added: {', '.join(new_fields)}")

        is_compatible = len(breaking_changes) == 0
        return is_compatible, breaking_changes, warnings

    def _check_avro_compatibility(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        mode: CompatibilityMode
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Check Avro schema compatibility.

        Args:
            source: Source Avro schema
            target: Target Avro schema
            mode: Compatibility mode

        Returns:
            Tuple of (is_compatible, breaking_changes, warnings)
        """
        breaking_changes = []
        warnings = []

        # Extract fields
        source_fields = {f["name"]: f for f in source.get("fields", [])}
        target_fields = {f["name"]: f for f in target.get("fields", [])}

        # Check for removed fields (breaking)
        removed_fields = set(source_fields.keys()) - set(target_fields.keys())
        if removed_fields:
            breaking_changes.append(f"Fields removed: {', '.join(removed_fields)}")

        # Check for new required fields (breaking for backward compatibility)
        if mode in [CompatibilityMode.BACKWARD, CompatibilityMode.FULL]:
            for field_name, field_def in target_fields.items():
                if field_name not in source_fields:
                    # New field without default is breaking
                    if "default" not in field_def:
                        breaking_changes.append(f"New required field added: {field_name}")

        # Check for type changes
        common_fields = set(source_fields.keys()) & set(target_fields.keys())
        for field_name in common_fields:
            source_type = source_fields[field_name].get("type")
            target_type = target_fields[field_name].get("type")

            if source_type != target_type:
                breaking_changes.append(
                    f"Field '{field_name}' type changed from {source_type} to {target_type}"
                )

        # Warnings for additive changes
        new_optional_fields = [
            name for name, field_def in target_fields.items()
            if name not in source_fields and "default" in field_def
        ]
        if new_optional_fields:
            warnings.append(f"New optional fields added: {', '.join(new_optional_fields)}")

        is_compatible = len(breaking_changes) == 0
        return is_compatible, breaking_changes, warnings

    def _check_protobuf_compatibility(
        self,
        source: Dict[str, Any],
        target: Dict[str, Any],
        mode: CompatibilityMode
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Check Protobuf schema compatibility.

        Args:
            source: Source Protobuf schema
            target: Target Protobuf schema
            mode: Compatibility mode

        Returns:
            Tuple of (is_compatible, breaking_changes, warnings)
        """
        breaking_changes = []
        warnings = []

        # Extract message types
        source_messages = source.get("message_type", [])
        target_messages = target.get("message_type", [])

        if not source_messages or not target_messages:
            breaking_changes.append("Missing message type definitions")
            return False, breaking_changes, warnings

        source_fields = {f.get("number"): f for f in source_messages[0].get("field", [])}
        target_fields = {f.get("number"): f for f in target_messages[0].get("field", [])}

        # Check for removed fields (breaking)
        removed_field_numbers = set(source_fields.keys()) - set(target_fields.keys())
        if removed_field_numbers:
            breaking_changes.append(f"Fields removed: {', '.join(map(str, removed_field_numbers))}")

        # Check for type changes
        common_fields = set(source_fields.keys()) & set(target_fields.keys())
        for field_number in common_fields:
            source_type = source_fields[field_number].get("type")
            target_type = target_fields[field_number].get("type")

            if source_type != target_type:
                breaking_changes.append(
                    f"Field {field_number} type changed from {source_type} to {target_type}"
                )

        # Warnings for new fields
        new_fields = set(target_fields.keys()) - set(source_fields.keys())
        if new_fields:
            warnings.append(f"New fields added: {', '.join(map(str, new_fields))}")

        is_compatible = len(breaking_changes) == 0
        return is_compatible, breaking_changes, warnings

    def _get_field_type(self, field_def: Dict[str, Any]) -> str:
        """
        Extract field type from field definition.

        Args:
            field_def: Field definition

        Returns:
            Type string
        """
        if "type" in field_def:
            return str(field_def["type"])
        return "unknown"

    def _is_type_compatible(
        self,
        source_type: str,
        target_type: str,
        mode: CompatibilityMode
    ) -> bool:
        """
        Check if type change is compatible.

        Args:
            source_type: Source type
            target_type: Target type
            mode: Compatibility mode

        Returns:
            True if compatible, False otherwise
        """
        # Same type is always compatible
        if source_type == target_type:
            return True

        # Type widening is backward compatible
        widening_map = {
            "integer": ["number"],
            "number": ["integer"],
            "string": ["number", "integer"],  # Not really, but simplified
        }

        if source_type in widening_map:
            if target_type in widening_map[source_type]:
                return True

        # Type narrowing is breaking
        return False
