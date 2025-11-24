from datetime import datetime

import pytest

from health_reliability_monitoring.models import SafeToActRequest
from health_reliability_monitoring.services.safe_to_act_service import SafeToActService
from health_reliability_monitoring.services.telemetry_ingestion_service import (
    TelemetryIngestionService,
)
from health_reliability_monitoring.services.rollup_service import RollupService
from health_reliability_monitoring.dependencies import DeploymentClient


class StubRollup(RollupService):
    def __init__(self, tenant_state: str):
        self._tenant_state = tenant_state

    def tenant_view(self, tenant_id: str):
        from health_reliability_monitoring.models import TenantHealthView

        return TenantHealthView(
            tenant_id=tenant_id,
            plane_states={"Tenant": self._tenant_state},
            counts={"OK": 0, "DEGRADED": 1, "FAILED": 0, "UNKNOWN": 0},
            error_budget={},
            updated_at=datetime.utcnow(),
        )

    def latest_component_states(self):
        return {}


class StubTelemetry(TelemetryIngestionService):
    def __init__(self, age: float):
        super().__init__()
        self._age = age

    def last_ingest_age(self) -> float:
        return self._age


class StubPolicy:
    async def fetch_safe_to_act_policy(self, action_type: str):
        return {
            "deny_states": ["FAILED"],
            "degrade_states": ["DEGRADED"],
            "unknown_mode": "read_only",
            "component_overrides": {},
        }


@pytest.mark.asyncio
async def test_safe_to_act_denies_on_failed_plane():
    service = SafeToActService(
        rollup_service=StubRollup("FAILED"),
        telemetry_service=StubTelemetry(age=1),
        deployment_client=DeploymentClient("topic"),
        policy_client=StubPolicy(),
    )

    response = await service.evaluate(
        SafeToActRequest(tenant_id="tenant-1", plane="Tenant", action_type="auto_remediate")
    )
    assert response.allowed is False
    assert response.recommended_mode == "read_only"


@pytest.mark.asyncio
async def test_safe_to_act_scope_unknown_component_triggers_default_mode():
    class ScopeRollup(StubRollup):
        def latest_component_states(self):
            return {}

    service = SafeToActService(
        rollup_service=ScopeRollup("OK"),
        telemetry_service=StubTelemetry(age=1),
        deployment_client=DeploymentClient("topic"),
        policy_client=StubPolicy(),
    )

    response = await service.evaluate(
        SafeToActRequest(
            tenant_id="tenant-1",
            plane="Tenant",
            action_type="auto_remediate",
            component_scope=["pm-4"],
        )
    )
    assert response.allowed is False
    assert "component_unknown:pm-4" in response.reason_codes

