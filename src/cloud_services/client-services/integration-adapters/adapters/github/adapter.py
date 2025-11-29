"""
GitHub adapter implementation.

What: GitHub-specific adapter implementing BaseAdapter interface
Why: Handle GitHub webhooks, polling, and outbound actions
Reads/Writes: GitHub API via HTTP
Contracts: PRD FR-4, FR-5, FR-7 (Webhooks, Polling, Outbound Actions)
Risks: GitHub API changes, rate limits, authentication failures
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from ..base import BaseAdapter
from ..http_client import HTTPClient, ErrorType
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
from .webhook_verifier import GitHubWebhookVerifier


class GitHubAdapter(BaseAdapter):
    """GitHub adapter implementation."""

    def __init__(
        self,
        provider_id: str,
        connection_id: UUID,
        tenant_id: str,
        api_token: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        """
        Initialize GitHub adapter.
        
        Args:
            provider_id: Provider identifier ("github")
            connection_id: Connection ID
            tenant_id: Tenant ID
            api_token: GitHub API token (from KMS)
            webhook_secret: Webhook signing secret (from KMS)
        """
        super().__init__(provider_id, connection_id, tenant_id)
        self.api_token = api_token
        self.webhook_secret = webhook_secret
        self.client = HTTPClient(base_url="https://api.github.com")
        self.verifier = GitHubWebhookVerifier()
        self.circuit_breaker = get_circuit_breaker_manager().get_breaker(connection_id)

    def process_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Process GitHub webhook.
        
        Args:
            payload: Webhook payload
            headers: HTTP headers
            
        Returns:
            Event data ready for SignalEnvelope transformation
            
        Raises:
            ValueError: If signature is invalid
        """
        # Verify signature
        if self.webhook_secret:
            signature = self.verifier.extract_signature(headers)
            if signature:
                payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
                if not self.verifier.verify_signature(
                    payload_bytes, signature, self.webhook_secret
                ):
                    raise ValueError("Invalid webhook signature")
        
        # Extract event type from headers
        event_type = headers.get("X-GitHub-Event") or headers.get("x-github-event")
        if not event_type:
            raise ValueError("Missing X-GitHub-Event header")
        
        # Return event data
        return {
            "event_type": event_type,
            "payload": payload,
            "action": payload.get("action"),  # For pull_request, issues, etc.
        }

    def poll_events(
        self, cursor: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Poll GitHub API for events.
        
        Note: GitHub doesn't have a generic events API, so this would need
        to be implemented per resource type (issues, PRs, etc.).
        
        Args:
            cursor: Optional cursor (e.g., last event ID or timestamp)
            
        Returns:
            Tuple of (events, new_cursor)
        """
        # GitHub doesn't have a generic events polling API
        # This would need to be implemented per use case
        # For now, return empty list
        return [], cursor

    def execute_action(
        self, action: NormalisedActionCreate
    ) -> NormalisedActionResponse:
        """
        Execute outbound action on GitHub.
        
        Args:
            action: Normalised action to execute
            
        Returns:
            NormalisedActionResponse with execution result
        """
        # Route to appropriate action handler
        if action.canonical_type == "comment_on_pr":
            return self._comment_on_pr(action)
        elif action.canonical_type == "create_issue":
            return self._create_issue(action)
        elif action.canonical_type == "create_issue_comment":
            return self._create_issue_comment(action)
        else:
            raise ValueError(f"Unsupported action type: {action.canonical_type}")

    def _comment_on_pr(self, action: NormalisedActionCreate) -> NormalisedActionResponse:
        """Comment on a pull request."""
        repo = action.target.get("repository")
        pr_number = action.target.get("pr_number") or action.target.get("pr_id")
        body = action.payload.get("body") or action.payload.get("comment")
        
        if not repo or not pr_number or not body:
            raise ValueError("Missing required fields: repository, pr_number, body")
        
        # Make API call with circuit breaker
        def make_request():
            headers = {
                "Authorization": f"token {self.api_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = self.client.request(
                "POST",
                f"/repos/{repo}/issues/{pr_number}/comments",
                headers=headers,
                json={"body": body},
                idempotency_key=action.idempotency_key,
            )
            response.raise_for_status()
            return response.json()
        
        try:
            result = self.circuit_breaker.call(make_request)
            comment_id = result.get("id")
            comment_url = result.get("html_url")
            
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"comment_id": comment_id, "comment_url": comment_url},
                idempotency_key=action.idempotency_key,
                correlation_id=action.correlation_id,
                status=ActionStatus.COMPLETED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
        except Exception as e:
            # Return failed response
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"error": str(e)},
                idempotency_key=action.idempotency_key,
                correlation_id=action.correlation_id,
                status=ActionStatus.FAILED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    def _create_issue(self, action: NormalisedActionCreate) -> NormalisedActionResponse:
        """Create a GitHub issue."""
        repo = action.target.get("repository")
        title = action.payload.get("title")
        body = action.payload.get("body") or action.payload.get("description")
        
        if not repo or not title:
            raise ValueError("Missing required fields: repository, title")
        
        def make_request():
            headers = {
                "Authorization": f"token {self.api_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = self.client.request(
                "POST",
                f"/repos/{repo}/issues",
                headers=headers,
                json={"title": title, "body": body},
                idempotency_key=action.idempotency_key,
            )
            response.raise_for_status()
            return response.json()
        
        try:
            result = self.circuit_breaker.call(make_request)
            issue_number = result.get("number")
            issue_url = result.get("html_url")
            
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"issue_number": issue_number, "issue_url": issue_url},
                idempotency_key=action.idempotency_key,
                correlation_id=action.correlation_id,
                status=ActionStatus.COMPLETED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
        except Exception as e:
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"error": str(e)},
                idempotency_key=action.idempotency_key,
                correlation_id=action.correlation_id,
                status=ActionStatus.FAILED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    def _create_issue_comment(self, action: NormalisedActionCreate) -> NormalisedActionResponse:
        """Create a comment on a GitHub issue."""
        repo = action.target.get("repository")
        issue_number = action.target.get("issue_number") or action.target.get("issue_id")
        body = action.payload.get("body") or action.payload.get("comment")
        
        if not repo or not issue_number or not body:
            raise ValueError("Missing required fields: repository, issue_number, body")
        
        def make_request():
            headers = {
                "Authorization": f"token {self.api_token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = self.client.request(
                "POST",
                f"/repos/{repo}/issues/{issue_number}/comments",
                headers=headers,
                json={"body": body},
                idempotency_key=action.idempotency_key,
            )
            response.raise_for_status()
            return response.json()
        
        try:
            result = self.circuit_breaker.call(make_request)
            comment_id = result.get("id")
            comment_url = result.get("html_url")
            
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"comment_id": comment_id, "comment_url": comment_url},
                idempotency_key=action.idempotency_key,
                correlation_id=action.correlation_id,
                status=ActionStatus.COMPLETED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
        except Exception as e:
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"error": str(e)},
                idempotency_key=action.idempotency_key,
                correlation_id=action.correlation_id,
                status=ActionStatus.FAILED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

    def verify_connection(self) -> bool:
        """
        Verify GitHub connection (test API call).
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            def make_request():
                headers = {
                    "Authorization": f"token {self.api_token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                response = self.client.request("GET", "/user", headers=headers)
                response.raise_for_status()
                return response.json()
            
            self.circuit_breaker.call(make_request)
            return True
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get GitHub adapter capabilities.
        
        Returns:
            Capability flags
        """
        return {
            "webhook_supported": True,
            "polling_supported": False,  # GitHub doesn't have generic polling API
            "outbound_actions_supported": True,
        }

    @staticmethod
    def get_default_capabilities() -> Dict[str, bool]:
        """Get default capabilities for GitHub adapter."""
        return {
            "webhook_supported": True,
            "polling_supported": False,
            "outbound_actions_supported": True,
        }

