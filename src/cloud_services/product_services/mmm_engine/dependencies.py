"""
Dependency clients for MMM Engine (PM-1).

Mock implementations for IAM, ERIS, Policy, LLM Gateway, and Data Governance
to enable development before real integrations are wired up.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class MockIAMClient:
    """Mock IAM (EPC-1) client for token verification and role lookup."""

    def __init__(self) -> None:
        self.tokens: Dict[str, Dict[str, Any]] = {}

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        claims = self.tokens.get(token)
        if claims:
            return True, claims, None
        if token.startswith("tenant-"):
            tenant_id = token.replace("tenant-", "").split("-")[0] or "default-tenant"
            claims = {"tenant_id": tenant_id, "sub": f"user@{tenant_id}", "roles": ["developer"]}
            return True, claims, None
        return False, None, "Invalid or expired token"

    def register_token(self, token: str, claims: Dict[str, Any]) -> None:
        self.tokens[token] = claims


class MockERISClient:
    """Mock ERIS (EPC-7) client for DecisionReceipts."""

    def __init__(self) -> None:
        self.receipts: Dict[str, Dict[str, Any]] = {}
        self.available = True

    async def emit_receipt(self, receipt: Dict[str, Any]) -> str:
        if not self.available:
            raise RuntimeError("ERIS unavailable")
        receipt_id = receipt.get("receipt_id") or f"receipt-{len(self.receipts)+1}"
        self.receipts[receipt_id] = receipt
        logger.debug("Mock ERIS stored receipt %s", receipt_id)
        return receipt_id


class MockPolicyService:
    """Mock Policy & Config (EPC-3/EPC-10) service."""

    def evaluate(self, tenant_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"tenant_id": tenant_id, "policy_snapshot_id": "policy-v1", "allowed": True}


class MockLLMGateway:
    """Mock LLM Gateway (PM-6) for Mentor/Multiplier content generation."""

    async def generate(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "content": f"Mentor suggestion based on: {prompt[:60]}...",
            "safety": {"status": "pass", "timestamp": datetime.utcnow().isoformat()},
        }


class MockDataGovernance:
    """Mock Data Governance client for retention/privacy hooks."""

    def get_tenant_config(self, tenant_id: str) -> Dict[str, Any]:
        return {"retention_days": 365, "privacy_tags": [], "quiet_hours": {"start": 22, "end": 6}}


class MockUBISignalService:
    """Mock service returning recent UBI BehaviouralSignals."""

    def get_recent_signals(self, tenant_id: str, actor_id: str) -> list[Dict[str, Any]]:
        return [
            {
                "signal_id": "sig-1",
                "tenant_id": tenant_id,
                "actor_id": actor_id,
                "dimension": "flow",
                "severity": "WARN",
                "created_at": datetime.utcnow().isoformat(),
            }
        ]


