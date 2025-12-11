"""Governance enforcement stubs."""
from __future__ import annotations

from typing import Dict, Any


class GovernanceEnforcer:
    """Simple pass-through governance enforcer."""

    def __init__(self, data_governance) -> None:
        self.data_governance = data_governance

    def enforce(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        # Delegate to mock governance to allow modification/redaction
        result = self.data_governance.evaluate(signal)
        redactions = result.get("redactions", {})
        if redactions:
            payload = signal.get("payload") or {}
            for field in redactions:
                if field in payload:
                    payload[field] = None
            signal["payload"] = payload
        return result
