from __future__ import annotations

from src.shared_libs.tool_schema_validation import (
    TOOL_SCHEMA_INVALID,
    ToolOutputValidator,
    ToolSchemaRegistry,
)


def _sample_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["id", "status"],
        "properties": {
            "id": {"type": "string"},
            "status": {"type": "string"},
            "count": {"type": "integer"},
        },
    }


def test_tool_output_validator_allows_valid_payload() -> None:
    registry = ToolSchemaRegistry()
    registry.register("tool.sample", _sample_schema(), "1.0.0")
    validator = ToolOutputValidator(registry)

    result = validator.validate("tool.sample", {"id": "abc", "status": "ok", "count": 1})

    assert result.ok is True
    assert result.reason_code is None
    assert result.details is None
    assert result.schema_version == "1.0.0"


def test_tool_output_validator_denies_missing_required_field() -> None:
    registry = ToolSchemaRegistry()
    registry.register("tool.sample", _sample_schema(), "1.0.0")
    validator = ToolOutputValidator(registry)

    result = validator.validate("tool.sample", {"id": "abc"})

    assert result.ok is False
    assert result.reason_code == TOOL_SCHEMA_INVALID
    assert result.details is not None
    assert result.details.get("errors")
    assert result.schema_version == "1.0.0"
