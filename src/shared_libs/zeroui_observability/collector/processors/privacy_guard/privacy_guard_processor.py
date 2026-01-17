"""
Privacy Guard processor for ZeroUI Observability Layer.

Applies allow/deny rules from Phase 0 redaction policy.
Verifies redaction_applied=true and rejects unsafe payloads.
Emits privacy.audit.v1 events for violations.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ....privacy.redaction_enforcer import RedactionEnforcer, RedactionResult
from ....contracts.event_types import EventType

logger = logging.getLogger(__name__)


@dataclass
class PrivacyCheckResult:
    """Result of privacy check."""

    is_safe: bool
    violation_type: Optional[str] = None
    blocked_fields: Optional[list[str]] = None
    policy_version: Optional[str] = None
    should_emit_audit: bool = False


class PrivacyGuardProcessor:
    """
    Privacy Guard processor for OpenTelemetry Collector.

    Enforces:
    - Allow/deny rules from Phase 0 redaction policy
    - Verification of redaction_applied=true
    - Rejection of unsafe payloads
    - Emission of privacy.audit.v1 events
    """

    def __init__(
        self,
        enabled: bool = True,
        deny_patterns_file: Optional[str] = None,
        reject_on_violation: bool = True,
        emit_audit_events: bool = True,
        policy_version: str = "v1.0",
    ):
        """
        Initialize Privacy Guard processor.

        Args:
            enabled: Whether privacy enforcement is enabled
            deny_patterns_file: Path to deny patterns JSON file
            reject_on_violation: Reject events with violations (default: True)
            emit_audit_events: Emit privacy.audit.v1 events (default: True)
            policy_version: Policy version (default: v1.0)
        """
        self._enabled = enabled
        self._reject_on_violation = reject_on_violation
        self._emit_audit_events = emit_audit_events
        self._policy_version = policy_version

        # Initialize redaction enforcer
        self._redaction_enforcer = RedactionEnforcer(
            use_cccs=False,  # Use basic redaction for collector
            deny_patterns_file=deny_patterns_file,
        )

    def check_privacy(self, event: Dict[str, Any]) -> PrivacyCheckResult:
        """
        Check event for privacy violations.

        Args:
            event: Event dictionary (zero_ui.obsv.event.v1 envelope)

        Returns:
            PrivacyCheckResult with check outcome
        """
        if not self._enabled:
            return PrivacyCheckResult(is_safe=True)

        # Step 1: Check if redaction_applied is set
        payload = event.get("payload", {})
        redaction_applied = payload.get("redaction_applied", False)

        # Step 2: Apply redaction enforcement
        redaction_result = self._redaction_enforcer.enforce(
            payload,
            policy_hint=self._policy_version,
            compute_fingerprints=False,  # Fingerprints already computed in producer
        )

        # Step 3: Check for violations
        violations = []
        blocked_fields = redaction_result.blocked_fields or []
        removed_fields = redaction_result.removed_fields or []

        # Check if deny-listed fields were found
        if blocked_fields:
            violations.append("deny_listed_fields")
        if removed_fields:
            violations.append("removed_fields")

        # Check if redaction was applied but payload still contains sensitive content
        if redaction_applied and (blocked_fields or removed_fields):
            # Redaction was applied but violations still detected - this is a safety net
            violations.append("post_redaction_violation")

        # Step 4: Determine if event is safe
        is_safe = len(violations) == 0

        # Step 5: Determine if we should emit audit event
        should_emit_audit = (
            self._emit_audit_events
            and (not is_safe or not redaction_applied)
        )

        return PrivacyCheckResult(
            is_safe=is_safe,
            violation_type=",".join(violations) if violations else None,
            blocked_fields=blocked_fields,
            policy_version=redaction_result.policy_version,
            should_emit_audit=should_emit_audit,
        )

    def create_audit_event(
        self,
        original_event: Dict[str, Any],
        check_result: PrivacyCheckResult,
    ) -> Dict[str, Any]:
        """
        Create privacy.audit.v1 event for violation.

        Args:
            original_event: Original event that triggered violation
            check_result: Privacy check result

        Returns:
            privacy.audit.v1 event dictionary
        """
        from datetime import datetime
        from ....correlation.trace_context import get_or_create_trace_context

        # Get trace context from original event
        correlation = original_event.get("correlation", {})
        trace_id = correlation.get("trace_id")
        # Create new trace context if not available
        trace_ctx = get_or_create_trace_context(traceparent=None)

        # Create audit event
        audit_event = {
            "event_id": f"audit_{int(datetime.utcnow().timestamp() * 1000)}",
            "event_time": datetime.utcnow().isoformat() + "Z",
            "event_type": EventType.PRIVACY_AUDIT.value,
            "severity": "warn" if check_result.is_safe else "error",
            "source": original_event.get("source", {}),
            "correlation": {
                "trace_id": trace_id or trace_ctx.trace_id,
                "span_id": correlation.get("span_id") or trace_ctx.span_id,
            },
            "payload": {
                "audit_id": f"audit_{int(datetime.utcnow().timestamp() * 1000)}",
                "operation": "telemetry_collection",
                "component": original_event.get("source", {}).get("component", "collector"),
                "channel": original_event.get("source", {}).get("channel", "backend"),
                "encryption_in_transit": True,  # OTLP uses TLS
                "encryption_at_rest": False,  # Depends on storage backend
                "access_control_enforced": True,
                "data_class": "telemetry",
                "violation_type": check_result.violation_type,
                "blocked_fields": check_result.blocked_fields or [],
                "policy_version": check_result.policy_version or self._policy_version,
            },
        }

        return audit_event

    def process_log_record(self, log_record: Dict[str, Any]) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Process OTLP log record (event) for privacy violations.

        Args:
            log_record: OTLP log record containing event data

        Returns:
            Tuple of (should_accept, rejection_reason, audit_event)
        """
        if not self._enabled:
            return True, None, None

        # Extract event from log record body
        body = log_record.get("body", {})
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return False, "invalid_json", None

        # Check privacy
        check_result = self.check_privacy(body)

        # Create audit event if needed
        audit_event = None
        if check_result.should_emit_audit:
            audit_event = self.create_audit_event(body, check_result)

        # Determine if we should accept or reject
        if check_result.is_safe:
            return True, None, audit_event

        # Violation detected
        if self._reject_on_violation:
            return False, check_result.violation_type, audit_event

        # Accept but log violation
        logger.warning(
            f"Privacy violation detected but event accepted: {check_result.violation_type}",
            extra={"blocked_fields": check_result.blocked_fields},
        )
        return True, None, audit_event
