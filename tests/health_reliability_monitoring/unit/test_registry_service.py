import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from health_reliability_monitoring.database import models
from health_reliability_monitoring.services.registry_service import (
    ComponentRegistryService,
)
from health_reliability_monitoring.models import ComponentDefinition, DependencyReference
from health_reliability_monitoring.dependencies import EdgeAgentClient


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    models.Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False)
    with Session() as sess:
        yield sess


class StubPolicyClient:
    async def fetch_health_policy(self, policy_id: str):
        return {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_and_fetch_component(session, monkeypatch):
    service = ComponentRegistryService(session, StubPolicyClient(), EdgeAgentClient())
    component = ComponentDefinition(
        component_id="pm-4",
        name="Detection Engine",
        component_type="service",
        plane="Tenant",
        environment="prod",
        tenant_scope="tenant",
        dependencies=[DependencyReference(component_id="epc-8", critical=True)],
        metrics_profile=["GOLDEN_SIGNALS"],
        health_policies=["policy_detection"],
        slo_target=99.5,
    )

    response = service.register_component(component)
    assert response.component_id == "pm-4"

    stored = service.get_component("pm-4")
    assert stored is not None
    assert stored.component_id == "pm-4"
    assert stored.dependencies[0].component_id == "epc-8"

