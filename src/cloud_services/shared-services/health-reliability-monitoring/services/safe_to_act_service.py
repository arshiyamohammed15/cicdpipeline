"""
Safe-to-Act evaluation service.

Determines whether an action should proceed based on latest health states, SLO
posture, telemetry freshness, and policy overrides.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from ..config import load_settings
from ..dependencies import DeploymentClient, PolicyClient
from ..models import SafeToActRequest, SafeToActResponse
from .rollup_service import RollupService
from .telemetry_ingestion_service import TelemetryIngestionService
from ..metrics import safe_to_act_decisions_total

settings = load_settings()


class SafeToActService:
    """Evaluates Safe-to-Act requests."""

    def __init__(
        self,
        rollup_service: RollupService,
        telemetry_service: TelemetryIngestionService,
        deployment_client: DeploymentClient,
        policy_client: PolicyClient,
    ) -> None:
        self._rollup = rollup_service
        self._telemetry = telemetry_service
        self._deployment = deployment_client
        self._policy_client = policy_client

    async def evaluate(self, request: SafeToActRequest) -> SafeToActResponse:
        """Process Safe-to-Act request per FR-7."""
        reason_codes: List[str] = []
        allowed = True
        recommended_mode = "normal"

        telemetry_age = self._telemetry.last_ingest_age()
        policy = await self._policy_client.fetch_safe_to_act_policy(request.action_type)
        deny_states = set(policy.get("deny_states", ["FAILED"]))
        degrade_states = set(policy.get("degrade_states", ["DEGRADED"]))
        unknown_mode = policy.get("unknown_mode", settings.safe_to_act.default_mode)
        component_overrides = policy.get("component_overrides", {})
        if telemetry_age > settings.safe_to_act.telemetry_stale_seconds:
            allowed = not settings.safe_to_act.deny_on_unknown
            recommended_mode = unknown_mode
            reason_codes.append("health_system_unavailable")
        else:
            tenant_view = self._rollup.tenant_view(request.tenant_id)
            priority = {"FAILED": 3, "DEGRADED": 2, "UNKNOWN": 1, "OK": 0}
            worst_plane = max(tenant_view.plane_states.values() or ["OK"], key=lambda s: priority[s])
            if worst_plane in deny_states or worst_plane in degrade_states:
                allowed = False
                recommended_mode = (
                    policy.get("plane_modes", {})
                    .get(worst_plane.lower(), "read_only" if worst_plane in deny_states else "degraded")
                )
                reason_codes.append(f"plane_{worst_plane.lower()}")

        component_states = self._rollup.latest_component_states()
        if allowed and request.component_scope:
            for component_id in request.component_scope:
                snapshot = component_states.get(component_id)
                if not snapshot or snapshot.state == "UNKNOWN":
                    allowed = False
                    recommended_mode = unknown_mode
                    reason_codes.append(f"component_unknown:{component_id}")
                    break

                overrides = component_overrides.get(component_id, {})
                deny_override = set(overrides.get("deny_states", [])) or deny_states
                degrade_override = set(overrides.get("degrade_states", [])) or degrade_states
                if snapshot.state in deny_override:
                    allowed = False
                    recommended_mode = overrides.get("deny_mode", "read_only")
                    reason_codes.append(f"{component_id}_state_{snapshot.state.lower()}")
                    break
                if snapshot.state in degrade_override:
                    allowed = False
                    recommended_mode = overrides.get("degrade_mode", "degraded")
                    reason_codes.append(f"{component_id}_state_{snapshot.state.lower()}")
                    break

        if allowed and request.component_scope:
            reason_codes.append("component_scope_healthy")

        response = SafeToActResponse(
            allowed=allowed,
            recommended_mode=recommended_mode,  # type: ignore[arg-type]
            reason_codes=reason_codes or ["healthy"],
            evaluated_at=datetime.utcnow(),
            snapshot_refs=None,
        )
        safe_to_act_decisions_total.labels(mode=recommended_mode, allowed=str(allowed)).inc()
        await self._deployment.notify(response.model_dump())
        return response

