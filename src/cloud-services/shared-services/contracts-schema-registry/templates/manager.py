"""
Template library manager for Contracts & Schema Registry.

What: Template creation, management, and instantiation per PRD
Why: Provides pre-built templates for common patterns
Reads/Writes: Reads template definitions, writes instantiated schemas
Contracts: PRD template specification
Risks: Template misuse, incorrect instantiation
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database.connection import get_session
from ..database.models import Schema
from ..services import SchemaService

logger = logging.getLogger(__name__)

# Pre-built templates per PRD
TEMPLATES = {
    "user_profile": {
        "name": "user_profile",
        "description": "User profile schema template",
        "schema_definition": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "name": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"}
            },
            "required": ["id", "email"]
        },
        "required_fields": ["id", "email"],
        "optional_fields": ["name", "created_at"],
        "validation_rules": []
    },
    "api_error": {
        "name": "api_error",
        "description": "API error response template",
        "schema_definition": {
            "type": "object",
            "properties": {
                "error_code": {"type": "string"},
                "message": {"type": "string"},
                "details": {"type": "object"}
            },
            "required": ["error_code", "message"]
        },
        "required_fields": ["error_code", "message"],
        "optional_fields": ["details"],
        "validation_rules": []
    },
    "audit_event": {
        "name": "audit_event",
        "description": "Audit event template",
        "schema_definition": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string"},
                "timestamp": {"type": "string", "format": "date-time"},
                "action": {"type": "string"},
                "actor": {"type": "string"}
            },
            "required": ["event_id", "timestamp", "action"]
        },
        "required_fields": ["event_id", "timestamp", "action"],
        "optional_fields": ["actor"],
        "validation_rules": []
    },
    "pagination": {
        "name": "pagination",
        "description": "Pagination response template",
        "schema_definition": {
            "type": "object",
            "properties": {
                "items": {"type": "array"},
                "total": {"type": "integer"},
                "limit": {"type": "integer"},
                "offset": {"type": "integer"}
            },
            "required": ["items", "total"]
        },
        "required_fields": ["items", "total"],
        "optional_fields": ["limit", "offset"],
        "validation_rules": []
    },
    "address": {
        "name": "address",
        "description": "Address template",
        "schema_definition": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "zip": {"type": "string"},
                "country": {"type": "string"}
            },
            "required": ["street", "city", "country"]
        },
        "required_fields": ["street", "city", "country"],
        "optional_fields": ["state", "zip"],
        "validation_rules": []
    }
}


class TemplateManager:
    """
    Template library manager.

    Per PRD: Template CRUD operations, template instantiation with overrides.
    """

    def __init__(self):
        """Initialize template manager."""
        self.templates = TEMPLATES.copy()

    def list_templates(self, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available templates.

        Args:
            pattern: Optional name pattern filter

        Returns:
            List of template definitions
        """
        templates = list(self.templates.values())

        if pattern:
            templates = [
                t for t in templates
                if pattern.lower() in t["name"].lower()
            ]

        return templates

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get template by ID.

        Args:
            template_id: Template identifier (name)

        Returns:
            Template definition or None
        """
        return self.templates.get(template_id)

    def instantiate_template(
        self,
        template_id: str,
        name: str,
        namespace: str,
        compatibility: str,
        tenant_id: str,
        created_by: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Instantiate template into a schema.

        Args:
            template_id: Template identifier
            name: Schema name
            namespace: Schema namespace
            compatibility: Compatibility mode
            tenant_id: Tenant identifier
            created_by: Creator identifier
            overrides: Optional schema definition overrides

        Returns:
            Created schema metadata
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template '{template_id}' not found")

        # Start with template schema definition
        schema_definition = template["schema_definition"].copy()

        # Apply overrides
        if overrides:
            schema_definition.update(overrides)

        # Create schema using SchemaService
        schema_service = SchemaService()
        request_data = {
            "schema_type": "json_schema",
            "schema_definition": schema_definition,
            "compatibility": compatibility,
            "name": name,
            "namespace": namespace,
            "metadata": {
                "template_id": template_id,
                "template_name": template["name"],
                "description": template["description"]
            }
        }

        schema = schema_service.register_schema(
            request_data,
            tenant_id,
            created_by
        )

        return schema.model_dump()
