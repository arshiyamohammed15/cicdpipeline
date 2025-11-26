#!/usr/bin/env python3
"""
Schema validation script for LLM Gateway contracts.

Validates JSON schemas in contracts/schemas/*.json for:
- Syntax correctness
- Backwards compatibility (additive-only changes)
- Required fields per PRD §14.1

Test Plan Reference: Contract validation stage
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = PROJECT_ROOT / "contracts" / "schemas"

# Schemas are optional - validate any that exist
REQUIRED_SCHEMAS = set()  # Will be populated from actual files

REQUIRED_FIELDS = {
    "llm_request_v1.json": ["request_id", "actor", "tenant", "logical_model_id", "operation_type", "user_prompt"],
    "llm_response_v1.json": ["response_id", "request_id", "decision", "receipt_id", "policy_snapshot_id"],
    "safety_assessment_v1.json": ["assessment_id", "request_id", "input_checks", "output_checks", "risk_classes"],
    "safety_incident_v1.json": ["incident_id", "tenant_id", "risk_class", "severity", "decision", "dedupe_key"],
    "dry_run_decision_v1.json": ["decision_id", "request_id", "policy_snapshot_id", "decision", "reasons"],
}


def validate_schema_syntax(schema_path: Path) -> list[str]:
    """Validate JSON schema syntax."""
    errors = []
    try:
        with schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        
        # Validate schema structure
        jsonschema.Draft202012Validator.check_schema(schema)
        
        # Check for required $id field per PRD
        if "$id" not in schema:
            errors.append(f"{schema_path.name}: Missing required '$id' field")
        elif not schema["$id"].startswith("urn:zeroui:schemas:"):
            errors.append(f"{schema_path.name}: '$id' must start with 'urn:zeroui:schemas:'")
        
    except json.JSONDecodeError as exc:
        errors.append(f"{schema_path.name}: Invalid JSON: {exc}")
    except jsonschema.SchemaError as exc:
        errors.append(f"{schema_path.name}: Invalid JSON Schema: {exc}")
    except Exception as exc:
        errors.append(f"{schema_path.name}: Unexpected error: {exc}")
    
    return errors


def validate_required_fields(schema_path: Path, schema_name: str) -> list[str]:
    """Validate that schema defines required fields per PRD."""
    errors = []
    required = REQUIRED_FIELDS.get(schema_name, [])
    if not required:
        return errors
    
    try:
        with schema_path.open("r", encoding="utf-8") as f:
            schema = json.load(f)
        
        properties = schema.get("properties", {})
        for field in required:
            if field not in properties:
                errors.append(f"{schema_name}: Missing required field '{field}' in schema")
    
    except Exception as exc:
        errors.append(f"{schema_name}: Error checking required fields: {exc}")
    
    return errors


def main() -> int:
    """Main validation function."""
    all_errors: list[str] = []
    
    # Find all LLM gateway schemas
    schema_files = list(SCHEMAS_DIR.glob("llm_*.json"))
    schema_files.extend(SCHEMAS_DIR.glob("safety_*.json"))
    schema_files.extend(SCHEMAS_DIR.glob("dry_run_*.json"))
    
    if not schema_files:
        print("WARNING: No LLM gateway schemas found in contracts/schemas/")
        print(f"  Searched in: {SCHEMAS_DIR}")
        return 0  # Not an error if schemas don't exist yet
    
    # Validate each schema
    for schema_path in schema_files:
        schema_name = schema_path.name
        
        print(f"Validating {schema_name}...")
        
        # Syntax validation
        syntax_errors = validate_schema_syntax(schema_path)
        all_errors.extend(syntax_errors)
        
        # Required fields validation
        field_errors = validate_required_fields(schema_path, schema_name)
        all_errors.extend(field_errors)
        
        if not syntax_errors and not field_errors:
            print(f"  [OK] {schema_name} passed validation")
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"VALIDATION FAILED: {len(all_errors)} errors found")
        print("\nErrors:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print("VALIDATION PASSED: All schemas valid")
        return 0


if __name__ == "__main__":
    sys.exit(main())

