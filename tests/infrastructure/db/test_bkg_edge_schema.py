"""
Test suite for BKG Edge Schema validation.

Tests cover:
- JSON Schema contract validation
- Valid BKG edge creation
- Invalid entity types
- Invalid edge types
- Missing required fields
- Metadata handling
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BKG_SCHEMA_PATH = REPO_ROOT / "contracts" / "bkg" / "schemas" / "bkg_edge.schema.json"


@pytest.fixture
def bkg_schema() -> dict:
    """Load BKG edge JSON schema."""
    with open(BKG_SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def valid_bkg_edge() -> dict:
    """Valid BKG edge example."""
    return {
        "edge_id": "edge-123",
        "source_entity_type": "tenant",
        "source_entity_id": "tenant-1",
        "target_entity_type": "repo",
        "target_entity_id": "repo-1",
        "edge_type": "owns",
        "created_at": "2026-01-03T12:00:00Z",
    }


class TestBkgEdgeSchemaStructure:
    """Test BKG edge JSON schema structure."""

    def test_schema_has_required_fields(self, bkg_schema: dict) -> None:
        """Schema must define required fields."""
        assert "required" in bkg_schema
        required = set(bkg_schema["required"])
        expected_required = {
            "edge_id",
            "source_entity_type",
            "source_entity_id",
            "target_entity_type",
            "target_entity_id",
            "edge_type",
        }
        assert required == expected_required

    def test_schema_has_entity_type_enum(self, bkg_schema: dict) -> None:
        """Schema must define entity type enum."""
        source_prop = bkg_schema["properties"]["source_entity_type"]
        target_prop = bkg_schema["properties"]["target_entity_type"]

        assert "enum" in source_prop
        assert "enum" in target_prop

        expected_entity_types = {"tenant", "repo", "actor", "receipt", "policy", "gate", "signal", "event"}
        assert set(source_prop["enum"]) == expected_entity_types
        assert set(target_prop["enum"]) == expected_entity_types

    def test_schema_has_edge_type_enum(self, bkg_schema: dict) -> None:
        """Schema must define edge type enum."""
        edge_type_prop = bkg_schema["properties"]["edge_type"]

        assert "enum" in edge_type_prop

        expected_edge_types = {
            "owns",
            "contains",
            "triggers",
            "references",
            "depends_on",
            "belongs_to",
            "causes",
            "precedes",
        }
        assert set(edge_type_prop["enum"]) == expected_edge_types

    def test_schema_metadata_is_optional(self, bkg_schema: dict) -> None:
        """Metadata field must be optional."""
        assert "metadata" not in bkg_schema["required"]
        metadata_prop = bkg_schema["properties"]["metadata"]
        assert metadata_prop["type"] == "object"
        assert metadata_prop.get("additionalProperties") is True


class TestBkgEdgeValidation:
    """Test BKG edge validation against schema."""

    def test_valid_bkg_edge_passes(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """Valid BKG edge must pass validation."""
        jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_with_metadata_passes(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with metadata must pass validation."""
        valid_bkg_edge["metadata"] = {"weight": 0.8, "confidence": 0.95}
        jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_missing_edge_id_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge missing edge_id must fail validation."""
        del valid_bkg_edge["edge_id"]
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "edge_id" in str(exc_info.value)

    def test_bkg_edge_missing_source_entity_type_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge missing source_entity_type must fail validation."""
        del valid_bkg_edge["source_entity_type"]
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "source_entity_type" in str(exc_info.value)

    def test_bkg_edge_missing_source_entity_id_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge missing source_entity_id must fail validation."""
        del valid_bkg_edge["source_entity_id"]
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "source_entity_id" in str(exc_info.value)

    def test_bkg_edge_missing_target_entity_type_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge missing target_entity_type must fail validation."""
        del valid_bkg_edge["target_entity_type"]
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "target_entity_type" in str(exc_info.value)

    def test_bkg_edge_missing_target_entity_id_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge missing target_entity_id must fail validation."""
        del valid_bkg_edge["target_entity_id"]
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "target_entity_id" in str(exc_info.value)

    def test_bkg_edge_missing_edge_type_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge missing edge_type must fail validation."""
        del valid_bkg_edge["edge_type"]
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "edge_type" in str(exc_info.value)

    def test_bkg_edge_invalid_source_entity_type_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with invalid source_entity_type must fail validation."""
        valid_bkg_edge["source_entity_type"] = "invalid_type"
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "source_entity_type" in str(exc_info.value) or "invalid_type" in str(exc_info.value)

    def test_bkg_edge_invalid_target_entity_type_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with invalid target_entity_type must fail validation."""
        valid_bkg_edge["target_entity_type"] = "invalid_type"
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "target_entity_type" in str(exc_info.value) or "invalid_type" in str(exc_info.value)

    def test_bkg_edge_invalid_edge_type_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with invalid edge_type must fail validation."""
        valid_bkg_edge["edge_type"] = "invalid_edge"
        with pytest.raises(jsonschema.ValidationError) as exc_info:
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)
        assert "edge_type" in str(exc_info.value) or "invalid_edge" in str(exc_info.value)

    def test_bkg_edge_all_valid_entity_types_pass(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with all valid entity types must pass validation."""
        valid_entity_types = ["tenant", "repo", "actor", "receipt", "policy", "gate", "signal", "event"]
        for source_type in valid_entity_types:
            for target_type in valid_entity_types:
                valid_bkg_edge["source_entity_type"] = source_type
                valid_bkg_edge["target_entity_type"] = target_type
                jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_all_valid_edge_types_pass(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with all valid edge types must pass validation."""
        valid_edge_types = ["owns", "contains", "triggers", "references", "depends_on", "belongs_to", "causes", "precedes"]
        for edge_type in valid_edge_types:
            valid_bkg_edge["edge_type"] = edge_type
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_empty_metadata_passes(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with empty metadata object must pass validation."""
        valid_bkg_edge["metadata"] = {}
        jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_complex_metadata_passes(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with complex metadata must pass validation."""
        valid_bkg_edge["metadata"] = {
            "weight": 0.75,
            "confidence": 0.9,
            "tags": ["important", "verified"],
            "nested": {"key": "value"},
        }
        jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_non_string_edge_id_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with non-string edge_id must fail validation."""
        valid_bkg_edge["edge_id"] = 123
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_non_string_entity_id_fails(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with non-string entity_id must fail validation."""
        valid_bkg_edge["source_entity_id"] = 123
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

    def test_bkg_edge_empty_strings_pass(self, bkg_schema: dict, valid_bkg_edge: dict) -> None:
        """BKG edge with empty string IDs must pass (schema allows empty strings)."""
        valid_bkg_edge["edge_id"] = ""
        valid_bkg_edge["source_entity_id"] = ""
        valid_bkg_edge["target_entity_id"] = ""
        # Empty strings are valid per schema (type: string, no minLength)
        jsonschema.validate(instance=valid_bkg_edge, schema=bkg_schema)

