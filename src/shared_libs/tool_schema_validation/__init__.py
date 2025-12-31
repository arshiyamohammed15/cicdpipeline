"""
Tool output schema validation helpers.

Uses jsonschema if available; otherwise falls back to a minimal required-key and
type-check validator. The fallback only supports a small subset of JSON Schema.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

try:  # pragma: no cover - optional dependency
    from jsonschema import ValidationError as JSONSchemaValidationError
    from jsonschema.validators import validator_for
except ImportError:  # pragma: no cover - optional dependency
    JSONSchemaValidationError = Exception  # type: ignore[assignment]
    validator_for = None

try:  # pragma: no cover - optional dependency
    from pydantic import BaseModel
    from pydantic import ValidationError as PydanticValidationError
except ImportError:  # pragma: no cover - optional dependency
    BaseModel = None  # type: ignore[assignment]

    class PydanticValidationError(Exception):
        """Fallback validation error when pydantic is unavailable."""


TOOL_SCHEMA_INVALID = "TOOL_SCHEMA_INVALID"


@dataclass(frozen=True)
class ValidationResult:
    """Validation result for tool output payloads."""

    ok: bool
    reason_code: Optional[str] = None
    details: Optional[dict[str, list[str]]] = None
    schema_version: Optional[str] = None


SchemaType = Mapping[str, Any] | type


@dataclass(frozen=True)
class SchemaEntry:
    """Registered tool schema with version metadata."""

    schema: SchemaType
    schema_version: str


class ToolSchemaRegistry:
    """Registry of tool output schemas keyed by tool_id."""

    def __init__(self) -> None:
        self._schemas: dict[str, SchemaEntry] = {}

    def register(self, tool_id: str, schema_or_model: SchemaType, schema_version: str) -> None:
        if not tool_id:
            raise ValueError("tool_id must be a non-empty string")
        if not schema_version:
            raise ValueError("schema_version must be a non-empty string")
        self._schemas[tool_id] = SchemaEntry(
            schema=schema_or_model,
            schema_version=schema_version,
        )

    def get(self, tool_id: str) -> Optional[SchemaEntry]:
        return self._schemas.get(tool_id)


class ToolOutputValidator:
    """Validate tool outputs using the registered schema for a tool_id."""

    def __init__(self, registry: ToolSchemaRegistry) -> None:
        self._registry = registry

    def validate(self, tool_id: str, payload: object) -> ValidationResult:
        entry = self._registry.get(tool_id)
        if entry is None:
            return _error_result(
                [f"No schema registered for tool_id '{tool_id}'."],
                schema_version=None,
            )

        schema = entry.schema
        schema_version = entry.schema_version

        if _is_pydantic_model(schema):
            return _validate_with_pydantic(schema, payload, schema_version)

        if isinstance(schema, Mapping):
            return _validate_with_json_schema(schema, payload, schema_version)

        return _error_result(
            [f"Unsupported schema type for tool_id '{tool_id}'."],
            schema_version=schema_version,
        )


def _is_pydantic_model(schema: SchemaType) -> bool:
    if BaseModel is None:
        return False
    return isinstance(schema, type) and issubclass(schema, BaseModel)


def _validate_with_pydantic(
    model: type,
    payload: object,
    schema_version: str,
) -> ValidationResult:
    try:
        if hasattr(model, "model_validate"):
            model.model_validate(payload)
        else:
            model.parse_obj(payload)  # type: ignore[attr-defined]
    except PydanticValidationError as exc:
        return _error_result([str(exc)], schema_version=schema_version)
    return ValidationResult(ok=True, schema_version=schema_version)


def _validate_with_json_schema(
    schema: Mapping[str, Any],
    payload: object,
    schema_version: str,
) -> ValidationResult:
    if validator_for is None:
        return _validate_with_minimal_schema(schema, payload, schema_version)

    try:
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
        errors = sorted(
            (error.message for error in validator.iter_errors(payload)),
        )
    except JSONSchemaValidationError as exc:
        return _error_result([str(exc.message)], schema_version=schema_version)
    except Exception as exc:
        return _error_result([str(exc)], schema_version=schema_version)

    if errors:
        return _error_result(errors, schema_version=schema_version)
    return ValidationResult(ok=True, schema_version=schema_version)


def _validate_with_minimal_schema(
    schema: Mapping[str, Any],
    payload: object,
    schema_version: str,
) -> ValidationResult:
    """
    Minimal validator for a subset of JSON Schema.

    Supports object schemas with "required" and "properties" type checks only.
    """
    if schema.get("type", "object") != "object":
        return _error_result(
            ["Only object schemas are supported in fallback validator."],
            schema_version=schema_version,
        )

    if not isinstance(payload, Mapping):
        return _error_result(
            ["Payload must be an object for schema validation."],
            schema_version=schema_version,
        )

    required = schema.get("required") or []
    if not isinstance(required, list):
        return _error_result(
            ["Schema 'required' must be a list."],
            schema_version=schema_version,
        )

    properties = schema.get("properties") or {}
    if not isinstance(properties, Mapping):
        return _error_result(
            ["Schema 'properties' must be a mapping."],
            schema_version=schema_version,
        )

    missing = sorted(field for field in required if field not in payload)
    if missing:
        return _error_result(
            [f"Missing required fields: {', '.join(missing)}."],
            schema_version=schema_version,
        )

    type_errors: list[str] = []
    for field_name, field_schema in properties.items():
        if field_name not in payload or not isinstance(field_schema, Mapping):
            continue
        expected = field_schema.get("type")
        if expected is None:
            continue
        if not _matches_json_type(payload[field_name], expected):
            type_errors.append(f"Field '{field_name}' does not match type {expected}.")

    if type_errors:
        return _error_result(sorted(type_errors), schema_version=schema_version)

    return ValidationResult(ok=True, schema_version=schema_version)


def _matches_json_type(value: object, expected: object) -> bool:
    if isinstance(expected, list):
        return any(_matches_json_type(value, item) for item in expected)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, Mapping)
    if expected == "array":
        return isinstance(value, list)
    if expected == "null":
        return value is None
    return False


def _error_result(messages: list[str], schema_version: Optional[str]) -> ValidationResult:
    return ValidationResult(
        ok=False,
        reason_code=TOOL_SCHEMA_INVALID,
        details={"errors": messages},
        schema_version=schema_version,
    )


__all__ = [
    "TOOL_SCHEMA_INVALID",
    "SchemaType",
    "SchemaEntry",
    "ToolOutputValidator",
    "ToolSchemaRegistry",
    "ValidationResult",
]
