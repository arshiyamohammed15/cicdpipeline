"""
Jira adapter implementation.

What: Jira-specific adapter implementing BaseAdapter interface (polling-based)
Why: Handle Jira issue events via polling and outbound actions
Reads/Writes: Jira API via HTTP
Contracts: PRD FR-5, FR-7
Risks: Jira API changes, rate limits, authentication failures
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


class JiraAdapter(BaseAdapter):
    """Jira adapter implementation (polling-based)."""

    def __init__(
        self,
        provider_id: str,
        connection_id: UUID,
        tenant_id: str,
        api_token: Optional[str] = None,
        jira_url: Optional[str] = None,
    ):
        """Initialize Jira adapter."""
        super().__init__(provider_id, connection_id, tenant_id)
        self.api_token = api_token
        self.jira_url = jira_url or "https://your-domain.atlassian.net"
        self.client = HTTPClient(base_url=self.jira_url)
        self.circuit_breaker = get_circuit_breaker_manager().get_breaker(connection_id)

    def process_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process Jira webhook (if webhooks are enabled)."""
        # Jira supports webhooks but this adapter is primarily polling-based
        return {
            "event_type": payload.get("webhookEvent", "unknown"),
            "payload": payload,
        }

    def poll_events(
        self, cursor: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Poll Jira API for issue events."""
        try:
            def make_request():
                # Jira JQL query for recent issues
                jql = f"updated >= -1d ORDER BY updated DESC"
                if cursor:
                    jql = f"updated >= '{cursor}' ORDER BY updated DESC"
                
                headers = {
                    "Authorization": f"Basic {self.api_token}",
                    "Accept": "application/json",
                }
                response = self.client.request(
                    "GET",
                    "/rest/api/3/search",
                    headers=headers,
                    params={"jql": jql, "maxResults": 50},
                )
                response.raise_for_status()
                return response.json()
            
            result = self.circuit_breaker.call(make_request)
            issues = result.get("issues", [])
            
            # Transform to events
            events = []
            for issue in issues:
                events.append({
                    "event_type": "issue.updated",
                    "issue": issue,
                })
            
            # Update cursor (use last updated timestamp)
            new_cursor = None
            if issues:
                last_issue = issues[-1]
                new_cursor = last_issue.get("fields", {}).get("updated")
            
            return events, new_cursor
        except Exception:
            return [], cursor

    def execute_action(
        self, action: NormalisedActionCreate
    ) -> NormalisedActionResponse:
        """Execute outbound action on Jira."""
        if action.canonical_type == "create_issue":
            return self._create_issue(action)
        elif action.canonical_type == "add_issue_comment":
            return self._add_comment(action)
        else:
            raise ValueError(f"Unsupported action type: {action.canonical_type}")

    def _create_issue(self, action: NormalisedActionCreate) -> NormalisedActionResponse:
        """Create a Jira issue."""
        from datetime import datetime
        from uuid import uuid4
        
        project_key = action.target.get("project_key")
        summary = action.payload.get("summary") or action.payload.get("title")
        description = action.payload.get("description") or action.payload.get("body")
        
        if not project_key or not summary:
            raise ValueError("Missing required fields: project_key, summary")
        
        def make_request():
            headers = {
                "Authorization": f"Basic {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            response = self.client.request(
                "POST",
                "/rest/api/3/issue",
                headers=headers,
                json={
                    "fields": {
                        "project": {"key": project_key},
                        "summary": summary,
                        "description": description,
                        "issuetype": {"name": "Task"},
                    }
                },
                idempotency_key=action.idempotency_key,
            )
            response.raise_for_status()
            return response.json()
        
        try:
            result = self.circuit_breaker.call(make_request)
            issue_key = result.get("key")
            issue_url = f"{self.jira_url}/browse/{issue_key}"
            
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"issue_key": issue_key, "issue_url": issue_url},
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

    def _add_comment(self, action: NormalisedActionCreate) -> NormalisedActionResponse:
        """Add comment to Jira issue."""
        from datetime import datetime
        from uuid import uuid4
        
        issue_key = action.target.get("issue_key")
        body = action.payload.get("body") or action.payload.get("comment")
        
        if not issue_key or not body:
            raise ValueError("Missing required fields: issue_key, body")
        
        def make_request():
            headers = {
                "Authorization": f"Basic {self.api_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            response = self.client.request(
                "POST",
                f"/rest/api/3/issue/{issue_key}/comment",
                headers=headers,
                json={"body": body},
                idempotency_key=action.idempotency_key,
            )
            response.raise_for_status()
            return response.json()
        
        try:
            result = self.circuit_breaker.call(make_request)
            comment_id = result.get("id")
            
            return NormalisedActionResponse(
                action_id=uuid4(),
                tenant_id=self.tenant_id,
                provider_id=self.provider_id,
                connection_id=self.connection_id,
                canonical_type=action.canonical_type,
                target=action.target,
                payload={"comment_id": comment_id},
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
        """Verify Jira connection."""
        try:
            def make_request():
                headers = {
                    "Authorization": f"Basic {self.api_token}",
                    "Accept": "application/json",
                }
                response = self.client.request("GET", "/rest/api/3/myself", headers=headers)
                response.raise_for_status()
                return response.json()
            
            self.circuit_breaker.call(make_request)
            return True
        except Exception:
            return False

    def get_capabilities(self) -> Dict[str, bool]:
        """Get Jira adapter capabilities."""
        return {
            "webhook_supported": False,  # Primarily polling-based
            "polling_supported": True,
            "outbound_actions_supported": True,
        }

    @staticmethod
    def get_default_capabilities() -> Dict[str, bool]:
        """Get default capabilities for Jira adapter."""
        return {
            "webhook_supported": False,
            "polling_supported": True,
            "outbound_actions_supported": True,
        }

