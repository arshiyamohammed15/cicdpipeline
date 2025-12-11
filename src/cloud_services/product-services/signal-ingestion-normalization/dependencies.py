"""Mock external dependencies for the SIN stub service."""
from __future__ import annotations

from typing import Any, Dict, Optional, Set, Tuple
import secrets
from datetime import datetime, timedelta


class MockM21IAM:
    """Simple in-memory IAM token registry."""

    def __init__(self) -> None:
        self._tokens: Dict[str, Dict[str, Any]] = {}

    def register_token(self, token: str, claims: Dict[str, Any], expires_in_seconds: int = 3600) -> None:
        self._tokens[token] = claims | {"expires_at": datetime.utcnow() + timedelta(seconds=expires_in_seconds)}

    def issue_token(self, claims: Dict[str, Any], expires_in_seconds: int = 3600) -> str:
        token = secrets.token_hex(16)
        self.register_token(token, claims, expires_in_seconds)
        return token

    def verify(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        if not token:
            return None
        raw = token.replace("Bearer ", "")
        claims = self._tokens.get(raw)
        if not claims:
            return None
        expires_at = claims.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at < datetime.utcnow():
            return None
        return claims


class MockM32Trust:
    """Stub trust publisher."""

    def __init__(self) -> None:
        self.events: list[Dict[str, Any]] = []

    async def publish(self, event: Dict[str, Any]) -> None:
        self.events.append(event)


class MockM35Budgeting:
    """Stub budgeting adapter."""

    def __init__(self) -> None:
        self.requests: list[Dict[str, Any]] = []

    def check_budget(self, tenant_id: str, resource_type: str, estimated_cost: float) -> bool:
        self.requests.append({"tenant_id": tenant_id, "resource_type": resource_type, "estimated_cost": estimated_cost})
        return True


class MockM29DataGovernance:
    """Stub data governance evaluator."""

    def __init__(self) -> None:
        self.evaluations: list[Dict[str, Any]] = []
        self._disallowed: Dict[Tuple[str, str, str], Set[str]] = {}
        self._redaction_rules: Dict[Tuple[str, str, str], Dict[str, str]] = {}

    def set_disallowed_fields(self, tenant_id: str, producer_id: str, signal_type: str, fields: list[str]) -> None:
        self._disallowed[(tenant_id, producer_id, signal_type)] = set(fields)

    def set_redaction_rules(self, tenant_id: str, producer_id: str, signal_type: str, rules: Dict[str, str]) -> None:
        self._redaction_rules[(tenant_id, producer_id, signal_type)] = rules

    def evaluate(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        payload = signal.get("payload", {}) or {}
        key = (signal.get("tenant_id"), signal.get("producer_id"), signal.get("signal_type"))
        violations = [f for f in self._disallowed.get(key, set()) if f in payload]
        redactions: Dict[str, str] = {}
        for field, action in self._redaction_rules.get(key, {}).items():
            if field in payload:
                redactions[field] = action or "redact"
        allowed = len(violations) == 0
        result = {"allowed": allowed, "redactions": redactions, "violations": violations}
        self.evaluations.append(result)
        return result


class MockM34SchemaRegistry:
    """In-memory schema registry."""

    def __init__(self) -> None:
        self.contracts: Dict[tuple[str, str], Dict[str, Any]] = {}

    def register_contract(self, signal_type: str, contract_version: str, contract: Dict[str, Any]) -> None:
        self.contracts[(signal_type, contract_version)] = contract

    def get_contract(self, signal_type: str, contract_version: str) -> Optional[Dict[str, Any]]:
        return self.contracts.get((signal_type, contract_version))


class MockAPIGateway:
    """Stub API gateway for downstream notifications."""

    def __init__(self) -> None:
        self.calls: list[Dict[str, Any]] = []

    def notify(self, payload: Dict[str, Any]) -> None:
        self.calls.append(payload)
