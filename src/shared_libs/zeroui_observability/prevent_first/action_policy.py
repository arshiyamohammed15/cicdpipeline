"""
OBS-14: Action Policy - Policy-driven action authorization via EPC-3.

Evaluates prevent-first actions against EPC-3 policy service for authorization.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    from ...cccs.adapters.epc3_adapter import EPC3PolicyAdapter, PolicyDecision, PolicyUnavailableError
    EPC3_AVAILABLE = True
except ImportError:
    EPC3_AVAILABLE = False
    PolicyDecision = None  # type: ignore
    PolicyUnavailableError = Exception  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class ActionPolicyConfig:
    """Action policy configuration."""

    action_id: str
    action_type: str  # "create_ticket", "request_human_validation", "reduce_autonomy_level", "gate_mode_change"
    enabled: bool
    confidence_gate: Dict[str, Any]  # {"enabled": bool, "min_confidence": float}
    permissions: Optional[Dict[str, Any]] = None
    escalation_path: Optional[Dict[str, Any]] = None
    action_parameters: Optional[Dict[str, Any]] = None


class ActionPolicy:
    """
    Policy-driven action authorization.

    Uses EPC-3 for policy evaluation to authorize prevent-first actions.
    """

    def __init__(
        self,
        epc3_adapter: Optional[Any] = None,  # EPC3PolicyAdapter
        module_id: str = "zeroui_observability_prevent_first",
    ):
        """
        Initialize action policy.

        Args:
            epc3_adapter: EPC-3 policy adapter (optional, creates default if not provided)
            module_id: Module ID for policy evaluation
        """
        self.module_id = module_id
        self.epc3_adapter = epc3_adapter

        if not self.epc3_adapter and EPC3_AVAILABLE:
            try:
                from ...cccs.adapters.epc3_adapter import EPC3PolicyAdapter
                self.epc3_adapter = EPC3PolicyAdapter()
            except Exception as e:
                logger.warning(f"Failed to initialize EPC-3 adapter: {e}")
                self.epc3_adapter = None

    async def evaluate_action_authorization(
        self,
        action_policy: ActionPolicyConfig,
        context: Dict[str, Any],
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate action authorization via EPC-3.

        Args:
            action_policy: Action policy configuration
            context: Evaluation context (forecast data, SLO info, etc.)
            tenant_id: Optional tenant ID
            environment: Optional environment

        Returns:
            Authorization result with decision, rationale, and policy info
        """
        # Check if action is enabled
        if not action_policy.enabled:
            return {
                "authorized": False,
                "reason": "Action is disabled",
                "policy_version_ids": [],
            }

        # Check permissions (tenant/environment filters)
        if action_policy.permissions:
            tenant_ids = action_policy.permissions.get("tenant_ids", [])
            if tenant_ids and tenant_id and tenant_id not in tenant_ids:
                return {
                    "authorized": False,
                    "reason": f"Tenant {tenant_id} not in allowed list",
                    "policy_version_ids": [],
                }

            environments = action_policy.permissions.get("environments", [])
            if environments and environment and environment not in environments:
                return {
                    "authorized": False,
                    "reason": f"Environment {environment} not in allowed list",
                    "policy_version_ids": [],
                }

        # If policy approval required, evaluate via EPC-3
        require_policy_approval = action_policy.permissions and action_policy.permissions.get(
            "require_policy_approval", False
        )

        if require_policy_approval and self.epc3_adapter:
            try:
                # Build policy evaluation inputs
                policy_inputs = {
                    "action_id": action_policy.action_id,
                    "action_type": action_policy.action_type,
                    "context": context,
                    "tenant_id": tenant_id,
                    "environment": environment,
                }

                # Evaluate policy
                decision = await self.epc3_adapter.evaluate_policy(
                    module_id=self.module_id,
                    inputs=policy_inputs,
                )

                return {
                    "authorized": decision.decision == "allow",
                    "reason": decision.rationale,
                    "policy_version_ids": decision.policy_version_ids,
                    "policy_snapshot_hash": decision.policy_snapshot_hash,
                }
            except PolicyUnavailableError as e:
                logger.error(f"Policy evaluation failed: {e}")
                # Fail-closed: deny if policy unavailable
                return {
                    "authorized": False,
                    "reason": f"Policy evaluation unavailable: {e}",
                    "policy_version_ids": [],
                }
        else:
            # No policy approval required, allow if enabled and permissions pass
            return {
                "authorized": True,
                "reason": "Action enabled and permissions passed",
                "policy_version_ids": [],
            }

    def check_confidence_gate(
        self,
        action_policy: ActionPolicyConfig,
        forecast_confidence: float,
    ) -> bool:
        """
        Check if confidence gate passes.

        Args:
            action_policy: Action policy configuration
            forecast_confidence: Forecast confidence (0.0 to 1.0)

        Returns:
            True if confidence gate passes, False otherwise
        """
        confidence_gate = action_policy.confidence_gate
        if not confidence_gate.get("enabled", False):
            return True  # Gate disabled, always pass

        min_confidence = confidence_gate.get("min_confidence", 0.0)
        return forecast_confidence >= min_confidence
