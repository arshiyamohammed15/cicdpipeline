"""
ZeroUI Observability Layer - Integration Package.

Contains integration modules for EPC-12, Phase 3, and other services.
"""

from .epc12_schema_registry import (
    EPC12SchemaRegistryClient,
    register_observability_schemas,
)

__all__ = [
    "EPC12SchemaRegistryClient",
    "register_observability_schemas",
]
