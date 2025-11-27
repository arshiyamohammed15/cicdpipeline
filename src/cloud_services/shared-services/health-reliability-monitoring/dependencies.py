"""
External dependency facades for the Health & Reliability Monitoring capability.

Includes lightweight clients/mocks for IAM (EPC-1), Configuration & Policy (EPC-3),
Alerting (EPC-4), Deployment (EPC-8), and ERIS (PM-7) so the module can run before
full integrations are wired.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class IAMClient:
    """Minimal IAM facade for token verification and scope enforcement."""

    def __init__(self) -> None:
        self._trusted_prefix = "valid_epc1_"

    async def verify(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify token signature and expiration (mocked)."""
        if token.startswith(self._trusted_prefix):
            return {
                "sub": "health-reliability-monitoring-system",
                "tenant_id": "tenant-default",
                "scope": [
                    "health_reliability_monitoring.read",
                    "health_reliability_monitoring.write",
                ],
                "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            }
        return None

    def authorize(self, claims: Dict[str, Any], scope: str) -> bool:
        """Check if token claims include the required scope."""
        return scope in claims.get("scope", [])


class PolicyClient:
    """Client for Configuration & Policy Management (EPC-3)."""

    def __init__(self, base_url: str, timeout_seconds: int = 5) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout_seconds)
        self._policy_cache: Dict[str, Dict[str, Any]] = {}
        self._slo_cache: Dict[str, Dict[str, Any]] = {}
        self._safe_policies: Dict[str, Dict[str, Any]] = {}

    async def fetch_health_policy(self, policy_id: str) -> Dict[str, Any]:
        """Retrieve health policy (mocked with cache fallback)."""
        if policy_id in self._policy_cache:
            return self._policy_cache[policy_id]
        # Mock policy payload
        payload = {
            "policy_id": policy_id,
            "thresholds": {"latency_p95_ms": 250, "error_rate": 0.02},
            "hysteresis": {"enter": 3, "exit": 2},
            "window_seconds": 300,
        }
        self._policy_cache[policy_id] = payload
        return payload

    async def fetch_slo(self, slo_id: str) -> Dict[str, Any]:
        """Retrieve SLO definitions for SLI/burn calculations."""
        if slo_id in self._slo_cache:
            return self._slo_cache[slo_id]
        payload = {
            "slo_id": slo_id,
            "target_percentage": 99.5,
            "window_days": 30,
            "error_budget_minutes": 216,
        }
        self._slo_cache[slo_id] = payload
        return payload

    async def fetch_safe_to_act_policy(self, action_type: str) -> Dict[str, Any]:
        """Return Safe-to-Act gating policy per action type."""
        if action_type in self._safe_policies:
            return self._safe_policies[action_type]
        payload = {
            "action_type": action_type,
            "deny_states": ["FAILED"],
            "degrade_states": ["DEGRADED"],
            "unknown_mode": "read_only",
            "plane_modes": {
                "failed": "read_only",
                "degraded": "degraded",
            },
            "component_overrides": {},
        }
        self._safe_policies[action_type] = payload
        return payload

    async def close(self) -> None:
        """Close HTTP client."""
        await self._client.aclose()


class AlertingClient:
    """Publisher for health transition events routed to EPC-4."""

    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.sent_events: List[Dict[str, Any]] = []

    async def publish(self, event: Dict[str, Any]) -> str:
        """Publish event to alerting bus (mock)."""
        event_id = uuid.uuid4().hex
        enriched = {"event_id": event_id, "topic": self.topic, **event}
        self.sent_events.append(enriched)
        logger.info("Published alerting event", extra={"event_id": event_id})
        return event_id


class DeploymentClient:
    """Client for EPC-8 gating notifications."""

    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.safe_to_act_events: List[Dict[str, Any]] = []

    async def notify(self, payload: Dict[str, Any]) -> None:
        """Send safe-to-act decision to deployment plane."""
        self.safe_to_act_events.append({"topic": self.topic, **payload})
        logger.info("Emitted safe-to-act decision", extra={"topic": self.topic})


class ERISClient:
    """Evidence & Receipt Indexing Service publisher."""

    def __init__(self, topic: str) -> None:
        self.topic = topic
        self.receipts: Dict[str, Dict[str, Any]] = {}

    async def emit_receipt(self, receipt: Dict[str, Any]) -> str:
        """Emit signed receipt into ERIS (mock)."""
        receipt_id = hashlib.sha256(
            json.dumps(receipt, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        payload = {"receipt_id": receipt_id, "topic": self.topic, **receipt}
        self.receipts[receipt_id] = payload
        logger.info("Stored ERIS receipt", extra={"receipt_id": receipt_id})
        return receipt_id


class EdgeAgentClient:
    """Placeholder Edge Agent integration for heartbeat contract enforcement."""

    async def upsert_profile(self, component: Dict[str, Any]) -> None:
        """Mocked call to push component expectations to agent fleets."""
        logger.debug("Updated edge agent profile", extra={"component": component.get("component_id")})

