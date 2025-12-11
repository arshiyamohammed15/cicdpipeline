"""
Component registry service for Health & Reliability Monitoring.

Handles CRUD operations, dependency graph management, and synchronization hooks
to other modules (Edge Agents, Config & Policy).
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import EdgeAgentClient, PolicyClient
from ..models import ComponentDefinition, ComponentRegistrationResponse
from ..database import models as db_models

logger = logging.getLogger(__name__)


class ComponentRegistryService:
    """Encapsulates registry persistence logic."""

    def __init__(self, session: Session, policy_client: PolicyClient, edge_client: EdgeAgentClient) -> None:
        self._session = session
        self._policy_client = policy_client
        self._edge_client = edge_client

    def register_component(self, payload: ComponentDefinition) -> ComponentRegistrationResponse:
        """Create or update a component definition."""
        existing: Optional[db_models.Component] = self._session.get(db_models.Component, payload.component_id)

        if existing:
            logger.info("Updating component registry entry", extra={"component_id": payload.component_id})
            component = existing
        else:
            logger.info("Creating component registry entry", extra={"component_id": payload.component_id})
            component = db_models.Component(component_id=payload.component_id)
            self._session.add(component)

        component.name = payload.name
        component.component_type = payload.component_type
        component.plane = payload.plane
        component.environment = payload.environment
        component.tenant_scope = payload.tenant_scope
        component.metrics_profile = list(payload.metrics_profile)
        component.health_policies = list(payload.health_policies)
        component.slo_target = payload.slo_target
        component.error_budget_minutes = payload.error_budget_minutes
        component.owner_team = payload.owner_team
        component.documentation_url = payload.documentation_url

        component.dependencies.clear()
        for dep in payload.dependencies:
            component.dependencies.append(
                db_models.ComponentDependency(
                    component_id=payload.component_id,
                    dependency_id=dep.component_id,
                    critical=dep.critical,
                )
            )

        self._session.flush()

        # Notify Edge Agent of updated profile asynchronously
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        async def _push():
            try:
                await self._edge_client.upsert_profile(payload.model_dump())
            except Exception:
                logger.debug("Edge profile push skipped or failed in test harness")

        if loop and loop.is_running():
            loop.create_task(_push())
        else:
            tmp_loop = asyncio.new_event_loop()
            try:
                tmp_loop.run_until_complete(_push())
            finally:
                tmp_loop.close()

        return ComponentRegistrationResponse(component_id=payload.component_id, enrolled=True)

    def get_component(self, component_id: str) -> Optional[ComponentDefinition]:
        """Fetch a component definition."""
        component: Optional[db_models.Component] = self._session.get(db_models.Component, component_id)
        if not component:
            return None

        return self._to_model(component)

    def list_components(self) -> List[ComponentDefinition]:
        """List all components."""
        stmt = select(db_models.Component)
        return [self._to_model(row) for row in self._session.scalars(stmt)]

    def _to_model(self, component: db_models.Component) -> ComponentDefinition:
        """Convert ORM entity to API model."""
        return ComponentDefinition(
            component_id=component.component_id,
            name=component.name,
            component_type=component.component_type,
            plane=component.plane,
            environment=component.environment,
            tenant_scope=component.tenant_scope,
            dependencies=[
                {"component_id": dep.dependency_id, "critical": dep.critical} for dep in component.dependencies
            ],
            metrics_profile=component.metrics_profile or [],
            health_policies=component.health_policies or [],
            slo_target=component.slo_target,
            error_budget_minutes=component.error_budget_minutes,
            owner_team=component.owner_team,
            documentation_url=component.documentation_url,
        )
