import pytest

from health_reliability_monitoring.models import SafeToActRequest
from health_reliability_monitoring.services.safe_to_act_service import SafeToActService
from health_reliability_monitoring.services.telemetry_ingestion_service import TelemetryIngestionService
from health_reliability_monitoring.services.rollup_service import RollupService
from health_reliability_monitoring.dependencies import DeploymentClient
from datetime import datetime


class IdleTelemetry(TelemetryIngestionService):
    def last_ingest_age(self) -> float:
        return 999


class EmptyRollup(RollupService):
    def __init__(self):
        pass

    def tenant_view(self, tenant_id: str):
        from health_reliability_monitoring.models import TenantHealthView

        return TenantHealthView(
            tenant_id=tenant_id,
            plane_states={"Tenant": "UNKNOWN"},
            counts={"OK": 0, "DEGRADED": 0, "FAILED": 0, "UNKNOWN": 1},
            error_budget={},
            updated_at=datetime.utcnow(),
        )

    def latest_component_states(self):
        return {}


class StubPolicy:
    async def fetch_safe_to_act_policy(self, action_type: str):
        return {
            "deny_states": ["FAILED"],
            "degrade_states": ["DEGRADED"],
            "unknown_mode": "read_only",
            "component_overrides": {},
        }

@pytest.mark.asyncio
async def test_safe_to_act_unknown_state_triggers_safe_mode(monkeypatch):
    service = SafeToActService(
        rollup_service=EmptyRollup(),
        telemetry_service=IdleTelemetry(),
        deployment_client=DeploymentClient("topic"),
        policy_client=StubPolicy(),
    )

    response = await service.evaluate(
        SafeToActRequest(tenant_id="tenant-42", plane="Tenant", action_type="auto_remediate")
    )
    assert response.allowed is False
    assert "health_system_unavailable" in response.reason_codes

