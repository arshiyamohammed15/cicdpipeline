"""
Schema Guard processor for OpenTelemetry Collector.

Validates zero_ui.obsv.event.v1 envelope and payload schemas.
"""

from .schema_guard_processor import SchemaGuardProcessor

__all__ = ["SchemaGuardProcessor"]
