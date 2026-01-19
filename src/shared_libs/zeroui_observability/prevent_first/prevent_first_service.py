"""
OBS-14: Prevent-First Service - Evaluates forecasts and triggers prevent-first actions.

Service that evaluates forecasts and triggers prevent-first actions with confidence gates.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..correlation.trace_context import TraceContext, get_or_create_trace_context

from .action_executor import ActionExecutor
from .action_policy import ActionPolicy, ActionPolicyConfig

logger = logging.getLogger(__name__)


class PreventFirstService:
    """
    Prevent-first service for proactive SLO management.

    Evaluates forecasts and triggers prevent-first actions when confidence gates pass.
    Integrates with forecast service, action executor, and policy evaluator.
    """

    def __init__(
        self,
        action_executor: Optional[ActionExecutor] = None,
        action_policy: Optional[ActionPolicy] = None,
        action_policies_path: Optional[Path] = None,
    ):
        """
        Initialize prevent-first service.

        Args:
            action_executor: Action executor instance
            action_policy: Action policy evaluator
            action_policies_path: Path to action policy configuration files
        """
        self.action_executor = action_executor or ActionExecutor()
        self.action_policy = action_policy or ActionPolicy()
        self.action_policies_path = action_policies_path
        self._action_policies: Dict[str, ActionPolicyConfig] = {}
        self._load_action_policies()

    def _load_action_policies(self) -> None:
        """Load action policies from configuration files."""
        if not self.action_policies_path:
            return

        try:
            if self.action_policies_path.is_file():
                # Single file
                with open(self.action_policies_path, "r") as f:
                    policies_data = json.load(f)
                    if isinstance(policies_data, list):
                        for policy_data in policies_data:
                            self._load_single_policy(policy_data)
                    else:
                        self._load_single_policy(policies_data)
            elif self.action_policies_path.is_dir():
                # Directory of policy files
                for policy_file in self.action_policies_path.glob("*.json"):
                    try:
                        with open(policy_file, "r") as f:
                            policy_data = json.load(f)
                            self._load_single_policy(policy_data)
                    except Exception as e:
                        logger.warning(f"Failed to load policy file {policy_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load action policies: {e}", exc_info=True)

    def _load_single_policy(self, policy_data: Dict[str, Any]) -> None:
        """Load a single action policy."""
        try:
            action_id = policy_data.get("action_id")
            if not action_id:
                logger.warning("Policy missing action_id, skipping")
                return

            policy = ActionPolicyConfig(
                action_id=action_id,
                action_type=policy_data.get("action_type", "create_ticket"),
                enabled=policy_data.get("enabled", False),  # Disabled by default
                confidence_gate=policy_data.get("confidence_gate", {"enabled": True, "min_confidence": 0.7}),
                permissions=policy_data.get("permissions"),
                escalation_path=policy_data.get("escalation_path"),
                action_parameters=policy_data.get("action_parameters"),
            )

            self._action_policies[action_id] = policy
            logger.info(f"Loaded action policy: {action_id} (enabled={policy.enabled})")
        except Exception as e:
            logger.error(f"Failed to load action policy: {e}", exc_info=True)

    def get_action_policy(self, action_id: str) -> Optional[ActionPolicyConfig]:
        """Get action policy by ID."""
        return self._action_policies.get(action_id)

    def list_action_policies(self) -> List[str]:
        """List all action policy IDs."""
        return list(self._action_policies.keys())

    async def evaluate_and_trigger(
        self,
        forecast_data: Dict[str, Any],
        action_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        trace_ctx: Optional[TraceContext] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate forecast and trigger prevent-first action if conditions are met.

        Args:
            forecast_data: Forecast data from ForecastService
            action_id: Optional specific action ID (if None, uses default for forecast)
            context: Additional context
            trace_ctx: Optional trace context
            tenant_id: Optional tenant ID
            environment: Optional environment

        Returns:
            Result with action execution status
        """
        # Get or create trace context
        if trace_ctx is None:
            trace_ctx = get_or_create_trace_context()

        # Determine action ID
        if not action_id:
            # Default action based on forecast
            slo_id = forecast_data.get("slo_id", "unknown")
            action_id = f"prevent_first_{slo_id}"

        # Get action policy
        action_policy = self.get_action_policy(action_id)
        if not action_policy:
            return {
                "action_id": action_id,
                "status": "not_found",
                "reason": f"Action policy {action_id} not found",
            }

        # Check if action is enabled
        if not action_policy.enabled:
            return {
                "action_id": action_id,
                "status": "disabled",
                "reason": "Action is disabled",
            }

        # Check confidence gate
        forecast_confidence = forecast_data.get("confidence", 0.0)
        confidence_passed = self.action_policy.check_confidence_gate(
            action_policy=action_policy,
            forecast_confidence=forecast_confidence,
        )

        if not confidence_passed:
            return {
                "action_id": action_id,
                "status": "blocked",
                "reason": f"Confidence gate failed: {forecast_confidence} < {action_policy.confidence_gate.get('min_confidence', 0.0)}",
            }

        # Execute action
        result = await self.action_executor.execute_action(
            action_policy=action_policy,
            action_type=action_policy.action_type,
            forecast_data=forecast_data,
            context=context or {},
            trace_ctx=trace_ctx,
            tenant_id=tenant_id,
            environment=environment,
        )

        return result

    async def evaluate_forecasts_and_trigger(
        self,
        forecasts: List[Dict[str, Any]],
        action_mappings: Optional[Dict[str, str]] = None,  # slo_id -> action_id
        context: Optional[Dict[str, Any]] = None,
        trace_ctx: Optional[TraceContext] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate multiple forecasts and trigger actions.

        Args:
            forecasts: List of forecast results from ForecastService
            action_mappings: Optional mapping of SLO ID to action ID
            context: Additional context
            trace_ctx: Optional trace context
            tenant_id: Optional tenant ID
            environment: Optional environment

        Returns:
            List of action execution results
        """
        results = []

        for forecast in forecasts:
            slo_id = forecast.get("slo_id", "unknown")
            action_id = None
            if action_mappings:
                action_id = action_mappings.get(slo_id)

            try:
                result = await self.evaluate_and_trigger(
                    forecast_data=forecast,
                    action_id=action_id,
                    context=context,
                    trace_ctx=trace_ctx,
                    tenant_id=tenant_id,
                    environment=environment,
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to evaluate forecast for SLO {slo_id}: {e}", exc_info=True)
                results.append({
                    "action_id": action_id or f"prevent_first_{slo_id}",
                    "status": "error",
                    "reason": str(e),
                })

        return results
