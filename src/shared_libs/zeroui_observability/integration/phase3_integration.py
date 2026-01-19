"""
Phase 3 Integration Layer - Wires forecast and prevent-first services with existing phases.

Integrates Phase 3 (Forecast & Prevent-First) with Phase 0, Phase 1, and Phase 2.
"""

import logging
from typing import Any, Dict, List, Optional

from ..correlation.trace_context import TraceContext, get_or_create_trace_context
from ..instrumentation.python.instrumentation import EventEmitter, get_event_emitter
from ..sli.sli_calculator import SLICalculator
from ..alerting.alert_config import AlertConfigLoader, AlertConfig
from ..forecast.forecast_service import ForecastService
from ..prevent_first.prevent_first_service import PreventFirstService
from ..prevent_first.action_executor import ActionExecutor
from ..prevent_first.action_policy import ActionPolicy

logger = logging.getLogger(__name__)


class Phase3IntegrationService:
    """
    Phase 3 integration service.

    Wires forecast and prevent-first services with existing observability phases.
    Provides unified interface for forecast-based proactive SLO management.
    """

    def __init__(
        self,
        event_emitter: Optional[EventEmitter] = None,
        sli_calculator: Optional[SLICalculator] = None,
        alert_config_loader: Optional[AlertConfigLoader] = None,
        forecast_service: Optional[ForecastService] = None,
        prevent_first_service: Optional[PreventFirstService] = None,
        epc4_client: Optional[Any] = None,  # EPC-4 client
        receipt_service: Optional[Any] = None,  # PM-7 receipt service
    ):
        """
        Initialize Phase 3 integration service.

        Args:
            event_emitter: Event emitter (Phase 0)
            sli_calculator: SLI calculator (Phase 1)
            alert_config_loader: Alert config loader (Phase 2)
            forecast_service: Forecast service (Phase 3)
            prevent_first_service: Prevent-first service (Phase 3)
            epc4_client: EPC-4 alerting service client
            receipt_service: PM-7 receipt service
        """
        # Phase 0
        self.event_emitter = event_emitter or get_event_emitter()

        # Phase 1
        self.sli_calculator = sli_calculator or SLICalculator()

        # Phase 2
        self.alert_config_loader = alert_config_loader or AlertConfigLoader()

        # Phase 3 - Forecast
        self.forecast_service = forecast_service or ForecastService(
            sli_calculator=self.sli_calculator,
            event_emitter=self.event_emitter,
        )

        # Phase 3 - Prevent-First
        action_policy = ActionPolicy()
        action_executor = ActionExecutor(
            epc4_client=epc4_client,
            receipt_service=receipt_service,
            action_policy=action_policy,
        )
        self.prevent_first_service = prevent_first_service or PreventFirstService(
            action_executor=action_executor,
            action_policy=action_policy,
        )

    async def compute_forecasts_for_alert_configs(
        self,
        alert_configs: List[AlertConfig],
        slo_objectives: Dict[str, float],
        sli_mappings: Dict[str, str],
        window_data_by_slo: Dict[str, Dict[str, Dict[str, int]]],
        component: str = "backend",
        channel: str = "backend",
        trace_ctx: Optional[TraceContext] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compute forecasts for alert configurations.

        Args:
            alert_configs: List of alert configurations
            slo_objectives: SLO objectives by SLO ID
            sli_mappings: SLI ID mappings by SLO ID
            window_data_by_slo: Window data by SLO ID
            component: Component name
            channel: Channel name
            trace_ctx: Optional trace context

        Returns:
            List of forecast results
        """
        return await self.forecast_service.compute_forecasts_for_slos(
            alert_configs=alert_configs,
            slo_objectives=slo_objectives,
            sli_mappings=sli_mappings,
            window_data_by_slo=window_data_by_slo,
            component=component,
            channel=channel,
            trace_ctx=trace_ctx,
        )

    async def evaluate_forecasts_and_trigger_actions(
        self,
        forecasts: List[Dict[str, Any]],
        action_mappings: Optional[Dict[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
        trace_ctx: Optional[TraceContext] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate forecasts and trigger prevent-first actions.

        Args:
            forecasts: List of forecast results
            action_mappings: Optional mapping of SLO ID to action ID
            context: Additional context
            trace_ctx: Optional trace context
            tenant_id: Optional tenant ID
            environment: Optional environment

        Returns:
            List of action execution results
        """
        return await self.prevent_first_service.evaluate_forecasts_and_trigger(
            forecasts=forecasts,
            action_mappings=action_mappings,
            context=context,
            trace_ctx=trace_ctx,
            tenant_id=tenant_id,
            environment=environment,
        )

    async def forecast_and_prevent_workflow(
        self,
        alert_configs: List[AlertConfig],
        slo_objectives: Dict[str, float],
        sli_mappings: Dict[str, str],
        window_data_by_slo: Dict[str, Dict[str, Dict[str, int]]],
        action_mappings: Optional[Dict[str, str]] = None,
        component: str = "backend",
        channel: str = "backend",
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        trace_ctx: Optional[TraceContext] = None,
    ) -> Dict[str, Any]:
        """
        Complete forecast-and-prevent workflow.

        Computes forecasts, evaluates them, and triggers prevent-first actions.

        Args:
            alert_configs: List of alert configurations
            slo_objectives: SLO objectives by SLO ID
            sli_mappings: SLI ID mappings by SLO ID
            window_data_by_slo: Window data by SLO ID
            action_mappings: Optional mapping of SLO ID to action ID
            component: Component name
            channel: Channel name
            tenant_id: Optional tenant ID
            environment: Optional environment
            trace_ctx: Optional trace context

        Returns:
            Workflow result with forecasts and action results
        """
        if trace_ctx is None:
            trace_ctx = get_or_create_trace_context()

        # Step 1: Compute forecasts
        forecasts = await self.compute_forecasts_for_alert_configs(
            alert_configs=alert_configs,
            slo_objectives=slo_objectives,
            sli_mappings=sli_mappings,
            window_data_by_slo=window_data_by_slo,
            component=component,
            channel=channel,
            trace_ctx=trace_ctx,
        )

        # Step 2: Evaluate forecasts and trigger actions
        action_results = await self.evaluate_forecasts_and_trigger_actions(
            forecasts=forecasts,
            action_mappings=action_mappings,
            context={"component": component, "channel": channel},
            trace_ctx=trace_ctx,
            tenant_id=tenant_id,
            environment=environment,
        )

        return {
            "forecasts": forecasts,
            "action_results": action_results,
            "trace_id": trace_ctx.trace_id,
        }
