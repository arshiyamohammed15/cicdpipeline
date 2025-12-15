"""
Repository pattern implementations for Integration Adapters Module.

What: CRUD operations for all database models with tenant isolation
Why: Encapsulate database access logic, enforce tenant isolation
Reads/Writes: Database tables via SQLAlchemy ORM
Contracts: Repository pattern with tenant-scoped queries
Risks: Tenant isolation violations, transaction handling errors
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import (
    IntegrationProvider,
    IntegrationConnection,
    WebhookRegistration,
    PollingCursor,
    AdapterEvent,
    NormalisedAction,
)


class ProviderRepository:
    """Repository for IntegrationProvider model."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, provider: IntegrationProvider) -> IntegrationProvider:
        """Create a new provider."""
        self.session.add(provider)
        self.session.commit()
        self.session.refresh(provider)
        return provider

    def get_by_id(self, provider_id: str) -> Optional[IntegrationProvider]:
        """Get provider by ID."""
        return self.session.query(IntegrationProvider).filter(
            IntegrationProvider.provider_id == provider_id
        ).first()

    def get_all(self) -> List[IntegrationProvider]:
        """Get all providers."""
        return self.session.query(IntegrationProvider).all()

    def get_by_category(self, category: str) -> List[IntegrationProvider]:
        """Get providers by category."""
        return self.session.query(IntegrationProvider).filter(
            IntegrationProvider.category == category
        ).all()

    def update(self, provider: IntegrationProvider) -> IntegrationProvider:
        """Update provider."""
        self.session.commit()
        self.session.refresh(provider)
        return provider

    def delete(self, provider_id: str) -> bool:
        """Delete provider."""
        provider = self.get_by_id(provider_id)
        if provider:
            self.session.delete(provider)
            self.session.commit()
            return True
        return False


class ConnectionRepository:
    """Repository for IntegrationConnection model with tenant isolation."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, connection: IntegrationConnection) -> IntegrationConnection:
        """Create a new connection."""
        self.session.add(connection)
        self.session.commit()
        self.session.refresh(connection)
        return connection

    def get_by_id(
        self, connection_id: UUID, tenant_id: Optional[str] = None
    ) -> Optional[IntegrationConnection]:
        """
        Get connection by ID with optional tenant isolation.
        
        Args:
            connection_id: Connection ID
            tenant_id: Tenant ID (if provided, enforces tenant scoping)
        """
        query = self.session.query(IntegrationConnection).filter(
            IntegrationConnection.connection_id == connection_id
        )
        if tenant_id is not None:
            query = query.filter(IntegrationConnection.tenant_id == tenant_id)
        return query.first()

    def get_all_by_tenant(self, tenant_id: str) -> List[IntegrationConnection]:
        """Get all connections for a tenant."""
        return self.session.query(IntegrationConnection).filter(
            IntegrationConnection.tenant_id == tenant_id
        ).all()

    def get_by_tenant_and_provider(
        self, tenant_id: str, provider_id: str
    ) -> List[IntegrationConnection]:
        """Get connections by tenant and provider."""
        return self.session.query(IntegrationConnection).filter(
            and_(
                IntegrationConnection.tenant_id == tenant_id,
                IntegrationConnection.provider_id == provider_id
            )
        ).all()

    def get_by_status(self, tenant_id: str, status: str) -> List[IntegrationConnection]:
        """Get connections by status for a tenant."""
        return self.session.query(IntegrationConnection).filter(
            and_(
                IntegrationConnection.tenant_id == tenant_id,
                IntegrationConnection.status == status
            )
        ).all()

    def get_all_active(self) -> List[IntegrationConnection]:
        """Get all active connections across all tenants."""
        return self.session.query(IntegrationConnection).filter(
            IntegrationConnection.status == "active"
        ).all()

    def update(self, connection: IntegrationConnection) -> IntegrationConnection:
        """Update connection."""
        self.session.commit()
        self.session.refresh(connection)
        return connection

    def delete(self, connection_id: UUID, tenant_id: str) -> bool:
        """Delete connection with tenant isolation."""
        connection = self.get_by_id(connection_id, tenant_id)
        if connection:
            self.session.delete(connection)
            self.session.commit()
            return True
        return False


class WebhookRegistrationRepository:
    """Repository for WebhookRegistration model."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, registration: WebhookRegistration) -> WebhookRegistration:
        """Create a new webhook registration."""
        self.session.add(registration)
        self.session.commit()
        self.session.refresh(registration)
        return registration

    def get_by_id(self, registration_id: UUID) -> Optional[WebhookRegistration]:
        """Get webhook registration by ID."""
        return self.session.query(WebhookRegistration).filter(
            WebhookRegistration.registration_id == registration_id
        ).first()

    def get_by_connection(self, connection_id: UUID) -> List[WebhookRegistration]:
        """Get webhook registrations by connection."""
        return self.session.query(WebhookRegistration).filter(
            WebhookRegistration.connection_id == connection_id
        ).all()

    def get_active_by_connection(
        self, connection_id: UUID, tenant_id: Optional[str] = None
    ) -> List[WebhookRegistration]:
        """Get active webhook registrations by connection (optionally tenant-scoped)."""
        query = (
            self.session.query(WebhookRegistration)
            .join(IntegrationConnection, WebhookRegistration.connection_id == IntegrationConnection.connection_id)
            .filter(
                and_(
                    WebhookRegistration.connection_id == connection_id,
                    WebhookRegistration.status == "active",
                )
            )
        )
        if tenant_id is not None:
            query = query.filter(IntegrationConnection.tenant_id == tenant_id)
        return query.all()

    def get_active_by_registration(
        self, registration_id: UUID, tenant_id: Optional[str] = None
    ) -> Optional[WebhookRegistration]:
        """Get a single active webhook registration by ID (optionally tenant-scoped)."""
        query = (
            self.session.query(WebhookRegistration)
            .join(IntegrationConnection, WebhookRegistration.connection_id == IntegrationConnection.connection_id)
            .filter(
                and_(
                    WebhookRegistration.registration_id == registration_id,
                    WebhookRegistration.status == "active",
                )
            )
        )
        if tenant_id is not None:
            query = query.filter(IntegrationConnection.tenant_id == tenant_id)
        return query.first()

    def update(self, registration: WebhookRegistration) -> WebhookRegistration:
        """Update webhook registration."""
        self.session.commit()
        self.session.refresh(registration)
        return registration

    def delete(self, registration_id: UUID) -> bool:
        """Delete webhook registration."""
        registration = self.get_by_id(registration_id)
        if registration:
            self.session.delete(registration)
            self.session.commit()
            return True
        return False


