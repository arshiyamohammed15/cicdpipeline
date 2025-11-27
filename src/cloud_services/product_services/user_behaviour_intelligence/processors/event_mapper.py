"""
Event Mapping & Transformation for UBI Module (EPC-9).

What: Maps PM-3 SignalEnvelope to UBI BehaviouralEvent
Why: Transform external signal format to internal representation per PRD Section 10.1
Reads/Writes: Event transformation (no storage)
Contracts: UBI PRD FR-1, Section 10.1
Risks: Mapping failures, data loss during transformation
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..models import BehaviouralEvent, ActorType

logger = logging.getLogger(__name__)


class EventMapper:
    """
    Event mapper for transforming PM-3 SignalEnvelope to UBI BehaviouralEvent.

    Per UBI PRD FR-1 and Section 10.1:
    - Map occurred_at → timestamp_utc
    - Map payload → properties
    - Map signal_type → event_type (canonical taxonomy)
    - Extract actor_type from resource or payload
    - Extract privacy_tags from resource or payload
    """

    # Event type taxonomy mapping (PM-3 signal_type → UBI canonical event_type)
    EVENT_TYPE_MAPPING: Dict[str, str] = {
        # File operations
        "file_edited": "file_edited",
        "file_created": "file_created",
        "file_deleted": "file_deleted",
        # Build/test operations
        "build_failed": "build_failed",
        "build_succeeded": "build_succeeded",
        "test_failed": "test_failed",
        "test_passed": "test_passed",
        # PR operations
        "pr_opened": "pr_created",
        "pr_created": "pr_created",
        "pr_merged": "pr_merged",
        "pr_closed": "pr_closed",
        "pr_reviewed": "pr_reviewed",
        # Commit operations
        "commit_created": "commit_created",
        "commit_pushed": "commit_pushed",
        # LLM operations
        "llm_request_submitted": "llm_request_submitted",
        "llm_request_completed": "llm_request_completed",
        "llm_request_failed": "llm_request_failed",
        # Context/focus operations
        "context_switch": "context_switch",
        "focus_session_started": "focus_session_started",
        "focus_session_ended": "focus_session_ended",
        # Gate/policy operations
        "gate_evaluated": "gate_evaluated",
        "policy_violation": "policy_violation",
        "override_attempted": "override_attempted",
    }

    def __init__(self):
        """Initialize event mapper."""
        pass

    def map_signal_envelope(self, signal_envelope: Dict[str, Any]) -> Optional[BehaviouralEvent]:
        """
        Map PM-3 SignalEnvelope to UBI BehaviouralEvent.

        Args:
            signal_envelope: SignalEnvelope dictionary from PM-3

        Returns:
            BehaviouralEvent or None if mapping fails
        """
        try:
            # Extract required fields
            signal_id = signal_envelope.get("signal_id")
            tenant_id = signal_envelope.get("tenant_id")
            actor_id = signal_envelope.get("actor_id")
            signal_type = signal_envelope.get("signal_type")
            occurred_at = signal_envelope.get("occurred_at")
            ingested_at = signal_envelope.get("ingested_at")
            payload = signal_envelope.get("payload", {})
            resource = signal_envelope.get("resource", {})
            schema_version = signal_envelope.get("schema_version", "1.0.0")
            
            if not signal_id or not tenant_id or not occurred_at:
                logger.error("Missing required fields in SignalEnvelope")
                return None
            
            # Map fields per PRD Section 10.1
            event_id = signal_id  # event_id mapped from signal_id
            timestamp_utc = occurred_at  # occurred_at → timestamp_utc
            properties = payload if isinstance(payload, dict) else {}  # payload → properties
            
            # Map signal_type to canonical event_type
            event_type = self._map_event_type(signal_type)
            if not event_type:
                logger.warning(f"Unknown signal_type: {signal_type}, using as-is")
                event_type = signal_type
            
            # Extract actor_type
            actor_type = self._extract_actor_type(resource, payload)
            
            # Extract source_system
            source_system = self._extract_source_system(resource, signal_envelope)
            
            # Extract privacy_tags
            privacy_tags = self._extract_privacy_tags(resource, payload)
            
            # Extract trace/span/correlation IDs
            trace_id = signal_envelope.get("trace_id")
            span_id = signal_envelope.get("span_id")
            correlation_id = signal_envelope.get("correlation_id")
            
            return BehaviouralEvent(
                event_id=event_id,
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type=actor_type,
                source_system=source_system,
                event_type=event_type,
                timestamp_utc=timestamp_utc,
                ingested_at=ingested_at or timestamp_utc,
                properties=properties,
                privacy_tags=privacy_tags,
                schema_version=schema_version,
                trace_id=trace_id,
                span_id=span_id,
                correlation_id=correlation_id,
                resource=resource if isinstance(resource, dict) else {}
            )
        except Exception as e:
            logger.error(f"Error mapping SignalEnvelope: {e}", exc_info=True)
            return None

    def _map_event_type(self, signal_type: Optional[str]) -> Optional[str]:
        """
        Map PM-3 signal_type to UBI canonical event_type.

        Args:
            signal_type: PM-3 signal_type

        Returns:
            UBI canonical event_type or None if not mappable
        """
        if not signal_type:
            return None
        
        return self.EVENT_TYPE_MAPPING.get(signal_type, signal_type)

    def _extract_actor_type(
        self,
        resource: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> ActorType:
        """
        Extract actor_type from resource or payload.

        Args:
            resource: Resource metadata
            payload: Event payload

        Returns:
            ActorType enum value
        """
        # Try resource first
        if isinstance(resource, dict):
            actor_type = resource.get("actor_type") or resource.get("actorType")
            if actor_type:
                return self._normalize_actor_type(actor_type)
        
        # Try payload
        if isinstance(payload, dict):
            actor_type = payload.get("actor_type") or payload.get("actorType")
            if actor_type:
                return self._normalize_actor_type(actor_type)
        
        # Default to human
        return ActorType.HUMAN

    def _normalize_actor_type(self, actor_type: str) -> ActorType:
        """
        Normalize actor_type string to ActorType enum.

        Args:
            actor_type: Actor type string

        Returns:
            ActorType enum value
        """
        actor_type_lower = actor_type.lower()
        if actor_type_lower in ["human", "person", "user"]:
            return ActorType.HUMAN
        elif actor_type_lower in ["ai_agent", "ai", "agent", "llm"]:
            return ActorType.AI_AGENT
        elif actor_type_lower in ["service", "system", "automated"]:
            return ActorType.SERVICE
        else:
            # Default to human if unknown
            logger.warning(f"Unknown actor_type: {actor_type}, defaulting to human")
            return ActorType.HUMAN

    def _extract_source_system(
        self,
        resource: Dict[str, Any],
        signal_envelope: Dict[str, Any]
    ) -> Optional[str]:
        """
        Extract source_system from resource or producer_id.

        Args:
            resource: Resource metadata
            signal_envelope: Full SignalEnvelope

        Returns:
            Source system string or None
        """
        # Try resource.service_name
        if isinstance(resource, dict):
            service_name = resource.get("service_name") or resource.get("serviceName")
            if service_name:
                return service_name
        
        # Try producer_id
        producer_id = signal_envelope.get("producer_id")
        if producer_id:
            # Extract service name from producer_id (e.g., "ide-producer" -> "IDE")
            if "ide" in producer_id.lower():
                return "IDE"
            elif "git" in producer_id.lower():
                return "Git"
            elif "ci" in producer_id.lower() or "cicd" in producer_id.lower():
                return "CI"
            elif "llm" in producer_id.lower() or "gateway" in producer_id.lower():
                return "LLM_GATEWAY"
        
        return None

    def _extract_privacy_tags(
        self,
        resource: Dict[str, Any],
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract privacy_tags from resource or payload.

        Args:
            resource: Resource metadata
            payload: Event payload

        Returns:
            Privacy tags dictionary
        """
        privacy_tags = {}
        
        # Try resource.privacy_tags
        if isinstance(resource, dict):
            resource_tags = resource.get("privacy_tags") or resource.get("privacyTags")
            if isinstance(resource_tags, dict):
                privacy_tags.update(resource_tags)
        
        # Try payload.privacy_tags
        if isinstance(payload, dict):
            payload_tags = payload.get("privacy_tags") or payload.get("privacyTags")
            if isinstance(payload_tags, dict):
                privacy_tags.update(payload_tags)
        
        # Default privacy tags based on event content
        if not privacy_tags:
            privacy_tags = {
                "contains_PI": False,
                "contains_code_snippet": False
            }
        
        return privacy_tags

