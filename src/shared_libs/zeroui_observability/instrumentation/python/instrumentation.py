"""
Python instrumentation for ZeroUI Observability Layer.

Async/non-blocking telemetry emission using OpenTelemetry OTLP.
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode
    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False
    trace = None  # type: ignore

from ...contracts.event_types import EventType
from ...correlation.trace_context import get_or_create_trace_context, TraceContext
from ...privacy.redaction_enforcer import RedactionEnforcer

logger = logging.getLogger(__name__)


class EventEmitter:
    """
    Event emitter for ZeroUI Observability Layer.

    Emits events using Phase 0 contracts (envelope + payload schemas).
    Applies redaction before emission and propagates trace context.
    """

    def __init__(
        self,
        otlp_endpoint: Optional[str] = None,
        enabled: bool = True,
        component: str = "backend",
        channel: str = "backend",
        version: Optional[str] = None,
    ):
        """
        Initialize event emitter.

        Args:
            otlp_endpoint: OTLP exporter endpoint (defaults to env var)
            enabled: Whether emission is enabled (defaults to feature flag)
            component: Component name
            channel: Channel name (ide, edge_agent, backend, ci, other)
            version: Component version
        """
        self._enabled = enabled and self._check_feature_flag()
        self._component = component
        self._channel = channel
        self._version = version or os.getenv("COMPONENT_VERSION", "unknown")

        # Initialize redaction enforcer
        self._redaction_enforcer = RedactionEnforcer(use_cccs=False)

        # Initialize OTLP if available
        self._otlp_initialized = False
        if OTLP_AVAILABLE and self._enabled:
            self._init_otlp(otlp_endpoint)

    def _check_feature_flag(self) -> bool:
        """Check if observability is enabled via feature flag."""
        return os.getenv("ZEROUI_OBSV_ENABLED", "true").lower() == "true"

    def _init_otlp(self, endpoint: Optional[str] = None) -> None:
        """Initialize OpenTelemetry OTLP exporter."""
        if not OTLP_AVAILABLE:
            logger.warning("OpenTelemetry not available, event emission disabled")
            return

        try:
            endpoint = endpoint or os.getenv("OTLP_EXPORTER_ENDPOINT", "http://localhost:4317")

            # Create resource
            resource = Resource.create({
                "service.name": self._component,
                "service.version": self._version,
                "zeroui.channel": self._channel,
            })

            # Create tracer provider
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            # Create OTLP exporter
            otlp_exporter = OTLPSpanExporter(endpoint=endpoint)

            # Add batch processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)

            self._otlp_initialized = True
            logger.info(f"OTLP exporter initialized: {endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize OTLP exporter: {e}", exc_info=True)

    async def emit_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        severity: str = "info",
        trace_ctx: Optional[TraceContext] = None,
    ) -> bool:
        """
        Emit observability event asynchronously.

        Args:
            event_type: Event type (from EventType enum)
            payload: Event payload (must match event type schema)
            severity: Event severity (debug, info, warn, error, critical)
            trace_ctx: Optional trace context (creates new if not provided)

        Returns:
            True if event was emitted, False otherwise
        """
        if not self._enabled:
            return False

        try:
            # Get or create trace context
            if trace_ctx is None:
                trace_ctx = get_or_create_trace_context()

            # Apply redaction to payload
            redaction_result = self._redaction_enforcer.enforce(
                payload,
                compute_fingerprints=True,
            )
            redacted_payload = redaction_result.redacted_payload
            redacted_payload["redaction_applied"] = redaction_result.redaction_applied

            # Create event envelope
            event = self._create_envelope(
                event_type=event_type,
                payload=redacted_payload,
                severity=severity,
                trace_ctx=trace_ctx,
            )

            # Emit via OTLP (async, non-blocking)
            await self._emit_otlp_log(event)

            return True
        except Exception as e:
            logger.error(f"Failed to emit event {event_type.value}: {e}", exc_info=True)
            return False

    def _create_envelope(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        severity: str,
        trace_ctx: TraceContext,
    ) -> Dict[str, Any]:
        """
        Create event envelope per zero_ui.obsv.event.v1 schema.

        Args:
            event_type: Event type
            payload: Event payload
            severity: Event severity
            trace_ctx: Trace context

        Returns:
            Event envelope dictionary
        """
        return {
            "event_id": f"evt_{uuid.uuid4().hex[:16]}",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "severity": severity,
            "source": {
                "component": self._component,
                "channel": self._channel,
                "version": self._version,
            },
            "correlation": {
                "trace_id": trace_ctx.trace_id,
                "span_id": trace_ctx.span_id,
            },
            "payload": payload,
        }

    async def _emit_otlp_log(self, event: Dict[str, Any]) -> None:
        """
        Emit event as OTLP log record (async, non-blocking).

        Args:
            event: Event envelope dictionary
        """
        if not self._otlp_initialized or not OTLP_AVAILABLE:
            logger.debug("OTLP not initialized, skipping emission")
            return

        try:
            # Use OpenTelemetry logging API to emit as log record
            # Events are transported as OTLP Logs per architecture
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span("zeroui.obsv.event") as span:
                # Set span attributes from event
                span.set_attribute("event.id", event["event_id"])
                span.set_attribute("event.type", event["event_type"])
                span.set_attribute("event.severity", event["severity"])
                span.set_attribute("zeroui.component", event["source"]["component"])
                span.set_attribute("zeroui.channel", event["source"]["channel"])

                # Log event as structured log (will be exported as OTLP log)
                logger.info(
                    "ZeroUI observability event",
                    extra={
                        "zeroui_event": event,
                        "trace_id": event["correlation"]["trace_id"],
                        "span_id": event["correlation"]["span_id"],
                    },
                )
        except Exception as e:
            logger.error(f"Failed to emit OTLP log: {e}", exc_info=True)

    async def emit_perf_sample(
        self,
        operation: str,
        latency_ms: int,
        trace_ctx: Optional[TraceContext] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Emit perf.sample.v1 event.

        Args:
            operation: Operation name
            latency_ms: Latency in milliseconds
            trace_ctx: Optional trace context
            **kwargs: Additional payload fields (cache_hit, async_path, queue_depth, etc.)

        Returns:
            True if event was emitted
        """
        payload = {
            "operation": operation,
            "latency_ms": latency_ms,
            "component": self._component,
            "channel": self._channel,
            **kwargs,
        }
        return await self.emit_event(
            EventType.PERF_SAMPLE,
            payload,
            severity="info",
            trace_ctx=trace_ctx,
        )

    async def emit_error_captured(
        self,
        error_class: str,
        error_code: str,
        stage: str,
        trace_ctx: Optional[TraceContext] = None,
        **kwargs: Any,
    ) -> bool:
        """
        Emit error.captured.v1 event.

        Args:
            error_class: Error class (data, architecture, prompt, retrieval, memory, tool, orchestration, security, unknown)
            error_code: Error code
            stage: Stage where error occurred
            trace_ctx: Optional trace context
            **kwargs: Additional payload fields (message_fingerprint, input_fingerprint, etc.)

        Returns:
            True if event was emitted
        """
        import hashlib

        # Compute fingerprints for required fields
        message = kwargs.get("message", "")
        message_fingerprint = hashlib.sha256(message.encode("utf-8")).hexdigest() if message else ""

        payload = {
            "error_class": error_class,
            "error_code": error_code,
            "stage": stage,
            "message_fingerprint": message_fingerprint,
            "input_fingerprint": kwargs.get("input_fingerprint", ""),
            "output_fingerprint": kwargs.get("output_fingerprint", ""),
            "internal_state_fingerprint": kwargs.get("internal_state_fingerprint", ""),
            "component": self._component,
            "channel": self._channel,
            **{k: v for k, v in kwargs.items() if k not in ["message"]},
        }
        return await self.emit_event(
            EventType.ERROR_CAPTURED,
            payload,
            severity="error",
            trace_ctx=trace_ctx,
        )


# Global event emitter instance
_event_emitter: Optional[EventEmitter] = None


def get_event_emitter() -> EventEmitter:
    """
    Get global event emitter instance (singleton).

    Returns:
        EventEmitter instance
    """
    global _event_emitter
    if _event_emitter is None:
        _event_emitter = EventEmitter()
    return _event_emitter
