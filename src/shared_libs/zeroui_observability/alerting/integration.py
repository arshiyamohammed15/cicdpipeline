"""
Integration layer for Phase 2 Alerting & Noise Control.

Wires burn-rate alert engine with:
- Phase 0: EventEmitter, trace context, event types
- Phase 1: SLI Calculator (for SLI-G FPR computation)
- EPC-4 (Alerting & Notification Service)
- EPC-5 (Health & Reliability Monitoring)
"""

import logging
from typing import Any, Dict, List, Optional

# Phase 0 integration
try:
    from ..correlation.trace_context import get_or_create_trace_context, TraceContext
    PHASE0_AVAILABLE = True
except ImportError:
    PHASE0_AVAILABLE = False
    TraceContext = None  # type: ignore
    
    def get_or_create_trace_context():
        """Fallback trace context creator."""
        class FallbackTraceContext:
            trace_id = "fallback-trace-id"
            span_id = "fallback-span-id"
        return FallbackTraceContext()

# Phase 1 integration
try:
    from ..sli.sli_calculator import SLICalculator, SLIResult
    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False
    SLICalculator = None  # type: ignore
    SLIResult = None  # type: ignore

from .alert_config import AlertConfig, AlertConfigLoader
from .burn_rate_engine import BurnRateAlertEngine, AlertEvaluationResult
from .noise_control import NoiseControlProcessor, AlertFingerprint

logger = logging.getLogger(__name__)


