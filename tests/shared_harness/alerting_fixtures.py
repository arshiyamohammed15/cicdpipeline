"""
Alerting-specific fixtures for test harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import uuid4

from .tenants import TenantProfile


@dataclass
class AlertEvent:
    """Synthetic alert event for testing."""

    alert_id: str
    tenant_id: str
    source_module: str
    severity: str  # P0/P1/P2/P3
    category: str
    summary: str
    dedup_key: str
    started_at: datetime
    labels: Dict[str, str] = field(default_factory=dict)


class AlertFixtureFactory:
    """Generates alert events for testing deduplication, routing, and fatigue controls."""

    def create_alert(
        self,
        tenant: TenantProfile,
        *,
        severity: str = "P1",
        source_module: str = "EPC-5",
        category: str = "reliability",
        dedup_key: str | None = None,
    ) -> AlertEvent:
        alert_id = f"alert-{uuid4().hex[:8]}"
        return AlertEvent(
            alert_id=alert_id,
            tenant_id=tenant.tenant_id,
            source_module=source_module,
            severity=severity,
            category=category,
            summary=f"Test alert from {source_module}",
            dedup_key=dedup_key or f"dedup-{category}-{tenant.tenant_id}",
            started_at=datetime.utcnow(),
            labels={"region": tenant.region, "tier": tenant.tier},
        )

    def create_alert_burst(
        self, tenant: TenantProfile, count: int, dedup_key: str
    ) -> List[AlertEvent]:
        """Create multiple alerts with the same dedup_key to test deduplication."""
        return [
            self.create_alert(tenant, dedup_key=dedup_key, severity="P1") for _ in range(count)
        ]

    def create_quiet_hours_alert(
        self, tenant: TenantProfile, hour: int
    ) -> AlertEvent:
        """Create an alert during quiet hours (e.g., hour=2 for 2 AM)."""
        alert = self.create_alert(tenant, severity="P2")
        alert.started_at = datetime.utcnow().replace(hour=hour, minute=0, second=0)
        return alert

