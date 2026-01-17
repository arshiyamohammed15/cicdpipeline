"""
Replay Bundle Builder for ZeroUI Observability Layer.

OBS-15: Failure Replay Bundle Builder (Deterministic)

Builds replay bundles from trace_id or run_id, including only allowed fields
(fingerprints, IDs, metadata - no raw content). Computes checksum after redaction.
"""

import hashlib
import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..contracts.event_types import EventType
from ..correlation.trace_context import TraceContext
from ..privacy.redaction_enforcer import RedactionEnforcer

logger = logging.getLogger(__name__)


@dataclass
class ReplayBundle:
    """Replay bundle structure per failure.replay.bundle.v1 schema."""

    replay_id: str
    trigger_event_id: str
    included_event_ids: List[str]
    checksum: str
    storage_ref: str
    trace_id: Optional[str] = None
    run_id: Optional[str] = None
    created_at: Optional[datetime] = None


class ReplayBundleBuilder:
    """
    Builds replay bundles from trace_id or run_id.

    Per OBS-15 requirements:
    - Builds bundles referencing trace spans + events (no raw sensitive content)
    - Includes only allowed fields (fingerprints, IDs, metadata)
    - Computes checksum after redaction
    - Emits failure.replay.bundle.v1 event with proper envelope
    """

    def __init__(
        self,
        redaction_enforcer: Optional[RedactionEnforcer] = None,
        event_retriever: Optional[Any] = None,  # Trace/event storage interface
    ):
        """
        Initialize replay bundle builder.

        Args:
            redaction_enforcer: Redaction enforcer for applying privacy policy
            event_retriever: Interface for retrieving events/spans from storage
        """
        self._redaction_enforcer = redaction_enforcer or RedactionEnforcer()
        self._event_retriever = event_retriever

    def build_from_trace_id(
        self,
        trace_id: str,
        trigger_event_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> ReplayBundle:
        """
        Build replay bundle from trace_id.

        Args:
            trace_id: Trace ID to build bundle from
            trigger_event_id: Optional trigger event ID (if not provided, uses first error event)
            tenant_id: Tenant ID for storage path
            component: Component identifier
            channel: Channel identifier

        Returns:
            ReplayBundle with included event IDs and checksum

        Raises:
            ValueError: If trace_id is invalid or no events found
        """
        if not trace_id or len(trace_id) != 32:
            raise ValueError(f"Invalid trace_id: {trace_id}")

        # Retrieve events/spans for this trace
        events = self._retrieve_events_for_trace(trace_id)

        if not events:
            raise ValueError(f"No events found for trace_id: {trace_id}")

        # Find trigger event (first error.captured.v1 or provided trigger)
        if not trigger_event_id:
            trigger_event_id = self._find_trigger_event(events)

        # Filter to included events (all events in trace, or subset)
        included_event_ids = [e.get("event_id") for e in events if e.get("event_id")]

        if not included_event_ids:
            raise ValueError(f"No event IDs found in trace: {trace_id}")

        # Build bundle payload (only allowed fields)
        bundle_payload = self._build_bundle_payload(
            trace_id=trace_id,
            trigger_event_id=trigger_event_id,
            included_event_ids=included_event_ids,
            events=events,
        )

        # Compute checksum after redaction
        checksum = self._compute_checksum(bundle_payload)

        # Generate replay_id
        replay_id = f"replay_{uuid.uuid4().hex[:16]}"

        # Generate storage_ref (will be set by storage layer)
        storage_ref = f"tenant/{tenant_id or 'unknown'}/evidence/data/replay-bundles/dt={datetime.now(timezone.utc).strftime('%Y-%m-%d')}/{replay_id}.jsonl"

        return ReplayBundle(
            replay_id=replay_id,
            trigger_event_id=trigger_event_id,
            included_event_ids=included_event_ids,
            checksum=checksum,
            storage_ref=storage_ref,
            trace_id=trace_id,
            created_at=datetime.now(timezone.utc),
        )

    def build_from_run_id(
        self,
        run_id: str,
        trigger_event_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> ReplayBundle:
        """
        Build replay bundle from run_id.

        Args:
            run_id: Run ID to build bundle from
            trigger_event_id: Optional trigger event ID
            tenant_id: Tenant ID for storage path
            component: Component identifier
            channel: Channel identifier

        Returns:
            ReplayBundle with included event IDs and checksum

        Raises:
            ValueError: If run_id is invalid or no events found
        """
        if not run_id:
            raise ValueError("run_id is required")

        # Retrieve events for this run_id
        events = self._retrieve_events_for_run(run_id)

        if not events:
            raise ValueError(f"No events found for run_id: {run_id}")

        # Extract trace_id from first event
        trace_id = events[0].get("correlation", {}).get("trace_id") if events else None

        # Find trigger event
        if not trigger_event_id:
            trigger_event_id = self._find_trigger_event(events)

        # Filter to included events
        included_event_ids = [e.get("event_id") for e in events if e.get("event_id")]

        if not included_event_ids:
            raise ValueError(f"No event IDs found in run: {run_id}")

        # Build bundle payload
        bundle_payload = self._build_bundle_payload(
            trace_id=trace_id,
            trigger_event_id=trigger_event_id,
            included_event_ids=included_event_ids,
            events=events,
            run_id=run_id,
        )

        # Compute checksum
        checksum = self._compute_checksum(bundle_payload)

        # Generate replay_id
        replay_id = f"replay_{uuid.uuid4().hex[:16]}"

        # Generate storage_ref
        storage_ref = f"tenant/{tenant_id or 'unknown'}/evidence/data/replay-bundles/dt={datetime.now(timezone.utc).strftime('%Y-%m-%d')}/{replay_id}.jsonl"

        return ReplayBundle(
            replay_id=replay_id,
            trigger_event_id=trigger_event_id,
            included_event_ids=included_event_ids,
            checksum=checksum,
            storage_ref=storage_ref,
            trace_id=trace_id,
            run_id=run_id,
            created_at=datetime.now(timezone.utc),
        )

    def _retrieve_events_for_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve events for a trace_id.

        Args:
            trace_id: Trace ID

        Returns:
            List of event dictionaries (with correlation.trace_id matching)
        """
        if self._event_retriever:
            try:
                return self._event_retriever.get_events_by_trace_id(trace_id)
            except Exception as e:
                logger.error(f"Failed to retrieve events for trace {trace_id}: {e}")

        # Fallback: return empty list (will be populated by storage layer)
        logger.warning(f"Event retriever not available, returning empty events for trace {trace_id}")
        return []

    def _retrieve_events_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve events for a run_id.

        Args:
            run_id: Run ID

        Returns:
            List of event dictionaries (with correlation.request_id or session_id matching)
        """
        if self._event_retriever:
            try:
                return self._event_retriever.get_events_by_run_id(run_id)
            except Exception as e:
                logger.error(f"Failed to retrieve events for run {run_id}: {e}")

        # Fallback: return empty list
        logger.warning(f"Event retriever not available, returning empty events for run {run_id}")
        return []

    def _find_trigger_event(self, events: List[Dict[str, Any]]) -> str:
        """
        Find trigger event (first error.captured.v1 or first event).

        Args:
            events: List of events

        Returns:
            Event ID of trigger event
        """
        # Look for error.captured.v1 first
        for event in events:
            event_type = event.get("event_type")
            if event_type == EventType.ERROR_CAPTURED.value:
                event_id = event.get("event_id")
                if event_id:
                    return event_id

        # Fallback to first event
        if events:
            event_id = events[0].get("event_id")
            if event_id:
                return event_id

        raise ValueError("No trigger event found")

    def _build_bundle_payload(
        self,
        trace_id: Optional[str],
        trigger_event_id: str,
        included_event_ids: List[str],
        events: List[Dict[str, Any]],
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build bundle payload with only allowed fields.

        Per PRD: only fingerprints, IDs, metadata - no raw content.

        Args:
            trace_id: Trace ID
            trigger_event_id: Trigger event ID
            included_event_ids: List of included event IDs
            events: List of event dictionaries
            run_id: Optional run ID

        Returns:
            Bundle payload dictionary (redacted, only allowed fields)
        """
        # Extract allowed metadata from events
        event_metadata = []
        for event in events:
            event_id = event.get("event_id")
            if not event_id or event_id not in included_event_ids:
                continue

            # Extract only allowed fields
            metadata = {
                "event_id": event_id,
                "event_type": event.get("event_type"),
                "event_time": event.get("event_time"),
                "severity": event.get("severity"),
                "source": {
                    "component": event.get("source", {}).get("component"),
                    "channel": event.get("source", {}).get("channel"),
                },
                "correlation": {
                    "trace_id": event.get("correlation", {}).get("trace_id"),
                    "span_id": event.get("correlation", {}).get("span_id"),
                },
            }

            # Extract fingerprints from payload (if present)
            payload = event.get("payload", {})
            fingerprints = {}
            for key in payload.keys():
                if key.endswith("_fingerprint"):
                    fingerprints[key] = payload[key]

            if fingerprints:
                metadata["fingerprints"] = fingerprints

            event_metadata.append(metadata)

        # Build bundle payload
        bundle_payload = {
            "trace_id": trace_id,
            "run_id": run_id,
            "trigger_event_id": trigger_event_id,
            "included_event_ids": included_event_ids,
            "event_count": len(included_event_ids),
            "events": event_metadata,
        }

        # Apply redaction
        redaction_result = self._redaction_enforcer.enforce(bundle_payload, compute_fingerprints=False)

        return redaction_result.redacted_payload

    def _compute_checksum(self, payload: Dict[str, Any]) -> str:
        """
        Compute SHA-256 checksum of payload.

        Args:
            payload: Payload dictionary

        Returns:
            Hex-encoded SHA-256 hash (64 characters)
        """
        # Serialize to JSON (canonical form)
        json_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()

    def to_event_payload(self, bundle: ReplayBundle, bundle_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert replay bundle to failure.replay.bundle.v1 event payload.

        Args:
            bundle: ReplayBundle instance
            bundle_payload: Bundle payload dictionary

        Returns:
            Event payload dictionary per failure.replay.bundle.v1 schema
        """
        return {
            "replay_id": bundle.replay_id,
            "trigger_event_id": bundle.trigger_event_id,
            "included_event_ids": bundle.included_event_ids,
            "checksum": bundle.checksum,
            "storage_ref": bundle.storage_ref,
        }

    async def build_and_emit(
        self,
        trace_id: str,
        event_emitter: Optional[Any] = None,  # EventEmitter from instrumentation
        tenant_id: Optional[str] = None,
        component: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> ReplayBundle:
        """
        Build replay bundle and emit failure.replay.bundle.v1 event.

        Args:
            trace_id: Trace ID to build bundle from
            event_emitter: Optional EventEmitter instance
            tenant_id: Tenant ID for storage path
            component: Component identifier
            channel: Channel identifier

        Returns:
            ReplayBundle instance
        """
        # Build bundle
        bundle = self.build_from_trace_id(
            trace_id,
            tenant_id=tenant_id,
            component=component,
            channel=channel,
        )

        # Build bundle payload
        events = self._retrieve_events_for_trace(trace_id)
        bundle_payload = self._build_bundle_payload(
            trace_id=trace_id,
            trigger_event_id=bundle.trigger_event_id,
            included_event_ids=bundle.included_event_ids,
            events=events,
        )

        # Emit event if emitter available
        if event_emitter:
            try:
                from ..instrumentation.python.instrumentation import EventEmitter
                from ..contracts.event_types import EventType

                event_payload = self.to_event_payload(bundle, bundle_payload)
                await event_emitter.emit_event(
                    event_type=EventType.FAILURE_REPLAY_BUNDLE,
                    payload=event_payload,
                    severity="info",
                )
                logger.info(f"Emitted failure.replay.bundle.v1 event for replay_id: {bundle.replay_id}")
            except Exception as e:
                logger.error(f"Failed to emit failure.replay.bundle.v1 event: {e}")

        return bundle
