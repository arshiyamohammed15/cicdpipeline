"""
Event payload schemas for ZeroUI Observability Layer.

Contains JSON Schema definitions for all 12 required event types.
"""

from .schema_loader import load_schema, validate_payload, get_schema_path

__all__ = ["load_schema", "validate_payload", "get_schema_path"]