class PollingCursorRepository:
    """Repository for PollingCursor model."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, cursor: PollingCursor) -> PollingCursor:
        """Create a new polling cursor."""
        self.session.add(cursor)
        self.session.commit()
        self.session.refresh(cursor)
        return cursor

    def get_by_id(self, cursor_id: UUID) -> Optional[PollingCursor]:
        """Get polling cursor by ID."""
        return self.session.query(PollingCursor).filter(
            PollingCursor.cursor_id == cursor_id
        ).first()

    def get_by_connection(self, connection_id: UUID) -> Optional[PollingCursor]:
        """Get polling cursor by connection (one per connection)."""
        return self.session.query(PollingCursor).filter(
            PollingCursor.connection_id == connection_id
        ).first()

    def update(self, cursor: PollingCursor) -> PollingCursor:
        """Update polling cursor."""
        self.session.commit()
        self.session.refresh(cursor)
        return cursor

    def delete(self, cursor_id: UUID) -> bool:
        """Delete polling cursor."""
        cursor = self.get_by_id(cursor_id)
        if cursor:
            self.session.delete(cursor)
            self.session.commit()
            return True
        return False


class AdapterEventRepository:
    """Repository for AdapterEvent model."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, event: AdapterEvent) -> AdapterEvent:
        """Create a new adapter event."""
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_by_id(self, event_id: UUID) -> Optional[AdapterEvent]:
        """Get adapter event by ID."""
        return self.session.query(AdapterEvent).filter(
            AdapterEvent.event_id == event_id
        ).first()

    def get_by_connection(
        self, connection_id: UUID, limit: int = 100
    ) -> List[AdapterEvent]:
        """Get adapter events by connection."""
        return self.session.query(AdapterEvent).filter(
            AdapterEvent.connection_id == connection_id
        ).order_by(AdapterEvent.received_at.desc()).limit(limit).all()

    def get_recent_by_connection(
        self, connection_id: UUID, since: datetime
    ) -> List[AdapterEvent]:
        """Get recent adapter events by connection since timestamp."""
        return self.session.query(AdapterEvent).filter(
            and_(
                AdapterEvent.connection_id == connection_id,
                AdapterEvent.received_at >= since
            )
        ).order_by(AdapterEvent.received_at.desc()).all()

    def delete(self, event_id: UUID) -> bool:
        """Delete adapter event."""
        event = self.get_by_id(event_id)
        if event:
            self.session.delete(event)
            self.session.commit()
            return True
        return False


class NormalisedActionRepository:
    """Repository for NormalisedAction model with tenant isolation."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, action: NormalisedAction) -> NormalisedAction:
        """Create a new normalised action."""
        self.session.add(action)
        self.session.commit()
        self.session.refresh(action)
        return action

    def get_by_id(self, action_id: UUID, tenant_id: str) -> Optional[NormalisedAction]:
        """Get normalised action by ID with tenant isolation."""
        return self.session.query(NormalisedAction).filter(
            and_(
                NormalisedAction.action_id == action_id,
                NormalisedAction.tenant_id == tenant_id
            )
        ).first()

    def get_by_idempotency_key(
        self, idempotency_key: str, tenant_id: str
    ) -> Optional[NormalisedAction]:
        """Get normalised action by idempotency key with tenant isolation."""
        return self.session.query(NormalisedAction).filter(
            and_(
                NormalisedAction.idempotency_key == idempotency_key,
                NormalisedAction.tenant_id == tenant_id
            )
        ).first()

    def get_pending_by_tenant(self, tenant_id: str, limit: int = 100) -> List[NormalisedAction]:
        """Get pending actions for a tenant."""
        return self.session.query(NormalisedAction).filter(
            and_(
                NormalisedAction.tenant_id == tenant_id,
                NormalisedAction.status == "pending"
            )
        ).order_by(NormalisedAction.created_at.asc()).limit(limit).all()

    def get_by_connection(
        self, connection_id: UUID, tenant_id: str, status: Optional[str] = None
    ) -> List[NormalisedAction]:
        """Get actions by connection with optional status filter."""
        query = self.session.query(NormalisedAction).filter(
            and_(
                NormalisedAction.connection_id == connection_id,
                NormalisedAction.tenant_id == tenant_id
            )
        )
        if status:
            query = query.filter(NormalisedAction.status == status)
        return query.order_by(NormalisedAction.created_at.desc()).all()

    def update(self, action: NormalisedAction) -> NormalisedAction:
        """Update normalised action."""
        self.session.commit()
        self.session.refresh(action)
        return action

    def delete(self, action_id: UUID, tenant_id: str) -> bool:
        """Delete normalised action with tenant isolation."""
        action = self.get_by_id(action_id, tenant_id)
        if action:
            self.session.delete(action)
            self.session.commit()
            return True
        return False

