"""
GitLab adapter implementation.

What: GitLab-specific adapter implementing BaseAdapter interface
Why: Handle GitLab webhooks, polling, and outbound actions
Reads/Writes: GitLab API via HTTP
Contracts: PRD FR-4, FR-5, FR-7
Risks: GitLab API changes, rate limits, authentication failures
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from ..base import BaseAdapter
from ..http_client import HTTPClient
try:
    from ...models import NormalisedActionCreate, NormalisedActionResponse, ActionStatus
    from ...reliability.circuit_breaker import get_circuit_breaker_manager
except ImportError:
    # Fallback for direct imports (e.g., in tests)
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))
    from models import NormalisedActionCreate, NormalisedActionResponse, ActionStatus
    from reliability.circuit_breaker import get_circuit_breaker_manager


class GitLabAdapter(BaseAdapter):
    """GitLab adapter implementation."""

    def __init__(
        self,
        provider_id: str,
        connection_id: UUID,
        tenant_id: str,
        api_token: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """Initialize GitLab adapter."""
        super().__init__(provider_id, connection_id, tenant_id)
        self.api_token = api_token
        self.webhook_secret = webhook_secret
        self.client = HTTPClient(base_url="https://gitlab.com/api/v4")
        self.circuit_breaker = get_circuit_breaker_manager().get_breaker(connection_id)

    def process_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process GitLab webhook."""
        # GitLab uses X-Gitlab-Token for webhook verification
        token = headers.get("X-Gitlab-Token") or headers.get("x-gitlab-token")
        if self.webhook_secret and token != self.webhook_secret:
            raise ValueError("Invalid webhook token")
        
        event_type = headers.get("X-Gitlab-Event") or headers.get("x-gitlab-event")
        if not event_type:
            raise ValueError("Missing X-Gitlab-Event header")
        
        return {
            "event_type": event_type,
            "payload": payload,
        }

    def poll_events(
        self, cursor: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Poll GitLab API for events."""
        # GitLab doesn't have a generic events API
        return [], cursor

    def execute_action(
        self, action: NormalisedActionCreate
    ) -> NormalisedActionResponse:
        """Execute outbound action on GitLab."""
        from datetime import datetime
        from uuid import uuid4
        
        # GitLab actions would be similar to GitHub
        # For now, return a basic response structure
        # Full implementation would require GitLab API-specific logic
        if action.canonical_type == "comment_on_merge_request":
            # Placeholder - would implement GitLab MR comment
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"status": "not_implemented"},
                idempotency_key=action.idempotency_key,
                correlation_id=action.correlation_id,
                status=ActionStatus.FAILED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        else:
            raise ValueError(f"Unsupported action type: {action.canonical_type}")

    def verify_connection(self) -> bool:
        """Verify GitLab connection."""
        try:
            def make_request():
                headers = {"PRIVATE-TOKEN": self.api_token}
                response = self.client.request("GET", "/user", headers=headers)
                response.raise_for_status()
                return response.json()
            
            self.circuit_breaker.call(make_request)
            return True
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, bool]:
        """Get GitLab adapter capabilities."""
        return {
            "webhook_supported": True,
            "polling_supported": False,
            "outbound_actions_supported": True,
        }

    @staticmethod
    def get_default_capabilities() -> Dict[str, bool]:
        """Get default capabilities for GitLab adapter."""
        return {
            "webhook_supported": True,
            "polling_supported": False,
            "outbound_actions_supported": True,
        }

