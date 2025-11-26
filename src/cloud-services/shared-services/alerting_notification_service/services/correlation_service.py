"""Correlation logic for alert incidents."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..clients import DependencyGraphClient, PolicyClient
from ..database.models import Alert, Incident


class CorrelationService:
    def __init__(self, session: AsyncSession, dependency_client: DependencyGraphClient | None = None):
        self.session = session
        self.policy_client = PolicyClient()
        self.dependency_client = dependency_client or DependencyGraphClient()

    async def correlate(self, alert: Alert) -> str:
        rules = self.policy_client.get_correlation_rules()
        window_minutes = self.policy_client.get_correlation_window()
        incident = await self._find_match(alert, rules, window_minutes)
        if incident:
            incident.alert_ids.append(alert.alert_id)
            incident.correlation_keys.append(alert.dedup_key)
            deps = alert.component_metadata.get("dependencies", [])
            for dep in deps:
                if dep not in incident.dependency_refs:
                    incident.dependency_refs.append(dep)
            await self.session.merge(incident)
            await self.session.commit()
            return incident.incident_id
        return f"inc-{alert.alert_id}"

    async def _find_match(self, alert: Alert, rules, window_minutes: int) -> Optional[Incident]:
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        statement = select(Incident).where(
            Incident.tenant_id == alert.tenant_id,
            Incident.opened_at >= window_start,
        )
        result = await self.session.exec(statement)
        incidents = result.scalars().all()
        for incident in incidents:
            if await self._matches_rules(alert, incident, rules):
                return incident
        return None

    async def _matches_rules(self, alert: Alert, incident: Incident, rules) -> bool:
        if not rules:
            return False
        for rule in rules:
            rule_window = rule.get("window_minutes")
            if rule_window is not None:
                cutoff = datetime.utcnow() - timedelta(minutes=rule_window)
                if incident.opened_at < cutoff:
                    continue
            if not self._conditions_match(rule.get("conditions", []), alert, incident):
                continue
            dep_match = rule.get("dependency_match")
            if dep_match == "shared":
                incident_component = incident.component_id or ""
                shared = await self.dependency_client.shared_dependencies(alert.component_id, incident_component)
                if not shared:
                    continue
            return True
        return False

    @staticmethod
    def _conditions_match(conditions, alert: Alert, incident: Incident) -> bool:
        for condition in conditions:
            if condition == "tenant_id" and incident.tenant_id != alert.tenant_id:
                return False
            if condition == "plane":
                if getattr(alert, "plane", None) != getattr(incident, "plane", None):
                    return False
            if condition == "severity" and incident.severity != alert.severity:
                return False
        return True

