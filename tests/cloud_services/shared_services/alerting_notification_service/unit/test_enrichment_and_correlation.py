
# Imports handled by conftest.py
from datetime import datetime, timedelta

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from alerting_notification_service.clients.component_client import DependencyGraphClient
from alerting_notification_service.database.models import Alert, Incident
from alerting_notification_service.services.correlation_service import CorrelationService
from alerting_notification_service.services.enrichment_service import EnrichmentService


class StubComponentClient:
    async def get_component(self, component_id):
        return {"component_id": component_id, "service_name": "svc", "slo_snapshot_url": "https://health/svc"}

    async def get_dependencies(self, component_id):
        return ["dep-1", "dep-2"]


class StubDependencyGraph:
    def __init__(self, shared_map=None):
        self.shared_map = shared_map or {}

    async def shared_dependencies(self, component_a, component_b):
        key = tuple(sorted((component_a or "", component_b or "")))
        return self.shared_map.get(key, [])


@pytest.mark.asyncio
async def test_enrichment_populates_metadata():
    alert = Alert(
        alert_id="enrich-1",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-1",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="test",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="comp-1:P2",
    )
    service = EnrichmentService(component_client=StubComponentClient())
    enriched = await service.enrich(alert)
    assert enriched.component_metadata["service_name"] == "svc"
    assert enriched.component_metadata["dependencies"] == ["dep-1", "dep-2"]
    assert enriched.slo_snapshot_url.endswith("svc")
    assert enriched.policy_refs == ["default"]
    assert "dedup_window_minutes" in enriched.labels


@pytest.mark.asyncio
async def test_enrichment_applies_tenant_contacts():
    tenant_meta = {"tenantA": {"tier": "gold", "contacts": ["ops@example.com"]}}
    alert = Alert(
        alert_id="enrich-tenant",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-1",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="test",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="comp-1:P2",
    )
    service = EnrichmentService(tenant_metadata=tenant_meta, component_client=StubComponentClient())
    enriched = await service.enrich(alert)
    assert enriched.labels["tenant_tier"] == "gold"
    assert "ops@example.com" in enriched.labels["tenant_contacts"]


@pytest.mark.asyncio
async def test_correlation_reuses_recent_incident(session: AsyncSession, monkeypatch):
    incident = Incident(
        incident_id="inc-existing",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-existing",
        title="Existing",
        severity="P2",
        opened_at=datetime.utcnow() - timedelta(minutes=1),
        alert_ids=[],
        correlation_keys=[],
    )
    session.add(incident)
    await session.commit()
    dep_client = StubDependencyGraph({tuple(sorted(("comp-2", "comp-existing"))): ["dep-a"]})
    service = CorrelationService(session, dependency_client=dep_client)
    monkeypatch.setattr(
        service.policy_client,
        "get_correlation_rules",
        lambda: [{"conditions": ["tenant_id", "plane"], "dependency_match": "shared"}],
    )

    alert = Alert(
        alert_id="corr-1",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-2",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="correlation test",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="comp-2:P2",
    )
    alert.component_metadata = {"dependencies": ["dep-a"]}
    incident_id = await service.correlate(alert)
    assert incident_id == "inc-existing"
    updated = await session.get(Incident, "inc-existing")
    assert "corr-1" in updated.alert_ids
    assert "dep-a" in updated.dependency_refs


@pytest.mark.asyncio
async def test_correlation_returns_new_when_no_match(session: AsyncSession, monkeypatch):
    incident = Incident(
        incident_id="inc-other",
        tenant_id="tenantB",
        title="Other",
        severity="P2",
        opened_at=datetime.utcnow() - timedelta(minutes=2),
        alert_ids=[],
        correlation_keys=[],
    )
    session.add(incident)
    await session.commit()
    service = CorrelationService(session, dependency_client=StubDependencyGraph())
    monkeypatch.setattr(service.policy_client, "get_correlation_rules", lambda: [{"conditions": ["tenant_id"]}])

    alert = Alert(
        alert_id="corr-new",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-3",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="new incident",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="comp-3:P2",
    )
    incident_id = await service.correlate(alert)
    assert incident_id.startswith("inc-")


@pytest.mark.asyncio
async def test_correlation_returns_new_when_rules_empty(session: AsyncSession, monkeypatch):
    incident = Incident(
        incident_id="inc-tenant",
        tenant_id="tenantA",
        title="Tenant Incident",
        severity="P2",
        opened_at=datetime.utcnow() - timedelta(minutes=2),
        alert_ids=[],
        correlation_keys=[],
    )
    session.add(incident)
    await session.commit()
    service = CorrelationService(session, dependency_client=StubDependencyGraph())
    monkeypatch.setattr(service.policy_client, "get_correlation_rules", lambda: [])

    alert = Alert(
        alert_id="corr-empty",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-4",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="no rules",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="comp-4:P2",
    )
    incident_id = await service.correlate(alert)
    assert incident_id.startswith("inc-")


@pytest.mark.asyncio
async def test_correlation_dependency_mismatch_creates_new(session: AsyncSession, monkeypatch):
    incident = Incident(
        incident_id="inc-diff",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-existing",
        title="Existing",
        severity="P2",
        opened_at=datetime.utcnow() - timedelta(minutes=1),
    )
    session.add(incident)
    await session.commit()
    dep_client = StubDependencyGraph({})
    service = CorrelationService(session, dependency_client=dep_client)
    monkeypatch.setattr(
        service.policy_client,
        "get_correlation_rules",
        lambda: [{"conditions": ["tenant_id", "plane"], "dependency_match": "shared"}],
    )

    alert = Alert(
        alert_id="corr-miss",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-new",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="new incident",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="comp-new:P2",
    )
    incident_id = await service.correlate(alert)
    assert incident_id != "inc-diff"


