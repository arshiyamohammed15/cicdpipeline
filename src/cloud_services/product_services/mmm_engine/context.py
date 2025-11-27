"""
Context builder for MMM Engine decisions.
"""

from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from .models import MMMContext, ActorType
from .service_registry import get_data_governance, get_ubi_signal_service


class ContextService:
    def __init__(self):
        self.data_governance = get_data_governance()
        self.signal_service = get_ubi_signal_service()

    def build_context(self, tenant_id: str, actor_id: str | None, actor_type: ActorType, extra: Dict[str, Any]) -> MMMContext:
        governance = self.data_governance.get_tenant_config(tenant_id)
        recent_signals = self.signal_service.get_recent_signals(tenant_id, actor_id or "unknown")
        return MMMContext(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_roles=extra.get("roles", []),
            repo_id=extra.get("repo_id"),
            branch=extra.get("branch"),
            file_path=extra.get("file_path"),
            policy_snapshot_id=None,
            quiet_hours=governance.get("quiet_hours"),
            recent_signals=recent_signals,
        )


