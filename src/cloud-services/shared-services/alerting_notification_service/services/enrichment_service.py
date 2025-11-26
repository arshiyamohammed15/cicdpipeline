"""Alert enrichment services for Alerting & Notification Service."""
from __future__ import annotations

from typing import Dict, Optional

from ..clients import ComponentMetadataClient, PolicyClient
from ..database.models import Alert


class EnrichmentService:
    def __init__(
        self,
        tenant_metadata: Optional[Dict[str, Dict]] = None,
        component_client: Optional[ComponentMetadataClient] = None,
        policy_client: Optional[PolicyClient] = None,
    ):
        self.policy_client = policy_client or PolicyClient()
        self.component_client = component_client or ComponentMetadataClient()
        self.tenant_metadata = tenant_metadata or {}

    async def enrich(self, alert: Alert) -> Alert:
        await self._enrich_tenant(alert)
        await self._enrich_component(alert)
        self._enrich_policy(alert)
        return alert

    async def _enrich_tenant(self, alert: Alert) -> None:
        tenant_meta = self.tenant_metadata.get(alert.tenant_id, {})
        alert.labels.setdefault("tenant_tier", tenant_meta.get("tier", "standard"))
        contacts = tenant_meta.get("contacts", [])
        if contacts:
            alert.labels.setdefault("tenant_contacts", ",".join(contacts))

    async def _enrich_component(self, alert: Alert) -> None:
        metadata = await self.component_client.get_component(alert.component_id)
        dependencies = await self.component_client.get_dependencies(alert.component_id)
        alert.component_metadata = metadata or {}
        alert.component_metadata["dependencies"] = dependencies
        if metadata and metadata.get("slo_snapshot_url"):
            alert.slo_snapshot_url = metadata["slo_snapshot_url"]

    def _enrich_policy(self, alert: Alert) -> None:
        dedup_window = self.policy_client.get_dedup_window(alert.category, alert.severity)
        alert.labels.setdefault("dedup_window_minutes", str(dedup_window))
        if not alert.policy_refs:
            alert.policy_refs = ["default"]

