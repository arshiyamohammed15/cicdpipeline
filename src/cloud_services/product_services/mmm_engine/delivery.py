"""
Delivery orchestrator for MMM actions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List

from .models import MMMDecision, MMMAction, Surface
from .integrations.downstream_clients import (
    EdgeAgentClient,
    CIWorkflowClient,
    AlertingClient,
    DELIVERY_METRICS,
)

logger = logging.getLogger(__name__)


class DeliveryOrchestrator:
    """Routes MMM actions to the appropriate downstream clients."""

    def __init__(
        self,
        edge_client: EdgeAgentClient,
        ci_client: CIWorkflowClient,
        alerting_client: AlertingClient,
    ) -> None:
        self.edge_client = edge_client
        self.ci_client = ci_client
        self.alerting_client = alerting_client

    def deliver(self, decision: MMMDecision) -> Dict[str, List[bool]]:
        results: Dict[str, List[bool]] = {"ide": [], "ci": [], "alert": []}

        for action in decision.actions:
            payload = self._build_payload(decision, action)
            if Surface.IDE in action.surfaces:
                success = self.edge_client.send_action(payload)
                results["ide"].append(success)
            if Surface.CI in action.surfaces:
                success = self.ci_client.send_action(payload)
                results["ci"].append(success)
            if Surface.ALERT in action.surfaces:
                success = self.alerting_client.send_action(payload)
                results["alert"].append(success)

        logger.debug("Delivery results for decision %s: %s", decision.decision_id, results)
        logger.info(
            "MMM delivery summary | decision=%s attempts=%s success=%s failures=%s",
            decision.decision_id,
            DELIVERY_METRICS["total_attempts"],
            DELIVERY_METRICS["successful_deliveries"],
            DELIVERY_METRICS["failed_deliveries"],
        )
        return results

    @staticmethod
    def _build_payload(decision: MMMDecision, action: MMMAction) -> Dict[str, object]:
        return {
            "decision_id": decision.decision_id,
            "tenant_id": decision.tenant_id,
            "actor_id": decision.actor_id,
            "actor_type": decision.actor_type.value,
            "action_id": action.action_id,
            "action_type": action.type.value,
            "requires_consent": action.requires_consent,
            "requires_dual_channel": action.requires_dual_channel,
            "payload": action.payload,
            "context": decision.context.model_dump(),
            "timestamp_utc": datetime.utcnow().isoformat(),
        }

