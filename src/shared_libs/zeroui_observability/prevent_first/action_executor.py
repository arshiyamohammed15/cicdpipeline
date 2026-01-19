"""
OBS-14: Action Executor - Executes prevent-first actions with confidence gates.

Integrates with EPC-3 (policy), EPC-4 (alerting), and PM-7 (receipts) to execute actions.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from ..correlation.trace_context import TraceContext

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executor for prevent-first actions.

    Executes actions only when confidence gate passes and policy authorizes.
    Integrates with EPC-3, EPC-4, and PM-7 for authorization, routing, and audit.
    """

    def __init__(
        self,
        epc4_client: Optional[Any] = None,  # EPC-4 client for ticket creation
        receipt_service: Optional[Any] = None,  # PM-7 receipt service
        action_policy: Optional[Any] = None,  # ActionPolicy instance
    ):
        """
        Initialize action executor.

        Args:
            epc4_client: EPC-4 alerting service client
            receipt_service: PM-7 receipt service
            action_policy: Action policy evaluator
        """
        self.epc4_client = epc4_client
        self.receipt_service = receipt_service
        self.action_policy = action_policy

    async def execute_action(
        self,
        action_policy: Any,  # ActionPolicyConfig
        action_type: str,
        forecast_data: Dict[str, Any],
        context: Dict[str, Any],
        trace_ctx: Optional[TraceContext] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute prevent-first action.

        Args:
            action_policy: Action policy configuration
            action_type: Action type
            forecast_data: Forecast data (confidence, time_to_breach, etc.)
            context: Additional context
            trace_ctx: Optional trace context
            tenant_id: Optional tenant ID
            environment: Optional environment

        Returns:
            Execution result with receipt_id, action_id, and status
        """
        action_id = f"action_{uuid.uuid4().hex[:16]}"
        receipt_id = None

        try:
            # Check confidence gate
            forecast_confidence = forecast_data.get("confidence", 0.0)
            if self.action_policy:
                confidence_passed = self.action_policy.check_confidence_gate(
                    action_policy=action_policy,
                    forecast_confidence=forecast_confidence,
                )
                if not confidence_passed:
                    return {
                        "action_id": action_id,
                        "status": "blocked",
                        "reason": f"Confidence gate failed: {forecast_confidence} < {action_policy.confidence_gate.get('min_confidence', 0.0)}",
                        "receipt_id": None,
                    }

            # Evaluate policy authorization
            authorization = None
            if self.action_policy:
                authorization = await self.action_policy.evaluate_action_authorization(
                    action_policy=action_policy,
                    context={**forecast_data, **context},
                    tenant_id=tenant_id,
                    environment=environment,
                )

                if not authorization.get("authorized", False):
                    return {
                        "action_id": action_id,
                        "status": "denied",
                        "reason": authorization.get("reason", "Policy denied"),
                        "receipt_id": None,
                        "policy_version_ids": authorization.get("policy_version_ids", []),
                    }

            # Execute action based on type
            action_result = await self._execute_action_by_type(
                action_type=action_type,
                action_policy=action_policy,
                forecast_data=forecast_data,
                context=context,
                trace_ctx=trace_ctx,
                tenant_id=tenant_id,
            )

            # Generate receipt via PM-7
            if self.receipt_service and trace_ctx:
                receipt_id = await self._generate_receipt(
                    action_id=action_id,
                    action_type=action_type,
                    forecast_data=forecast_data,
                    authorization=authorization,
                    action_result=action_result,
                    trace_ctx=trace_ctx,
                    tenant_id=tenant_id,
                )

            return {
                "action_id": action_id,
                "status": "executed",
                "reason": "Action executed successfully",
                "receipt_id": receipt_id,
                "action_result": action_result,
                "policy_version_ids": authorization.get("policy_version_ids", []) if authorization else [],
            }

        except Exception as e:
            logger.error(f"Failed to execute action {action_id}: {e}", exc_info=True)
            return {
                "action_id": action_id,
                "status": "failed",
                "reason": f"Execution failed: {e}",
                "receipt_id": receipt_id,
            }

    async def _execute_action_by_type(
        self,
        action_type: str,
        action_policy: Any,
        forecast_data: Dict[str, Any],
        context: Dict[str, Any],
        trace_ctx: Optional[TraceContext],
        tenant_id: Optional[str],
    ) -> Dict[str, Any]:
        """Execute action based on type."""
        if action_type == "create_ticket":
            return await self._create_ticket(
                action_policy=action_policy,
                forecast_data=forecast_data,
                context=context,
                trace_ctx=trace_ctx,
                tenant_id=tenant_id,
            )
        elif action_type == "request_human_validation":
            return await self._request_human_validation(
                action_policy=action_policy,
                forecast_data=forecast_data,
                context=context,
                trace_ctx=trace_ctx,
                tenant_id=tenant_id,
            )
        elif action_type == "reduce_autonomy_level":
            return await self._reduce_autonomy_level(
                action_policy=action_policy,
                forecast_data=forecast_data,
                context=context,
                trace_ctx=trace_ctx,
                tenant_id=tenant_id,
            )
        elif action_type == "gate_mode_change":
            return await self._gate_mode_change(
                action_policy=action_policy,
                forecast_data=forecast_data,
                context=context,
                trace_ctx=trace_ctx,
                tenant_id=tenant_id,
            )
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    async def _create_ticket(
        self,
        action_policy: Any,
        forecast_data: Dict[str, Any],
        context: Dict[str, Any],
        trace_ctx: Optional[TraceContext],
        tenant_id: Optional[str],
    ) -> Dict[str, Any]:
        """Create ticket via EPC-4."""
        if not self.epc4_client:
            logger.warning("EPC-4 client not available, skipping ticket creation")
            return {"ticket_created": False, "reason": "EPC-4 client not available"}

        # Build ticket payload
        action_params = action_policy.action_parameters or {}
        title_template = action_params.get("ticket_title_template", "Prevent-First Action: SLO Breach Forecast")
        description_template = action_params.get(
            "ticket_description_template",
            "Forecast indicates potential SLO breach. Time to breach: {time_to_breach_seconds}s, Confidence: {confidence}",
        )

        time_to_breach = forecast_data.get("time_to_breach_seconds")
        confidence = forecast_data.get("confidence", 0.0)

        format_args = {**forecast_data, **context}
        title = title_template
        try:
            description = description_template.format(**format_args)
        except KeyError:
            description = description_template.format(
                time_to_breach_seconds=time_to_breach,
                confidence=confidence,
            )

        # Determine severity from forecast
        severity = "WARN"
        if time_to_breach is not None and time_to_breach < 3600:  # < 1 hour
            severity = "CRITICAL"
        elif time_to_breach is not None and time_to_breach < 14400:  # < 4 hours
            severity = "ERROR"

        # Create alert via EPC-4
        try:
            alert_payload = {
                "tenant_id": tenant_id or "unknown",
                "component_id": context.get("component", "observability"),
                "category": "prevent_first_forecast",
                "severity": severity,
                "title": title,
                "description": description,
                "metadata": {
                    "forecast_id": forecast_data.get("forecast_id"),
                    "slo_id": forecast_data.get("slo_id"),
                    "sli_id": forecast_data.get("sli_id"),
                    "time_to_breach_seconds": time_to_breach,
                    "confidence": confidence,
                    "trace_id": trace_ctx.trace_id if trace_ctx else None,
                },
            }

            # Call EPC-4 API (simplified - in practice would use proper client)
            if hasattr(self.epc4_client, "emit_alert"):
                self.epc4_client.emit_alert(alert_payload)
            elif hasattr(self.epc4_client, "post"):
                await self.epc4_client.post("/v1/alerts", json=alert_payload)

            return {"ticket_created": True, "alert_payload": alert_payload}
        except Exception as e:
            logger.error(f"Failed to create ticket via EPC-4: {e}", exc_info=True)
            return {"ticket_created": False, "reason": str(e)}

    async def _request_human_validation(
        self,
        action_policy: Any,
        forecast_data: Dict[str, Any],
        context: Dict[str, Any],
        trace_ctx: Optional[TraceContext],
        tenant_id: Optional[str],
    ) -> Dict[str, Any]:
        """Request human-in-the-loop validation."""
        # This would integrate with a human validation service
        # For now, create a ticket requesting validation
        return await self._create_ticket(
            action_policy=action_policy,
            forecast_data=forecast_data,
            context={**context, "validation_requested": True},
            trace_ctx=trace_ctx,
            tenant_id=tenant_id,
        )

    async def _reduce_autonomy_level(
        self,
        action_policy: Any,
        forecast_data: Dict[str, Any],
        context: Dict[str, Any],
        trace_ctx: Optional[TraceContext],
        tenant_id: Optional[str],
    ) -> Dict[str, Any]:
        """Reduce autonomy level (stub - would integrate with autonomy management)."""
        action_params = action_policy.action_parameters or {}
        target_level = action_params.get("autonomy_level", "restricted")

        logger.info(f"Reducing autonomy level to {target_level} for tenant {tenant_id}")
        # In practice, this would call an autonomy management service

        return {"autonomy_level": target_level, "status": "reduced"}

    async def _gate_mode_change(
        self,
        action_policy: Any,
        forecast_data: Dict[str, Any],
        context: Dict[str, Any],
        trace_ctx: Optional[TraceContext],
        tenant_id: Optional[str],
    ) -> Dict[str, Any]:
        """Gate mode change (stub - would integrate with mode management)."""
        action_params = action_policy.action_parameters or {}
        mode_gate = action_params.get("mode_gate", "default")

        logger.info(f"Gating mode change {mode_gate} for tenant {tenant_id}")
        # In practice, this would call a mode management service

        return {"mode_gate": mode_gate, "status": "gated"}

    async def _generate_receipt(
        self,
        action_id: str,
        action_type: str,
        forecast_data: Dict[str, Any],
        authorization: Optional[Dict[str, Any]],
        action_result: Dict[str, Any],
        trace_ctx: TraceContext,
        tenant_id: Optional[str],
    ) -> Optional[str]:
        """Generate receipt via PM-7."""
        if not self.receipt_service:
            return None

        try:
            # Build receipt payload
            receipt_payload = {
                "gate_id": "prevent_first_action",
                "inputs": {
                    "action_id": action_id,
                    "action_type": action_type,
                    "forecast_data": forecast_data,
                    "authorization": authorization,
                },
                "decision": "pass" if action_result.get("status") == "executed" else "warn",
                "result": action_result,
                "actor": {
                    "actor_id": "zeroui_observability",
                    "actor_type": "system",
                },
                "trace_context": {
                    "trace_id": trace_ctx.trace_id,
                    "span_id": trace_ctx.span_id,
                },
            }

            # Generate receipt (simplified - in practice would use proper ReceiptService API)
            if hasattr(self.receipt_service, "generate_receipt"):
                receipt = await self.receipt_service.generate_receipt(receipt_payload)
                return receipt.get("receipt_id") if receipt else None
            else:
                # Fallback: generate receipt ID
                return f"receipt_{uuid.uuid4().hex[:16]}"

        except Exception as e:
            logger.error(f"Failed to generate receipt: {e}", exc_info=True)
            return None