@pytest.mark.asyncio
async def test_correlation_rule_window_prevents_match(session: AsyncSession, monkeypatch):
    incident = Incident(
        incident_id="inc-old",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-old",
        title="Old Incident",
        severity="P2",
        opened_at=datetime.utcnow() - timedelta(minutes=30),
    )
    session.add(incident)
    await session.commit()
    service = CorrelationService(session, dependency_client=StubDependencyGraph())
    monkeypatch.setattr(
        service.policy_client,
        "get_correlation_rules",
        lambda: [{"conditions": ["tenant_id"], "window_minutes": 5}],
    )

    alert = Alert(
        alert_id="corr-window",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-new",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="window test",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="comp-new:P2",
    )
    incident_id = await service.correlate(alert)
    assert incident_id != "inc-old"


@pytest.mark.asyncio
async def test_dependency_graph_client_default():
    client = DependencyGraphClient()
    result = await client.shared_dependencies("a", "b")
    assert result == []


@pytest.mark.asyncio
async def test_matches_rules_dependency_flow(session: AsyncSession):
    dep_client = StubDependencyGraph({tuple(sorted(("comp-inline", "comp-inc"))): ["dep"]})
    service = CorrelationService(session, dependency_client=dep_client)
    incident = Incident(
        incident_id="inc-inline",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-inc",
        title="inline",
        severity="P2",
        opened_at=datetime.utcnow(),
    )
    alert = Alert(
        alert_id="inline",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-inline",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="inline",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="inline",
    )
    alert.component_metadata = {"dependencies": ["dep"]}
    rules = [{"conditions": ["tenant_id", "plane"], "dependency_match": "shared", "window_minutes": 10}]
    assert await service._matches_rules(alert, incident, rules)


@pytest.mark.asyncio
async def test_matches_rules_plane_mismatch(session: AsyncSession):
    dep_client = StubDependencyGraph({tuple(sorted(("comp-inline", "comp-inc"))): ["dep"]})
    service = CorrelationService(session, dependency_client=dep_client)
    incident = Incident(
        incident_id="inc-inline",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-inc",
        title="inline",
        severity="P2",
        opened_at=datetime.utcnow(),
    )
    alert = Alert(
        alert_id="inline",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Platform",
        environment="prod",
        component_id="comp-inline",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="inline",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="inline",
    )
    rules = [{"conditions": ["tenant_id", "plane"], "dependency_match": "shared"}]
    assert not await service._matches_rules(alert, incident, rules)


@pytest.mark.asyncio
async def test_correlate_appends_dependency_refs(session: AsyncSession, monkeypatch):
    incident = Incident(
        incident_id="inc-deps",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-root",
        title="Deps",
        severity="P2",
        opened_at=datetime.utcnow(),
        dependency_refs=[],
    )
    session.add(incident)
    await session.commit()
    service = CorrelationService(session, dependency_client=StubDependencyGraph({}))
    monkeypatch.setattr(
        service.policy_client,
        "get_correlation_rules",
        lambda: [{"conditions": ["tenant_id"], "window_minutes": 10}],
    )

    alert = Alert(
        alert_id="corr-deps",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-leaf",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="deps",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="leaf",
    )
    alert.component_metadata = {"dependencies": ["dep-x"]}
    incident_id = await service.correlate(alert)
    assert incident_id == "inc-deps"
    updated = await session.get(Incident, "inc-deps")
    assert "dep-x" in updated.dependency_refs


def test_conditions_severity_mismatch():
    incident = Incident(
        incident_id="inc-sev",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-x",
        title="sev",
        severity="P1",
        opened_at=datetime.utcnow(),
    )
    alert = Alert(
        alert_id="alert-sev",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-y",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="sev",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="sev",
    )
    assert not CorrelationService._conditions_match(["severity"], alert, incident)


def test_conditions_tenant_mismatch():
    incident = Incident(
        incident_id="inc-tenant",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-x",
        title="tenant",
        severity="P2",
        opened_at=datetime.utcnow(),
    )
    alert = Alert(
        alert_id="alert-tenant",
        tenant_id="tenantB",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-y",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="tenant",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="tenant",
    )
    assert not CorrelationService._conditions_match(["tenant_id"], alert, incident)


@pytest.mark.asyncio
async def test_matches_rules_window_skip(session: AsyncSession):
    service = CorrelationService(session, dependency_client=StubDependencyGraph({}))
    incident = Incident(
        incident_id="inc-window",
        tenant_id="tenantA",
        plane="Tenant",
        component_id="comp-x",
        title="window",
        severity="P2",
        opened_at=datetime.utcnow() - timedelta(minutes=30),
    )
    alert = Alert(
        alert_id="alert-window",
        tenant_id="tenantA",
        source_module="EPC-5",
        plane="Tenant",
        environment="prod",
        component_id="comp-y",
        severity="P2",
        priority="P2",
        category="reliability",
        summary="window",
        labels={},
        started_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        dedup_key="window",
    )
    rules = [{"conditions": ["tenant_id"], "window_minutes": 5}]
    assert not await service._matches_rules(alert, incident, rules)

