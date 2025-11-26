"""Automation service for triggering remediation workflows."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None

from sqlmodel.ext.asyncio.session import AsyncSession

from ..database.models import Alert
from ..observability.metrics import AUTOMATION_EXECUTIONS
from ..repositories import AlertRepository
from .evidence_service import EvidenceService


class AutomationService:
    """Service for triggering automated remediation workflows."""

    def __init__(self, session: AsyncSession, evidence_service: Optional[EvidenceService] = None):
        self.session = session
        self.alert_repo = AlertRepository(session)
        self.evidence = evidence_service or EvidenceService()

    async def trigger_automation_hooks(self, alert: Alert) -> List[Dict[str, Any]]:
        """
        Trigger automation hooks for an alert.
        
        Args:
            alert: Alert with automation_hooks
        
        Returns:
            List of automation execution results
        """
        if not alert.automation_hooks:
            return []

        results = []
        for hook_url in alert.automation_hooks:
            try:
                result = await self._execute_hook(hook_url, alert)
                results.append(result)
            except Exception as e:
                results.append(
                    {
                        "hook_url": hook_url,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )

        for result in results:
            AUTOMATION_EXECUTIONS.labels(status=result.get("status", "unknown")).inc()

        await self.evidence.record_event(
            event_type="automation_triggered",
            tenant_id=alert.tenant_id,
            actor=None,
            alert_id=alert.alert_id,
            metadata={"hooks": alert.automation_hooks, "results": results},
        )

        return results

    async def _execute_hook(self, hook_url: str, alert: Alert) -> Dict[str, Any]:
        """
        Execute a single automation hook.
        
        Args:
            hook_url: URL or identifier for the automation hook
            alert: Alert to pass to the hook
        
        Returns:
            Execution result
        """
        # For now, this is a stub implementation
        # In production, this would:
        # 1. Call the automation service/workflow engine
        # 2. Pass alert context
        # 3. Wait for execution result
        # 4. Handle success/failure

        # Stub: simulate async execution
        await asyncio.sleep(0.01)

        # If hook_url looks like an HTTP URL, try to call it
        if httpx and hook_url.startswith(("http://", "https://")):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    payload = {
                        "alert_id": alert.alert_id,
                        "tenant_id": alert.tenant_id,
                        "component_id": alert.component_id,
                        "severity": alert.severity,
                        "category": alert.category,
                        "summary": alert.summary,
                    }
                    response = await client.post(hook_url, json=payload)
                    response.raise_for_status()
                    return {
                        "hook_url": hook_url,
                        "status": "success",
                        "response": response.json() if response.content else {},
                        "timestamp": asyncio.get_event_loop().time(),
                    }
            except Exception as e:
                return {
                    "hook_url": hook_url,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": asyncio.get_event_loop().time(),
                }

        # Default: return success for stub hooks
        return {
            "hook_url": hook_url,
            "status": "success",
            "message": "stub_execution",
            "timestamp": asyncio.get_event_loop().time(),
        }

    async def handle_automation_result(
        self,
        alert_id: str,
        hook_url: str,
        success: bool,
        result_data: Optional[Dict[str, Any]] = None,
    ) -> Alert:
        """
        Handle automation execution result.
        
        If automation fails, may create a new alert about the failure.
        
        Args:
            alert_id: Original alert ID
            hook_url: Hook that was executed
            success: Whether automation succeeded
            result_data: Optional result data
        
        Returns:
            Updated alert (or new alert if automation failed)
        """
        alert = await self.alert_repo.fetch(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        if not success:
            # Automation failed - could create a new alert about the failure
            # For now, just log it via ERIS
            await self.evidence.record_event(
                event_type="automation_failed",
                tenant_id=alert.tenant_id,
                actor=None,
                alert_id=alert_id,
                metadata={"hook_url": hook_url, "result_data": result_data},
            )

        return alert

