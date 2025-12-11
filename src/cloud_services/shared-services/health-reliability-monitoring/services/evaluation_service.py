"""
Health evaluation engine for the Health & Reliability Monitoring capability.

Applies policy thresholds, hysteresis, and roll-up awareness to produce
HealthSnapshot records for downstream consumption.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
import time
import inspect
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..dependencies import PolicyClient
from ..models import HealthSnapshot, TelemetryPayload
from ..database import models as db_models
from .slo_service import SLOService
from .event_bus_service import EventBusService
from ..metrics import evaluation_latency_seconds

logger = logging.getLogger(__name__)


class HealthEvaluationService:
    """Evaluates telemetry batches into canonical health snapshots."""

    def __init__(
        self,
        session: Session,
        policy_client: PolicyClient,
        slo_service: SLOService | None = None,
        event_bus: EventBusService | None = None,
    ) -> None:
        self._session = session
        self._policy_client = policy_client
        self._state_cache: Dict[str, Tuple[str, datetime]] = {}
        self._slo_service = slo_service
        self._event_bus = event_bus

    async def evaluate_batch(self, telemetry_batch: List[TelemetryPayload]) -> List[HealthSnapshot]:
        """Evaluate multiple telemetry payloads in one pass."""
        start = time.perf_counter()
        snapshots: List[HealthSnapshot] = []
        for payload in telemetry_batch:
            component = self._session.get(db_models.Component, payload.component_id)
            if not component:
                logger.warning("Received telemetry for unknown component", extra={"component_id": payload.component_id})
                continue

            reason, state = await self._determine_state(payload, component.health_policies)
            snapshot = self._persist_snapshot(payload, state, reason)

            if self._slo_service and component.slo_target:
                await self._update_slo(component.component_id, component.slo_target, payload)

            if self._event_bus:
                maybe_coro = self._event_bus.emit_health_transition(
                    {
                        "component_id": payload.component_id,
                        "state": state,
                        "reason": reason,
                        "tenant_id": payload.tenant_id,
                    }
                )
                if inspect.isawaitable(maybe_coro):
                    await maybe_coro
            snapshots.append(snapshot)

        evaluation_latency_seconds.observe(time.perf_counter() - start)
        return snapshots

    async def _determine_state(
        self, payload: TelemetryPayload, health_policies: List[str]
    ) -> Tuple[str, str]:
        """Apply configured thresholds."""
        if not payload.metrics:
            return "no_metrics", "UNKNOWN"

        state = "OK"
        reason = "healthy"
        worst = 0
        for policy_id in health_policies:
            policy = await self._policy_client.fetch_health_policy(policy_id)
            thresholds = policy.get("thresholds", {})
            if not thresholds:
                continue
            metrics = payload.metrics
            local_state = "OK"
            local_reason = "within_policy"
            weight = 0

            sample_window = metrics.get("sample_window_sec")
            if sample_window is not None and sample_window < policy.get("window_seconds", 0):
                local_state = "UNKNOWN"
                local_reason = "insufficient_window"
                weight = max(weight, 1)

            heartbeat_limit = thresholds.get("heartbeat_lag_sec")
            if heartbeat_limit and metrics.get("heartbeat_lag_sec", 0) > heartbeat_limit:
                local_state = "UNKNOWN"
                local_reason = "heartbeat_stale"
                weight = max(weight, 1)

            if metrics.get("saturation_pct", 0) > thresholds.get("saturation_pct", 100):
                local_state = "DEGRADED"
                local_reason = f"saturation_above_{thresholds.get('saturation_pct')}"
                weight = max(weight, 2)

            if metrics.get("latency_p95_ms", 0) > thresholds.get("latency_p95_ms", 9999):
                local_state = "DEGRADED"
                local_reason = f"latency_above_{thresholds.get('latency_p95_ms')}"
                weight = max(weight, 2)

            if metrics.get("error_rate", 0) > thresholds.get("error_rate", 1):
                local_state = "FAILED"
                local_reason = f"error_rate_above_{thresholds.get('error_rate')}"
                weight = 3

            if weight > worst:
                worst = weight
                state = local_state
                reason = local_reason
                if weight == 3:
                    break

        if state == "OK" and worst == 0:
            reason = "within_policy"

        # Anti-flapping: require state to change if persisted for >= 2 windows
        cache_entry = self._state_cache.get(payload.component_id)
        if cache_entry:
            cached_state, since = cache_entry
            hold_minutes = policy.get("hysteresis", {}).get("exit", 2) if "policy" in locals() else 2
            if state != cached_state and datetime.utcnow() - since < timedelta(minutes=hold_minutes):
                state = cached_state
                reason = "hysteresis_hold"
            elif state != cached_state:
                self._state_cache[payload.component_id] = (state, datetime.utcnow())
        else:
            self._state_cache[payload.component_id] = (state, datetime.utcnow())

        return reason, state

    def _persist_snapshot(self, payload: TelemetryPayload, state: str, reason: str) -> HealthSnapshot:
        """Persist snapshot to DB and return API model."""
        snapshot_id = hashlib.sha1(
            f"{payload.component_id}{payload.timestamp.isoformat()}".encode("utf-8")
        ).hexdigest()
        entity = db_models.HealthSnapshot(
            snapshot_id=snapshot_id,
            component_id=payload.component_id,
            tenant_id=payload.tenant_id,
            plane=payload.plane,
            environment=payload.environment,
            state=state,
            reason_code=reason,
            metrics_summary=payload.metrics,
            slo_state=None,
        )
        self._session.merge(entity)
        self._session.flush()

        return HealthSnapshot(
            snapshot_id=snapshot_id,
            component_id=payload.component_id,
            tenant_id=payload.tenant_id,
            plane=payload.plane,
            environment=payload.environment,
            state=state,
            reason_code=reason,
            metrics_summary=payload.metrics,
            slo_state=None,
            policy_version=None,
            evaluated_at=datetime.utcnow(),
        )

    async def _update_slo(self, component_id: str, target: float, payload: TelemetryPayload) -> None:
        """Derive simple availability sample for SLO tracking."""
        window_minutes = 60
        error_rate = payload.metrics.get("error_rate", 0)
        success_ratio = max(0.0, 1.0 - error_rate)
        success_minutes = int(window_minutes * success_ratio)
        maybe_coro = self._slo_service.update_slo(
            component_id=component_id,
            slo_id=f"{component_id}-default-slo",
            success_minutes=success_minutes,
            total_minutes=window_minutes,
        )
        if inspect.isawaitable(maybe_coro):
            await maybe_coro