class ObservabilityAlertingService:
    """
    Service that integrates Phase 2 alerting with existing ZeroUI services.
    
    Coordinates:
    - Burn-rate evaluation from SLI data
    - Noise control (dedup, rate-limit)
    - Alert event emission to EPC-4
    - FPR tracking for SLI-G
    """

    def __init__(
        self,
        config_loader: AlertConfigLoader,
        noise_control: NoiseControlProcessor,
        epc4_client: Optional[Any] = None,  # EPC-4 Alerting Service client
        sli_calculator: Optional[SLICalculator] = None,  # Phase 1: SLI Calculator for SLI-G
    ):
        """
        Initialize service.
        
        Args:
            config_loader: AlertConfigLoader instance
            noise_control: NoiseControlProcessor instance
            epc4_client: Optional EPC-4 client (for alert routing)
            sli_calculator: Optional SLI calculator (Phase 1) for SLI-G FPR computation
        """
        self.config_loader = config_loader
        self.noise_control = noise_control
        self.epc4_client = epc4_client
        
        # Phase 1 integration: SLI Calculator for SLI-G (False Positive Rate)
        if PHASE1_AVAILABLE and SLICalculator:
            self.sli_calculator = sli_calculator or SLICalculator()
        else:
            self.sli_calculator = None
            logger.warning("Phase 1 SLI Calculator not available, SLI-G computation disabled")

    async def evaluate_and_route_alert(
        self,
        alert_id: str,
        window_data: Dict[str, Dict[str, int]],
        slo_objective: float,
        component: str,
        channel: str,
        trace_ctx: Optional[TraceContext] = None,  # Phase 0: Trace context
        confidence: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate alert using burn-rate engine and route through noise control.
        
        Args:
            alert_id: Alert ID (must match loaded config)
            window_data: Dict mapping window_name to {"error_count": int, "total_count": int}
            slo_objective: SLO target (e.g., 0.99 for 99%)
            component: Component identifier
            channel: Channel identifier
            trace_ctx: Optional trace context (Phase 0) - creates new if not provided
            confidence: Optional confidence score for confidence-gated alerts
            
        Returns:
            Dictionary with evaluation result and routing decision
        """
        # Phase 0: Get or create trace context
        if PHASE0_AVAILABLE:
            if trace_ctx is None:
                trace_ctx = get_or_create_trace_context()
        else:
            # Fallback if Phase 0 not available
            trace_ctx = None

        # Load alert config
        config = self.config_loader.get_config(alert_id)
        if not config:
            raise ValueError(f"Alert config not found: {alert_id}")

        # Evaluate burn-rate
        engine = BurnRateAlertEngine(config)
        evaluation_result = engine.evaluate_alert(
            window_data=window_data,
            slo_objective=slo_objective,
            confidence=confidence,
        )

        if not evaluation_result.should_fire:
            return {
                "alert_id": alert_id,
                "should_fire": False,
                "reason": evaluation_result.reason,
                "noise_control_decision": None,
                "trace_id": trace_ctx.trace_id if trace_ctx else None,
            }

        # Create alert event
        alert_event = engine.create_alert_event(
            evaluation_result=evaluation_result,
            slo_id=config.slo_id,
            component=component,
            channel=channel,
            trace_id=trace_ctx.trace_id if trace_ctx else None,  # Phase 0: Use trace context
        )

        # Process through noise control (Phase 0 integration: emits alert.noise_control.v1)
        decision, noise_control_payload = await self.noise_control.process_alert(
            alert_event,
            trace_ctx=trace_ctx,
        )

        # Route to EPC-4 if allowed
        routed = False
        if decision == "allow" and self.epc4_client:
            try:
                # Route based on config
                if config.routing.mode == "ticket":
                    # Create ticket via EPC-4
                    ticket_result = self._create_ticket(alert_event, config)
                    routed = True
                    logger.info(f"Alert {alert_id} routed to ticket: {ticket_result}")
                elif config.routing.mode == "page":
                    # Page via EPC-4 (disabled in ticket mode)
                    logger.warning(f"Paging disabled in ticket mode for alert {alert_id}")
            except Exception as e:
                logger.error(f"Failed to route alert {alert_id} to EPC-4: {e}", exc_info=True)

        return {
            "alert_id": alert_id,
            "should_fire": True,
            "alert_type": evaluation_result.alert_type,
            "noise_control_decision": decision,
            "noise_control_payload": noise_control_payload,
            "routed": routed,
            "routing_mode": config.routing.mode,
            "trace_id": trace_ctx.trace_id if trace_ctx else None,  # Phase 0: Include trace ID
        }

    def _create_ticket(
        self,
        alert_event: Dict[str, Any],
        config: AlertConfig,
    ) -> Dict[str, Any]:
        """
        Create ticket via EPC-4 (stub implementation).
        
        Args:
            alert_event: Alert event dictionary
            config: AlertConfig
            
        Returns:
            Ticket creation result
        """
        # In production, this would call EPC-4 API
        # For now, return stub
        if self.epc4_client:
            # Example: await self.epc4_client.create_alert(...)
            pass

        return {
            "ticket_id": f"ticket-{alert_event['alert_id']}",
            "target": config.routing.target,
            "mode": config.routing.mode,
        }

    def record_false_positive_feedback(
        self,
        alert_id: str,
        fingerprint: AlertFingerprint,
        is_false_positive: bool,
        human_validator: Optional[str] = None,
        detector_type: Optional[str] = None,
    ) -> Optional[SLIResult]:
        """
        Record false positive feedback for SLI-G computation (Phase 1 integration).
        
        Args:
            alert_id: Alert ID
            fingerprint: AlertFingerprint
            is_false_positive: True if alert was false positive
            human_validator: Optional human validator identifier
            detector_type: Optional detector type for SLI-G grouping
            
        Returns:
            SLIResult for SLI-G if computed, None otherwise
        """
        # Record in noise control
        self.noise_control.record_false_positive(
            fingerprint=fingerprint,
            is_false_positive=is_false_positive,
            human_validator=human_validator,
        )

        # Phase 1 integration: Compute SLI-G (False Positive Rate) using SLI Calculator
        if self.sli_calculator:
            try:
                # Get FPR data from noise control
                fpr_data = self.noise_control.get_fpr_data(detector_type=detector_type)
                
                # Compute SLI-G: false_positive / (false_positive + true_positive)
                false_positive = fpr_data.get("false_positive", 0)
                true_positive = fpr_data.get("true_positive", 0)
                
                if false_positive + true_positive > 0:
                    fpr_value = false_positive / (false_positive + true_positive)
                    
                    # Create SLI result (matching SLI-G formula from PRD)
                    sli_result = SLIResult(
                        sli_id="SLI-G",
                        sli_name="False Positive Rate (FPR)",
                        value=fpr_value,
                        numerator=float(false_positive),
                        denominator=float(false_positive + true_positive),
                        grouping={"detector_type": detector_type or "unknown", "alert_fingerprint": fingerprint.fingerprint},
                        metadata={
                            "false_positive": false_positive,
                            "true_positive": true_positive,
                            "human_validator": human_validator,
                        },
                    )
                    
                    logger.info(
                        f"SLI-G computed for alert {alert_id}: FPR={fpr_value:.4f} "
                        f"(FP={false_positive}, TP={true_positive})"
                    )
                    return sli_result
                else:
                    logger.debug(f"Insufficient data for SLI-G computation: FP={false_positive}, TP={true_positive}")
            except Exception as e:
                logger.error(f"Failed to compute SLI-G for alert {alert_id}: {e}", exc_info=True)

        return None
