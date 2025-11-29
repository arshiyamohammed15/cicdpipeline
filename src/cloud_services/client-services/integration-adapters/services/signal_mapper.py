"""
SignalEnvelope mapping service for Integration Adapters Module.

What: Transforms provider-specific events into canonical SignalEnvelope format per PRD Section 10.1
Why: Normalize provider events to PM-3 canonical format
Reads/Writes: Provider events → SignalEnvelope
Contracts: PRD Section 10.1 (Event Mapping to SignalEnvelope)
Risks: Mapping errors, missing fields, incorrect canonical types
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

# Import SignalEnvelope from PM-3
try:
    from signal_ingestion_normalization.models import (
        SignalEnvelope,
        Resource,
        SignalKind,
        Environment,
    )
except ImportError:
    # Fallback: Define minimal structures if PM-3 not available
    from enum import Enum
    from pydantic import BaseModel, Field
    
    class SignalKind(str, Enum):
        EVENT = "event"
        METRIC = "metric"
        LOG = "log"
        TRACE = "trace"
    
    class Environment(str, Enum):
        DEV = "dev"
        STAGE = "stage"
        PROD = "prod"
    
    class Resource(BaseModel):
        service_name: Optional[str] = None
        repository: Optional[str] = None
        branch: Optional[str] = None
        commit: Optional[str] = None
        module: Optional[str] = None
        file_path: Optional[str] = None
        pr_id: Optional[int] = None
        environment: Optional[str] = None
        deployment_id: Optional[str] = None
    
    class SignalEnvelope(BaseModel):
        signal_id: str
        tenant_id: str
        environment: Environment
        producer_id: str
        actor_id: Optional[str] = None
        signal_kind: SignalKind
        signal_type: str
        occurred_at: datetime
        ingested_at: datetime
        trace_id: Optional[str] = None
        span_id: Optional[str] = None
        correlation_id: Optional[str] = None
        resource: Optional[Resource] = None
        payload: Dict[str, Any]
        schema_version: str
        sequence_no: Optional[int] = None


class SignalMapper:
    """
    Maps provider-specific events to SignalEnvelope format per PRD Section 10.1.
    
    Mapping rules:
    - provider_id → payload.provider_metadata.provider_id
    - connection_id → producer_id
    - provider event type → canonical signal_type
    - provider event timestamp → occurred_at
    - adapter processing time → ingested_at
    - canonical entity IDs → resource fields or payload.canonical_keys
    """

    def __init__(self, environment: Environment = Environment.PROD):
        """Initialize signal mapper."""
        self.environment = environment
        self.schema_version = "1.0.0"

    def map_provider_event_to_signal_envelope(
        self,
        provider_id: str,
        connection_id: str,
        tenant_id: str,
        provider_event: Dict[str, Any],
        provider_event_type: str,
        occurred_at: datetime,
        correlation_id: Optional[str] = None,
    ) -> SignalEnvelope:
        """
        Map provider-specific event to SignalEnvelope format.
        
        Args:
            provider_id: Provider identifier (e.g., "github", "jira")
            connection_id: Integration connection ID
            tenant_id: Tenant ID
            provider_event: Provider-specific event payload
            provider_event_type: Provider event type (e.g., "pull_request.opened")
            occurred_at: When event occurred in provider system
            correlation_id: Optional correlation ID from provider event
            
        Returns:
            SignalEnvelope: Canonical signal envelope
        """
        # Generate signal ID
        signal_id = str(uuid.uuid4())
        
        # Map provider event type to canonical signal_type
        canonical_signal_type = self._map_event_type_to_canonical(provider_id, provider_event_type)
        
        # Extract resource context from provider event
        resource = self._extract_resource_context(provider_id, provider_event)
        
        # Build payload with provider metadata
        payload = self._build_payload(provider_id, connection_id, provider_event, canonical_signal_type)
        
        # Create SignalEnvelope
        signal_envelope = SignalEnvelope(
            signal_id=signal_id,
            tenant_id=tenant_id,
            environment=self.environment,
            producer_id=connection_id,  # Adapter acts as producer for PM-3
            signal_kind=SignalKind.EVENT,
            signal_type=canonical_signal_type,
            occurred_at=occurred_at,
            ingested_at=datetime.utcnow(),
            correlation_id=correlation_id or provider_event.get("id"),
            resource=resource,
            payload=payload,
            schema_version=self.schema_version,
        )
        
        return signal_envelope

    def _map_event_type_to_canonical(self, provider_id: str, provider_event_type: str) -> str:
        """
        Map provider event type to canonical signal_type.
        
        Examples:
        - github.pull_request.opened → pr_opened
        - jira.issue.created → issue_created
        - slack.message.posted → chat_message
        """
        # Common mappings (check full event type first, then without provider prefix)
        mappings = {
            # GitHub
            "pull_request.opened": "pr_opened",
            "pull_request.closed": "pr_closed",
            "pull_request.merged": "pr_merged",
            "pull_request.review_requested": "pr_review_requested",
            "push": "push",
            "issues.opened": "issue_created",
            "issues.closed": "issue_closed",
            # Jira
            "issue.created": "issue_created",
            "issue.updated": "issue_updated",
            "issue.commented": "issue_commented",
            # Slack
            "message.posted": "chat_message",
            # Generic
            "event": "event",
        }
        
        # Try direct mapping first (full event type)
        if provider_event_type in mappings:
            return mappings[provider_event_type]
        
        # Remove provider prefix if present and try again
        event_type = provider_event_type
        if "." in event_type:
            event_type = event_type.split(".", 1)[-1]
            if event_type in mappings:
                return mappings[event_type]
        
        # Try provider-specific mapping
        provider_mappings = {
            "github": {
                "pull_request": "pr_opened",
                "push": "push",
                "issues": "issue_created",
            },
            "jira": {
                "issue": "issue_created",
            },
            "slack": {
                "message": "chat_message",
            },
        }
        
        if provider_id in provider_mappings:
            for prefix, canonical in provider_mappings[provider_id].items():
                if prefix in event_type.lower():
                    return canonical
        
        # Default: use event type as-is (normalized)
        return event_type.replace(".", "_").replace("-", "_")

    def _extract_resource_context(self, provider_id: str, provider_event: Dict[str, Any]) -> Optional[Resource]:
        """
        Extract resource context from provider event.
        
        Maps to Resource model fields:
        - repository → resource.repository
        - branch → resource.branch
        - pr_id → resource.pr_id
        """
        resource_data = {}
        
        # GitHub/GitLab: Extract repository context
        if provider_id in ["github", "gitlab"]:
            if "repository" in provider_event:
                repo = provider_event["repository"]
                if isinstance(repo, dict):
                    if "full_name" in repo:
                        resource_data["repository"] = repo["full_name"]
                    elif "name" in repo and "owner" in repo:
                        owner = repo["owner"]
                        owner_name = owner.get("login") if isinstance(owner, dict) else str(owner)
                        resource_data["repository"] = f"{owner_name}/{repo['name']}"
            
            # Extract branch
            if "ref" in provider_event:
                resource_data["branch"] = provider_event["ref"]
            elif "pull_request" in provider_event:
                pr = provider_event["pull_request"]
                if isinstance(pr, dict) and "head" in pr:
                    head = pr["head"]
                    if isinstance(head, dict) and "ref" in head:
                        resource_data["branch"] = head["ref"]
            
            # Extract PR ID
            if "pull_request" in provider_event:
                pr = provider_event["pull_request"]
                if isinstance(pr, dict) and "number" in pr:
                    resource_data["pr_id"] = pr["number"]
            elif "number" in provider_event:
                resource_data["pr_id"] = provider_event["number"]
        
        # Jira: Extract issue context
        elif provider_id == "jira":
            if "issue" in provider_event:
                issue = provider_event["issue"]
                if isinstance(issue, dict):
                    # Store issue key in canonical_keys instead
                    pass
        
        if not resource_data:
            return None
        
        return Resource(**resource_data)

    def _build_payload(
        self,
        provider_id: str,
        connection_id: str,
        provider_event: Dict[str, Any],
        canonical_signal_type: str,
    ) -> Dict[str, Any]:
        """
        Build SignalEnvelope payload with provider metadata and canonical fields.
        
        Structure:
        - payload.provider_metadata.provider_id
        - payload.provider_metadata.connection_id
        - payload.canonical_keys (for entity IDs like issue_key, channel_id)
        - payload.{canonical_fields} (provider event data normalized)
        """
        payload: Dict[str, Any] = {}
        
        # Add provider metadata
        payload["provider_metadata"] = {
            "provider_id": provider_id,
            "connection_id": connection_id,
        }
        
        # Extract canonical keys
        canonical_keys = {}
        
        # GitHub/GitLab: Extract PR/issue numbers
        if provider_id in ["github", "gitlab"]:
            if "pull_request" in provider_event:
                pr = provider_event["pull_request"]
                if isinstance(pr, dict):
                    if "number" in pr:
                        payload["pr_number"] = pr["number"]
                    if "title" in pr:
                        payload["title"] = pr["title"]
                    if "state" in pr:
                        payload["state"] = pr["state"]
            elif "issue" in provider_event:
                issue = provider_event["issue"]
                if isinstance(issue, dict):
                    if "number" in issue:
                        payload["issue_number"] = issue["number"]
                    if "title" in issue:
                        payload["title"] = issue["title"]
        
        # Jira: Extract issue key
        elif provider_id == "jira":
            if "issue" in provider_event:
                issue = provider_event["issue"]
                if isinstance(issue, dict) and "key" in issue:
                    canonical_keys["issue_key"] = issue["key"]
                    payload["issue_key"] = issue["key"]
                if isinstance(issue, dict) and "fields" in issue:
                    fields = issue["fields"]
                    if isinstance(fields, dict):
                        if "summary" in fields:
                            payload["summary"] = fields["summary"]
        
        # Slack: Extract channel ID
        elif provider_id == "slack":
            if "channel" in provider_event:
                channel = provider_event["channel"]
                if isinstance(channel, dict) and "id" in channel:
                    canonical_keys["channel_id"] = channel["id"]
                elif isinstance(channel, str):
                    canonical_keys["channel_id"] = channel
        
        # Add canonical keys if any
        if canonical_keys:
            payload["canonical_keys"] = canonical_keys
        
        # Copy other relevant fields from provider event (normalized)
        # Exclude sensitive fields and large nested objects
        excluded_fields = {"repository", "sender", "user", "actor", "installation"}
        for key, value in provider_event.items():
            if key not in excluded_fields and not isinstance(value, dict):
                if key not in payload:
                    payload[key] = value
        
        return payload

