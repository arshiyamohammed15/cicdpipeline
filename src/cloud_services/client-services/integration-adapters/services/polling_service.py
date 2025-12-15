"""
Polling service for periodic event polling.

What: Orchestrates periodic polling for providers that don't support webhooks
Why: Enable event ingestion for polling-based providers (e.g., Jira)
Reads/Writes: Database (PollingCursor), external provider APIs
Contracts: PRD FR-5 (Polling & Backfill)
Risks: Rate limit exhaustion, budget overruns, polling failures
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

try:
    from ..database.models import IntegrationConnection, PollingCursor
    from ..database.repositories import (
        ConnectionRepository,
        PollingCursorRepository,
    )
    from ..integrations.budget_client import BudgetClient
    from ..integrations.pm3_client import PM3Client
    from ..services.adapter_registry import get_adapter_registry
    from ..services.signal_mapper import SignalMapper
    from ..observability.metrics import get_metrics_registry
    from ..observability.audit import get_audit_logger
except ImportError:
    import sys
    import os
    parent_dir = os.path.join(os.path.dirname(__file__), "../..")
    parent_dir = os.path.abspath(parent_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    try:
        from integration_adapters.database.models import IntegrationConnection, PollingCursor
        from integration_adapters.database.repositories import (
            ConnectionRepository,
            PollingCursorRepository,
        )
        from integration_adapters.integrations.budget_client import BudgetClient
        from integration_adapters.integrations.pm3_client import PM3Client
        from integration_adapters.services.adapter_registry import get_adapter_registry
        from integration_adapters.services.signal_mapper import SignalMapper
        from integration_adapters.observability.metrics import get_metrics_registry
        from integration_adapters.observability.audit import get_audit_logger
    except ImportError:
        from database.models import IntegrationConnection, PollingCursor
        from database.repositories import (
            ConnectionRepository,
            PollingCursorRepository,
        )
        from integrations.budget_client import BudgetClient
        from integrations.pm3_client import PM3Client
        from services.adapter_registry import get_adapter_registry
        from services.signal_mapper import SignalMapper
        from observability.metrics import get_metrics_registry
        from observability.audit import get_audit_logger

logger = logging.getLogger(__name__)


class PollingService:
    """
    Service for orchestrating periodic polling operations.
    
    Implements FR-5: Polling & Backfill
    - Polling with configured intervals
    - Pagination handling
    - Cursor management
    - Integration with M35 for rate/budget limits
    - Idempotency enforcement
    """

    def __init__(
        self,
        session: Session,
        budget_client: Optional[BudgetClient] = None,
        pm3_client: Optional[PM3Client] = None,
    ):
        """
        Initialize polling service.
        
        Args:
            session: Database session
            budget_client: Budget client (optional, creates default if None)
            pm3_client: PM-3 client (optional, creates default if None)
        """
        self.session = session
        self.connection_repo = ConnectionRepository(session)
        self.polling_repo = PollingCursorRepository(session)
        self.budget_client = budget_client or BudgetClient()
        self.pm3_client = pm3_client or PM3Client()
        self.adapter_registry = get_adapter_registry()
        self.signal_mapper = SignalMapper()
        self.metrics = get_metrics_registry()
        self.audit = get_audit_logger()

    def poll_connection(
        self,
        connection_id: UUID,
        tenant_id: str,
        poll_interval_minutes: int = 5,
    ) -> bool:
        """
        Poll a specific connection for new events.
        
        Args:
            connection_id: Connection ID to poll
            tenant_id: Tenant ID
            poll_interval_minutes: Minimum interval between polls (default: 5 minutes)
            
        Returns:
            True if polling succeeded, False otherwise
        """
        # Get connection
        connection = self.connection_repo.get_by_id(connection_id, tenant_id)
        if not connection or connection.status != "active":
            logger.warning(f"Connection not found or inactive: {connection_id}")
            return False

        # Check if polling is due
        cursor = self.polling_repo.get_by_connection(connection_id)
        if cursor:
            time_since_last_poll = datetime.utcnow() - cursor.last_polled_at
            if time_since_last_poll < timedelta(minutes=poll_interval_minutes):
                logger.debug(f"Polling not due yet for connection: {connection_id}")
                return True  # Not an error, just not time yet

        # Check budget before polling (FR-9)
        allowed, _ = self.budget_client.check_budget(
            tenant_id, connection.provider_id, str(connection_id)
        )
        if not allowed:
            logger.warning(f"Budget check failed for polling: {connection_id}")
            return False

        # Get adapter
        adapter = self.adapter_registry.get_adapter(
            connection.provider_id, connection_id, tenant_id
        )
        if not adapter:
            logger.error(f"Adapter not found for provider: {connection.provider_id}")
            return False

        # Get cursor position
        cursor_position = cursor.cursor_position if cursor else None

        # Poll for events
        try:
            events, new_cursor = adapter.poll_events(cursor_position)
            
            if not events:
                # Update cursor even if no events (to track last poll time)
                if cursor:
                    cursor.last_polled_at = datetime.utcnow()
                    self.polling_repo.update(cursor)
                else:
                    cursor = self.polling_repo.create(
                        PollingCursor(
                            connection_id=connection_id,
                            cursor_position=None,
                            last_polled_at=datetime.utcnow(),
                        )
                    )
                return True

            # Process each event
            for event in events:
                # Map to SignalEnvelope (FR-6)
                signal_envelope = self.signal_mapper.map_provider_event_to_signal_envelope(
                    provider_id=connection.provider_id,
                    connection_id=str(connection_id),
                    tenant_id=tenant_id,
                    provider_event=event.get("payload", event),
                    provider_event_type=event.get("event_type", "unknown"),
                    occurred_at=event.get("occurred_at", datetime.utcnow()),
                    correlation_id=event.get("id"),
                )

                # Forward to PM-3 (FR-6)
                self.pm3_client.ingest_signal(signal_envelope)

                # Update cursor position
                new_cursor_position = new_cursor or event.get("cursor_position") or event.get("id")
                if cursor:
                    cursor.cursor_position = new_cursor_position
                    cursor.last_polled_at = datetime.utcnow()
                    self.polling_repo.update(cursor)
                else:
                    cursor = self.polling_repo.create(
                        PollingCursor(
                            connection_id=connection_id,
                            cursor_position=new_cursor_position,
                            last_polled_at=datetime.utcnow(),
                        )
                    )

            # Record metrics (FR-12)
            self.metrics.increment_event_normalized(
                connection.provider_id, connection_id
            )

            return True

        except Exception as e:
            logger.error(f"Polling failed for connection {connection_id}: {e}")
            self.audit.log_error(
                tenant_id=tenant_id,
                operation="polling.poll_connection",
                error=str(e),
                metadata={"connection_id": str(connection_id)},
            )
            return False

    def poll_all_due_connections(
        self,
        poll_interval_minutes: int = 5,
        max_connections: int = 100,
    ) -> int:
        """
        Poll all connections that are due for polling.
        
        Args:
            poll_interval_minutes: Minimum interval between polls
            max_connections: Maximum number of connections to poll in one run
            
        Returns:
            Number of connections polled successfully
        """
        # Get all active connections
        all_connections = self.connection_repo.get_all_active()
        
        # Filter to connections that are due for polling
        due_connections = []
        for connection in all_connections[:max_connections]:
            cursor = self.polling_repo.get_by_connection(connection.connection_id)
            if not cursor:
                # No cursor means never polled - include it
                due_connections.append(connection)
            else:
                time_since_last_poll = datetime.utcnow() - cursor.last_polled_at
                if time_since_last_poll >= timedelta(minutes=poll_interval_minutes):
                    due_connections.append(connection)

        # Poll each connection
        success_count = 0
        for connection in due_connections:
            if self.poll_connection(
                connection.connection_id,
                connection.tenant_id,
                poll_interval_minutes,
            ):
                success_count += 1

        return success_count

    def get_polling_status(
        self, connection_id: UUID, tenant_id: str
    ) -> Optional[dict]:
        """
        Get polling status for a connection.
        
        Args:
            connection_id: Connection ID
            tenant_id: Tenant ID
            
        Returns:
            Polling status dict or None if connection not found
        """
        connection = self.connection_repo.get_by_id(connection_id, tenant_id)
        if not connection:
            return None

        cursor = self.polling_repo.get_by_connection(connection_id)
        
        return {
            "connection_id": str(connection_id),
            "provider_id": connection.provider_id,
            "has_cursor": cursor is not None,
            "cursor_position": cursor.cursor_position if cursor else None,
            "last_polled_at": cursor.last_polled_at.isoformat() if cursor and cursor.last_polled_at else None,
        }

