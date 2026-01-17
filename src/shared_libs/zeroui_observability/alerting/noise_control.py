"""
OBS-12: Noise Control (Dedup, Rate-limit, Suppression) + FPR SLI.

Fingerprints alerts; dedups; rate-limits; measures false positive rate from feedback loops.
Emits alert.noise_control.v1 events for every suppression/merge decision.

Integrated with Phase 0 (EventEmitter) and Phase 1 (SLI Calculator).
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

# Phase 0 integration: EventEmitter and EventType
try:
    from ..contracts.event_types import EventType
    from ..instrumentation.python.instrumentation import EventEmitter
    from ..correlation.trace_context import get_or_create_trace_context, TraceContext
    PHASE0_AVAILABLE = True
except ImportError:
    # Fallback if Phase 0 not available
    PHASE0_AVAILABLE = False
    EventType = None  # type: ignore
    EventEmitter = None  # type: ignore
    TraceContext = None  # type: ignore
    
    def get_or_create_trace_context():
        """Fallback trace context creator."""
        class FallbackTraceContext:
            trace_id = "fallback-trace-id"
            span_id = "fallback-span-id"
        return FallbackTraceContext()

logger = logging.getLogger(__name__)


@dataclass
class AlertFingerprint:
    """Alert fingerprint for deduplication."""

    fingerprint: str
    components: Dict[str, Any]  # Components used to generate fingerprint


class NoiseControlProcessor:
    """
    Noise control processor for alert deduplication, rate limiting, and suppression.
    
    Emits alert.noise_control.v1 events for every decision (allow, suppress, dedup, rate_limited).
    """

    def __init__(
        self,
        dedup_window_seconds: int = 900,  # 15 minutes default
        rate_limit_window_seconds: int = 3600,  # 1 hour default
        max_alerts_per_window: int = 5,
        event_emitter: Optional[EventEmitter] = None,
        component: str = "alerting-noise-control",
        channel: str = "backend",
    ):
        """
        Initialize noise control processor.
        
        Args:
            dedup_window_seconds: Deduplication window in seconds
            rate_limit_window_seconds: Rate limit window in seconds
            max_alerts_per_window: Maximum alerts per fingerprint per window
            event_emitter: Optional EventEmitter instance (creates default if None)
            component: Component name for event emission
            channel: Channel name for event emission
        """
        self.dedup_window_seconds = dedup_window_seconds
        self.rate_limit_window_seconds = rate_limit_window_seconds
        self.max_alerts_per_window = max_alerts_per_window

        # Phase 0 integration: EventEmitter for emitting alert.noise_control.v1 events
        if PHASE0_AVAILABLE and EventEmitter:
            self._event_emitter = event_emitter or EventEmitter(
                component=component,
                channel=channel,
            )
        else:
            self._event_emitter = None
            logger.warning("Phase 0 EventEmitter not available, alert.noise_control.v1 events will not be emitted")

        # In-memory state (in production, use Redis or similar)
        self._fingerprint_history: Dict[str, List[datetime]] = {}
        self._suppression_reasons: Dict[str, str] = {}

    def compute_fingerprint(
        self,
        alert_id: str,
        component: str,
        channel: Optional[str] = None,
        slo_id: Optional[str] = None,
        alert_type: Optional[str] = None,
        additional_keys: Optional[Dict[str, Any]] = None,
    ) -> AlertFingerprint:
        """
        Compute deterministic fingerprint for alert deduplication.
        
        Args:
            alert_id: Alert ID
            component: Component identifier
            channel: Optional channel identifier
            slo_id: Optional SLO ID
            alert_type: Optional alert type ("fast" | "slow")
            additional_keys: Optional additional keys for fingerprinting
            
        Returns:
            AlertFingerprint
        """
        components = {
            "alert_id": alert_id,
            "component": component,
        }
        if channel:
            components["channel"] = channel
        if slo_id:
            components["slo_id"] = slo_id
        if alert_type:
            components["alert_type"] = alert_type
        if additional_keys:
            components.update(additional_keys)

        # Create deterministic fingerprint
        fingerprint_str = json.dumps(components, sort_keys=True)
        fingerprint = hashlib.sha256(fingerprint_str.encode("utf-8")).hexdigest()[:16]

        return AlertFingerprint(fingerprint=fingerprint, components=components)

    def should_dedup(
        self,
        fingerprint: AlertFingerprint,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if alert should be deduplicated.
        
        Args:
            fingerprint: AlertFingerprint
            now: Optional current time (for testing)
            
        Returns:
            Tuple of (should_dedup, reason)
        """
        if now is None:
            now = datetime.utcnow()

        fp = fingerprint.fingerprint
        window_start = now - timedelta(seconds=self.dedup_window_seconds)

        # Get history for this fingerprint
        history = self._fingerprint_history.get(fp, [])
        recent_alerts = [ts for ts in history if ts >= window_start]

        if recent_alerts:
            # Update history (keep only recent)
            self._fingerprint_history[fp] = recent_alerts
            return True, "dedup"

        # Add to history
        if fp not in self._fingerprint_history:
            self._fingerprint_history[fp] = []
        self._fingerprint_history[fp].append(now)

        return False, None

    def should_rate_limit(
        self,
        fingerprint: AlertFingerprint,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if alert should be rate-limited.
        
        Args:
            fingerprint: AlertFingerprint
            now: Optional current time (for testing)
            
        Returns:
            Tuple of (should_rate_limit, reason)
        """
        if now is None:
            now = datetime.utcnow()

        fp = fingerprint.fingerprint
        window_start = now - timedelta(seconds=self.rate_limit_window_seconds)

        # Get history for this fingerprint
        history = self._fingerprint_history.get(fp, [])
        recent_alerts = [ts for ts in history if ts >= window_start]

        if len(recent_alerts) >= self.max_alerts_per_window:
            return True, "rate_limited"

        return False, None

    async def process_alert(
        self,
        alert_event: Dict[str, Any],
        fingerprint: Optional[AlertFingerprint] = None,
        trace_ctx: Optional[Any] = None,  # TraceContext from Phase 0
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process alert through noise control pipeline.
        
        Args:
            alert_event: Alert event dictionary
            fingerprint: Optional pre-computed fingerprint
            trace_ctx: Optional trace context (creates new if not provided)
            
        Returns:
            Tuple of (decision, alert.noise_control.v1 event payload)
            decision: "allow" | "suppress" | "dedup" | "rate_limited"
        """
        # Compute fingerprint if not provided
        if fingerprint is None:
            fingerprint = self.compute_fingerprint(
                alert_id=alert_event.get("alert_id", ""),
                component=alert_event.get("component", ""),
                channel=alert_event.get("channel"),
                slo_id=alert_event.get("slo_id"),
                alert_type=alert_event.get("alert_type"),
            )

        # Check rate limit first (stricter)
        should_rate_limit, rate_limit_reason = self.should_rate_limit(fingerprint)
        if should_rate_limit:
            decision = "rate_limited"
            reason = rate_limit_reason
        else:
            # Check dedup
            should_dedup, dedup_reason = self.should_dedup(fingerprint)
            if should_dedup:
                decision = "dedup"
                reason = dedup_reason
            else:
                decision = "allow"
                reason = None

        # Count alerts in window for event
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.dedup_window_seconds)
        history = self._fingerprint_history.get(fingerprint.fingerprint, [])
        count_in_window = len([ts for ts in history if ts >= window_start])

        # Create alert.noise_control.v1 event payload
        noise_control_payload = self._create_noise_control_event(
            alert_id=alert_event.get("alert_id", ""),
            fingerprint=fingerprint,
            decision=decision,
            window="dedup",
            count_in_window=count_in_window,
            reason=reason,
            component=alert_event.get("component", ""),
        )

        # Phase 0 integration: Emit event via EventEmitter with proper envelope
        if self._event_emitter and PHASE0_AVAILABLE and EventType:
            try:
                # Get trace context (use provided or create new)
                if trace_ctx is None:
                    trace_ctx = get_or_create_trace_context()

                # Determine severity based on decision
                severity = "warn" if decision in ["dedup", "rate_limited"] else "info"

                # Emit event asynchronously (non-blocking)
                await self._event_emitter.emit_event(
                    event_type=EventType.ALERT_NOISE_CONTROL,
                    payload=noise_control_payload,
                    severity=severity,
                    trace_ctx=trace_ctx,
                )
            except Exception as e:
                logger.error(f"Failed to emit alert.noise_control.v1 event: {e}", exc_info=True)
        else:
            logger.debug("EventEmitter not available, skipping alert.noise_control.v1 emission")

        return decision, noise_control_payload

    def _create_noise_control_event(
        self,
        alert_id: str,
        fingerprint: AlertFingerprint,
        decision: str,
        window: str,
        count_in_window: int,
        reason: Optional[str],
        component: str,
    ) -> Dict[str, Any]:
        """
        Create alert.noise_control.v1 event payload.
        
        Args:
            alert_id: Alert ID
            fingerprint: AlertFingerprint
            decision: "allow" | "suppress" | "dedup" | "rate_limited"
            window: Window name (e.g., "dedup")
            count_in_window: Count of alerts in window
            reason: Optional reason fingerprint
            component: Component identifier
            
        Returns:
            Event payload dictionary
        """
        reason_fingerprint = None
        if reason:
            reason_fingerprint = hashlib.sha256(reason.encode("utf-8")).hexdigest()[:16]

        return {
            "alert_id": alert_id,
            "alert_fingerprint": fingerprint.fingerprint,
            "decision": decision,
            "window": window,
            "count_in_window": count_in_window,
            "reason_fingerprint": reason_fingerprint,
            "component": component,
        }

    def record_false_positive(
        self,
        fingerprint: AlertFingerprint,
        is_false_positive: bool,
        human_validator: Optional[str] = None,
    ) -> None:
        """
        Record false positive feedback for FPR SLI computation.
        
        Args:
            fingerprint: AlertFingerprint
            is_false_positive: True if alert was false positive
            human_validator: Optional human validator identifier
        """
        # In production, this would write to a database for FPR SLI computation
        # For now, log it
        logger.info(
            f"False positive feedback: fingerprint={fingerprint.fingerprint}, "
            f"is_false_positive={is_false_positive}, validator={human_validator}"
        )

    def get_fpr_data(
        self,
        detector_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get false positive rate data for FPR SLI computation.
        
        Args:
            detector_type: Optional detector type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary with false_positive and true_positive counts
        """
        # In production, this would query a database
        # For now, return placeholder
        return {
            "false_positive": 0,
            "true_positive": 0,
            "detector_type": detector_type,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        }
