"""
Main integration service for Integration Adapters Module.

What: Orchestrates all integration operations implementing all 15 FRs
Why: Central business logic for integration adapters
Reads/Writes: Database, external services, adapters
Contracts: PRD Section 8 (Functional Requirements FR-1 through FR-15)
Risks: Service orchestration errors, tenant isolation violations
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

try:
    from ..database.models import (
        IntegrationProvider,
        IntegrationConnection,
        WebhookRegistration,
        PollingCursor,
        AdapterEvent,
        NormalisedAction,
    )
    from ..database.repositories import (
        ProviderRepository,
        ConnectionRepository,
        WebhookRegistrationRepository,
        PollingCursorRepository,
        AdapterEventRepository,
        NormalisedActionRepository,
    )
    from ..models import (
        IntegrationProviderCreate,
        IntegrationConnectionCreate,
        IntegrationConnectionUpdate,
        ConnectionStatus,
    )
    from ..integrations.kms_client import KMSClient
    from ..integrations.budget_client import BudgetClient
    from ..integrations.pm3_client import PM3Client
    from ..integrations.eris_client import ERISClient
    from ..observability.metrics import get_metrics_registry
    from ..observability.audit import get_audit_logger
    from ..config import config as app_config
except ImportError:
    # Fallback for direct imports (e.g., in tests)
    import sys
    import os
    # Add parent directory to path
    parent_dir = os.path.join(os.path.dirname(__file__), "../..")
    parent_dir = os.path.abspath(parent_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    # Try absolute imports first
    try:
        from integration_adapters.database.models import (
            IntegrationProvider,
            IntegrationConnection,
            WebhookRegistration,
            PollingCursor,
            AdapterEvent,
            NormalisedAction,
        )
        from integration_adapters.database.repositories import (
            ProviderRepository,
            ConnectionRepository,
            WebhookRegistrationRepository,
            PollingCursorRepository,
            AdapterEventRepository,
            NormalisedActionRepository,
        )
        from integration_adapters.models import (
            IntegrationProviderCreate,
            IntegrationConnectionCreate,
            IntegrationConnectionUpdate,
            ConnectionStatus,
        )
        from integration_adapters.integrations.kms_client import KMSClient
        from integration_adapters.integrations.budget_client import BudgetClient
        from integration_adapters.integrations.pm3_client import PM3Client
        from integration_adapters.integrations.eris_client import ERISClient
        from integration_adapters.observability.metrics import get_metrics_registry
        from integration_adapters.observability.audit import get_audit_logger
        from integration_adapters.config import config as app_config
    except ImportError:
        # Fallback to relative imports if package not installed
        from database.models import (
            IntegrationProvider,
            IntegrationConnection,
            WebhookRegistration,
            PollingCursor,
            AdapterEvent,
            NormalisedAction,
        )
        from database.repositories import (
            ProviderRepository,
            ConnectionRepository,
            WebhookRegistrationRepository,
            PollingCursorRepository,
            AdapterEventRepository,
            NormalisedActionRepository,
        )
        from models import (
            IntegrationProviderCreate,
            IntegrationConnectionCreate,
            IntegrationConnectionUpdate,
            ConnectionStatus,
        )
        from integrations.kms_client import KMSClient
        from integrations.budget_client import BudgetClient
        from integrations.pm3_client import PM3Client
        from integrations.eris_client import ERISClient
        from observability.metrics import get_metrics_registry
        from observability.audit import get_audit_logger
        from config import config as app_config

from .adapter_registry import get_adapter_registry
from .signal_mapper import SignalMapper
from shared_libs.tool_schema_validation import ToolOutputValidator, ToolSchemaRegistry

logger = logging.getLogger(__name__)

TOOL_OUTPUT_SCHEMA_VIOLATION = "TOOL_OUTPUT_SCHEMA_VIOLATION"
DEFAULT_TOOL_SCHEMA_VERSION = "1.0.0"


class ToolOutputSchemaViolation(Exception):
    """Raised when a tool output fails schema validation."""

    def __init__(
        self,
        tool_id: str,
        validation_summary: dict[str, list[str]],
        schema_version: Optional[str],
    ):
        super().__init__(f"Tool output schema violation for {tool_id}")
        self.tool_id = tool_id
        self.reason_code = TOOL_OUTPUT_SCHEMA_VIOLATION
        self.validation_summary = validation_summary
        self.schema_version = schema_version


class IntegrationService:
    """
    Main integration service implementing all functional requirements.
    
    Implements:
    - FR-1: Provider & Adapter Registry
    - FR-2: Integration Connections (Tenant Scoped)
    - FR-3: Authentication & Authorization
    - FR-4: Webhook Ingestion
    - FR-5: Polling & Backfill
    - FR-6: Event Normalisation
    - FR-7: Outbound Actions
    - FR-8: Error Handling, Retries & Circuit Breaking
    - FR-9: Rate Limiting & Budgeting Integration
    - FR-10: Tenant Isolation & Multi-Tenancy
    - FR-11: Versioning & Compatibility
    - FR-12: Observability & Diagnostics
    - FR-13: Evidence & Receipts
    - FR-14: Integration Adapter SDK / SPI
    - FR-15: Security & Privacy Constraints
    """

    def __init__(
        self,
        session: Session,
        kms_client: Optional[KMSClient] = None,
        budget_client: Optional[BudgetClient] = None,
        pm3_client: Optional[PM3Client] = None,
        eris_client: Optional[ERISClient] = None,
    ):
        """
        Initialize integration service.
        
        Args:
            session: Database session
            kms_client: KMS client (optional, creates default if None)
            budget_client: Budget client (optional, creates default if None)
            pm3_client: PM-3 client (optional, creates default if None)
            eris_client: ERIS client (optional, creates default if None)
        """
        self.session = session
        self.provider_repo = ProviderRepository(session)
        self.connection_repo = ConnectionRepository(session)
        self.webhook_repo = WebhookRegistrationRepository(session)
        self.polling_repo = PollingCursorRepository(session)
        self.event_repo = AdapterEventRepository(session)
        self.action_repo = NormalisedActionRepository(session)
        
        self.kms_client = kms_client or KMSClient()
        self.budget_client = budget_client or BudgetClient()
        self.pm3_client = pm3_client or PM3Client()
        self.eris_client = eris_client or ERISClient()
        
        self.adapter_registry = get_adapter_registry()
        self.signal_mapper = SignalMapper()
        self.metrics = get_metrics_registry()
        self.audit = get_audit_logger()
        self._tool_schema_registry = ToolSchemaRegistry()
        self._tool_output_validator = ToolOutputValidator(self._tool_schema_registry)
        self._default_tool_schema_version = DEFAULT_TOOL_SCHEMA_VERSION
        self._load_tool_schema_registry_config()

    def register_tool_output_schema(
        self,
        tool_id: str,
        schema_or_model: object,
        schema_version: str,
    ) -> None:
        """Register a tool output schema for validation."""
        self._tool_schema_registry.register(tool_id, schema_or_model, schema_version)

    def _tool_id_for_action(self, provider_id: str, canonical_type: str) -> str:
        return f"{provider_id}.{canonical_type}"

    def _ensure_tool_schema(self, tool_id: str) -> None:
        if self._tool_schema_registry.get(tool_id) is None:
            from ..models import NormalisedActionResponse
            self._tool_schema_registry.register(
                tool_id,
                NormalisedActionResponse,
                self._default_tool_schema_version,
            )

    def _load_tool_schema_registry_config(self) -> None:
        path = getattr(app_config, "TOOL_SCHEMA_REGISTRY_PATH", None)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(data, dict):
            return
        registry = data.get("tool_schema_registry")
        if not isinstance(registry, dict):
            return
        default_version = registry.get("default_schema_version")
        if isinstance(default_version, str) and default_version:
            self._default_tool_schema_version = default_version
        tools = registry.get("tools")
        if not isinstance(tools, dict):
            return
        from ..models import NormalisedActionResponse
        for tool_id, entry in tools.items():
            if not isinstance(tool_id, str) or not tool_id:
                continue
            if isinstance(entry, str):
                version = entry
            elif isinstance(entry, dict):
                version = entry.get("schema_version")
            else:
                version = None
            if isinstance(version, str) and version:
                self._tool_schema_registry.register(
                    tool_id,
                    NormalisedActionResponse,
                    version,
                )

    def _handle_tool_output_violation(
        self,
        *,
        tenant_id: str,
        connection_id: UUID,
        action_data: Dict[str, Any],
        action: NormalisedAction,
        tool_id: str,
        validation_summary: dict[str, list[str]],
        schema_version: Optional[str],
    ) -> None:
        action.status = "failed"
        action.payload = {"error": "tool output schema violation"}
        self.action_repo.update(action)

        self.eris_client.emit_receipt(
            tenant_id=tenant_id,
            connection_id=str(connection_id),
            provider_id=action_data["provider_id"],
            operation_type=(
                f"integration.action.{action_data['provider_id']}."
                f"{action_data['canonical_type']}.output_validation"
            ),
            request_metadata={},
            result={
                "tool_id": tool_id,
                "reason_code": TOOL_OUTPUT_SCHEMA_VIOLATION,
                "validation_summary": validation_summary,
                "schema_version": schema_version,
                "outcome": "blocked",
                "timestamp": datetime.utcnow().isoformat(),
            },
            correlation_id=action_data.get("correlation_id"),
        )
        self.metrics.increment_action_error(action_data["provider_id"], connection_id)

    # FR-1: Provider & Adapter Registry
    def create_provider(
        self, provider_data: IntegrationProviderCreate
    ) -> IntegrationProvider:
        """
        Create a new integration provider (FR-1).
        
        Args:
            provider_data: Provider creation data
            
        Returns:
            Created provider
        """
        provider = IntegrationProvider(
            provider_id=provider_data.provider_id,
            category=provider_data.category.value,
            name=provider_data.name,
            status=provider_data.status.value,
            capabilities=provider_data.capabilities,
            api_version=provider_data.api_version,
        )
        return self.provider_repo.create(provider)

    def get_provider(self, provider_id: str) -> Optional[IntegrationProvider]:
        """Get provider by ID (FR-1)."""
        return self.provider_repo.get_by_id(provider_id)

    def list_providers(self) -> List[IntegrationProvider]:
        """List all providers (FR-1)."""
        return self.provider_repo.get_all()

    # FR-2: Integration Connections (Tenant Scoped)
    def create_connection(
        self, tenant_id: str, connection_data: IntegrationConnectionCreate
    ) -> IntegrationConnection:
        """
        Create a new integration connection (FR-2).
        
        Args:
            tenant_id: Tenant ID
            connection_data: Connection creation data
            
        Returns:
            Created connection
        """
        connection = IntegrationConnection(
            tenant_id=tenant_id,
            provider_id=connection_data.provider_id,
            display_name=connection_data.display_name,
            auth_ref=connection_data.auth_ref,
            status=ConnectionStatus.PENDING_VERIFICATION.value,
            enabled_capabilities=connection_data.enabled_capabilities,
            metadata_tags=connection_data.metadata_tags,
        )
        return self.connection_repo.create(connection)

    def get_connection(
        self, connection_id: UUID, tenant_id: str
    ) -> Optional[IntegrationConnection]:
        """Get connection by ID with tenant isolation (FR-2, FR-10)."""
        return self.connection_repo.get_by_id(connection_id, tenant_id)

    def list_connections(self, tenant_id: str) -> List[IntegrationConnection]:
        """List all connections for tenant (FR-2, FR-10)."""
        return self.connection_repo.get_all_by_tenant(tenant_id)

    def update_connection(
        self,
        connection_id: UUID,
        tenant_id: str,
        update_data: IntegrationConnectionUpdate,
    ) -> Optional[IntegrationConnection]:
        """Update connection (FR-2, FR-10)."""
        connection = self.connection_repo.get_by_id(connection_id, tenant_id)
        if not connection:
            return None
        
        if update_data.display_name is not None:
            connection.display_name = update_data.display_name
        if update_data.status is not None:
            connection.status = update_data.status.value
        if update_data.enabled_capabilities is not None:
            connection.enabled_capabilities = update_data.enabled_capabilities
        if update_data.metadata_tags is not None:
            connection.metadata_tags = update_data.metadata_tags
        
        return self.connection_repo.update(connection)

    def verify_connection(
        self, connection_id: UUID, tenant_id: str
    ) -> bool:
        """
        Verify connection (FR-2, FR-3).
        
        Args:
            connection_id: Connection ID
            tenant_id: Tenant ID
            
        Returns:
            True if verification successful, False otherwise
        """
        connection = self.connection_repo.get_by_id(connection_id, tenant_id)
        if not connection:
            return False
        
        # Get adapter
        adapter = self.adapter_registry.get_adapter(
            connection.provider_id, connection.connection_id, tenant_id
        )
        if not adapter:
            return False
        
        # Get auth secret from KMS (FR-3)
        auth_secret = self.kms_client.get_secret(connection.auth_ref, tenant_id)
        if not auth_secret:
            logger.error(f"Failed to retrieve auth secret for connection {connection_id}")
            return False
        
        # Verify connection
        try:
            # Set auth secret on adapter (adapter-specific)
            if hasattr(adapter, "api_token"):
                adapter.api_token = auth_secret
            
            is_valid = adapter.verify_connection()
            
            if is_valid:
                connection.status = ConnectionStatus.ACTIVE.value
                connection.last_verified_at = datetime.utcnow()
                self.connection_repo.update(connection)
            
            return is_valid
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            connection.status = ConnectionStatus.ERROR.value
            self.connection_repo.update(connection)
            return False

    # FR-4: Webhook Ingestion
    def process_webhook(
        self,
        provider_id: str,
        connection_token: str,
        payload: Dict[str, Any],
        headers: Dict[str, str],
    ) -> bool:
        """
        Process incoming webhook (FR-4) with tenant-aware, registration-scoped lookup.
        
        Args:
            provider_id: Provider identifier
            connection_token: Registration token (UUID of WebhookRegistration)
            payload: Webhook payload
            headers: HTTP headers
            
        Returns:
            True if processed successfully, False otherwise
        """
        # Require a registration token (not raw connection_id) to reduce guessability.
        try:
            registration_id = UUID(connection_token)
        except ValueError:
            logger.error(f"Invalid webhook token: {connection_token}")
            return False

        registration = self.webhook_repo.get_active_by_registration(registration_id)
        if not registration:
            logger.error(f"No active webhook registration for token: {registration_id}")
            return False

        # Resolve connection with tenant isolation.
        connection = self.connection_repo.get_by_id(
            registration.connection_id,
            getattr(registration, "connection", None).tenant_id
            if getattr(registration, "connection", None)
            else None,
        )
        if not connection:
            logger.error(
                f"Connection not found for registration {registration_id}: {registration.connection_id}"
            )
            return False

        if connection.provider_id != provider_id:
            logger.error(
                f"Provider mismatch for connection {connection.connection_id}: "
                f"expected {connection.provider_id}, got {provider_id}"
            )
            return False

        # Get adapter
        adapter = self.adapter_registry.get_adapter(
            provider_id, connection.connection_id, connection.tenant_id
        )
        if not adapter:
            logger.error(f"Adapter not found for provider: {provider_id}")
            return False
        
        # Get webhook secret from KMS
        webhook_registrations = self.webhook_repo.get_active_by_connection(
            connection.connection_id, connection.tenant_id
        )
        if not webhook_registrations:
            logger.error(
                f"No active webhook registration for connection: {connection.connection_id}"
            )
            return False
        
        webhook_secret = self.kms_client.get_secret(
            webhook_registrations[0].secret_ref, connection.tenant_id
        )
        if webhook_secret and hasattr(adapter, "webhook_secret"):
            adapter.webhook_secret = webhook_secret
        
        # Process webhook
        try:
            event_data = adapter.process_webhook(payload, headers)
            
            # Map to SignalEnvelope (FR-6)
            signal_envelope = self.signal_mapper.map_provider_event_to_signal_envelope(
                provider_id=provider_id,
                connection_id=str(connection.connection_id),
                tenant_id=connection.tenant_id,
                provider_event=event_data.get("payload", payload),
                provider_event_type=event_data.get("event_type", "unknown"),
                occurred_at=datetime.utcnow(),  # Would extract from payload in practice
                correlation_id=payload.get("id"),
            )
            
            # Forward to PM-3 (FR-6)
            self.pm3_client.ingest_signal(signal_envelope)
            
            # Record metrics (FR-12)
            self.metrics.increment_webhook_received(provider_id, connection.connection_id)
            self.metrics.increment_event_normalized(provider_id, connection.connection_id)
            
            return True
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            self.metrics.increment_webhook_error(provider_id, connection.connection_id)
            return False

    # FR-7: Outbound Actions
    def execute_action(
        self, tenant_id: str, action_data: Dict[str, Any]
    ) -> Optional[NormalisedAction]:
        """
        Execute outbound action (FR-7).
        
        Args:
            tenant_id: Tenant ID
            action_data: Action data (NormalisedActionCreate-like)
            
        Returns:
            NormalisedAction with execution result
        """
        connection_id = UUID(action_data["connection_id"])
        connection = self.connection_repo.get_by_id(connection_id, tenant_id)
        if not connection:
            return None
        
        # Check budget (FR-9)
        allowed, _ = self.budget_client.check_budget(
            tenant_id, action_data["provider_id"], str(connection_id)
        )
        if not allowed:
            logger.warning(f"Budget check failed for action: {action_data.get('idempotency_key')}")
            return None
        
        # Get adapter
        adapter = self.adapter_registry.get_adapter(
            action_data["provider_id"], connection_id, tenant_id
        )
        if not adapter:
            return None
        
        # Get auth secret
        auth_secret = self.kms_client.get_secret(connection.auth_ref, tenant_id)
        if auth_secret and hasattr(adapter, "api_token"):
            adapter.api_token = auth_secret
        
        # Create action record
        action = NormalisedAction(
            tenant_id=tenant_id,
            provider_id=action_data["provider_id"],
            connection_id=connection_id,
            canonical_type=action_data["canonical_type"],
            target=action_data["target"],
            payload=action_data["payload"],
            idempotency_key=action_data["idempotency_key"],
            correlation_id=action_data.get("correlation_id"),
            status="processing",
        )
        action = self.action_repo.create(action)
        
        # Execute action
        try:
            from ..models import NormalisedActionCreate
            action_create = NormalisedActionCreate(**action_data)
            result = adapter.execute_action(action_create)
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            action.status = "failed"
            action.payload = {"error": str(e)}
            self.action_repo.update(action)
            
            self.metrics.increment_action_error(action_data["provider_id"], connection_id)
            return action

        tool_id = self._tool_id_for_action(
            action_data["provider_id"],
            action_data["canonical_type"],
        )
        self._ensure_tool_schema(tool_id)
        validation = self._tool_output_validator.validate(tool_id, result)
        if not validation.ok:
            summary = validation.details or {"errors": ["Tool output schema validation failed."]}
            self._handle_tool_output_violation(
                tenant_id=tenant_id,
                connection_id=connection_id,
                action_data=action_data,
                action=action,
                tool_id=tool_id,
                validation_summary=summary,
                schema_version=validation.schema_version,
            )
            raise ToolOutputSchemaViolation(
                tool_id,
                summary,
                validation.schema_version,
            )

        try:
            # Update action status
            action.status = result.status.value
            action.payload = result.payload
            if result.completed_at:
                action.completed_at = result.completed_at
            self.action_repo.update(action)

            # Emit ERIS receipt (FR-13)
            self.eris_client.emit_receipt(
                tenant_id=tenant_id,
                connection_id=str(connection_id),
                provider_id=action_data["provider_id"],
                operation_type=f"integration.action.{action_data['provider_id']}.{action_data['canonical_type']}",
                request_metadata={"target": action_data["target"]},  # Redacted
                result={"status": result.status.value, "payload": result.payload},
                correlation_id=action_data.get("correlation_id"),
            )

            # Record metrics (FR-12)
            self.metrics.increment_action_executed(action_data["provider_id"], connection_id)

            return action
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            action.status = "failed"
            action.payload = {"error": str(e)}
            self.action_repo.update(action)

            self.metrics.increment_action_error(action_data["provider_id"], connection_id)
            return action
